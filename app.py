import io
import json
import os
import re
import time
import zipfile
from datetime import datetime, timedelta

# Tăng tốc độ đọc đa luồng song song của PyIceberg lên 32 workers
os.environ["PYICEBERG_MAX_WORKERS"] = "32"

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH HỆ THỐNG & BIẾN MÔI TRƯỜNG (.env)
# -----------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def get_config(key: str, default: str = "") -> str:
    """Đọc cấu hình từ biến môi trường (.env) hoặc từ st.secrets (khi deploy Streamlit Cloud)."""
    val = os.getenv(key)
    if val:
        return val
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

ACCOUNT_ID = get_config("R2_ACCOUNT_ID", "")
BUCKET = get_config("R2_BUCKET", "")
ACCESS_KEY_ID = get_config("R2_ACCESS_KEY_ID", "")
SECRET_ACCESS_KEY = get_config("R2_SECRET_ACCESS_KEY", "")
DEFAULT_USE_SAMPLE = get_config("USE_SAMPLE", "0") == "1"
R2_ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

# Thư mục bộ nhớ đệm cục bộ (Chỉ duy trì đúng 2 file, không phát sinh file rác)
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
CACHE_PARQUET_FILE = os.path.join(CACHE_DIR, "events_cache.parquet")
CACHE_META_FILE = os.path.join(CACHE_DIR, "events_cache_meta.json")

st.set_page_config(
    page_title="Basin Catalog — Phân Tích Truy Cập Web",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Bảng màu cao cấp đồng nhất (Sky Blue, Indigo, Emerald, Amber, Rose, Purple)
CHART_THEME = "plotly_dark"
COLOR_PALETTE = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa"]

# -----------------------------------------------------------------------------
# CSS TINH CHỈNH: GIAO DIỆN HIỆN ĐẠI, THOÁNG ĐÃNG, KHÔNG RỐI MẮT
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Gọn gàng padding trang */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1440px;
    }
    
    /* Thanh trạng thái dạng badge thanh lịch */
    .status-bar-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        padding: 8px 14px;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        margin-bottom: 1.2rem;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: #1e293b;
        border-radius: 6px;
        font-size: 0.8rem;
        color: #cbd5e1;
    }
    .status-chip b {
        color: #38bdf8;
    }

    /* Thẻ Container có viền mỏng tinh tế */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #0f172a;
        border: 1px solid #1e293b !important;
        border-radius: 10px;
    }

    /* Metric Cards đồng bộ */
    div[data-testid="stMetric"] {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px 16px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
    }

    /* Tabs tinh gọn */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0d131f;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #1e293b;
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 6px;
        padding: 6px 16px;
        font-weight: 600;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
    }

    /* Sidebar sạch sẽ */
    [data-testid="stSidebar"] {
        background-color: #090d16;
        border-right: 1px solid #1e293b;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. SINH DỮ LIỆU MẪU (KHI USE_SAMPLE=1)
# -----------------------------------------------------------------------------
def sample_events() -> pd.DataFrame:
    """Tạo dữ liệu mẫu đa dạng gồm nhiều nhóm ID và phân bố thời gian từ 2024 đến nay."""
    now_ms = int(time.time() * 1000)
    rows = []
    
    sample_ids = [
        "raumaxao", "nhóm 07 CNTT K22E", "nhom 06 cnttk22e", "coffeet1", "cuong nhom2",
        "Nhóm 04-K22E", "nhóm 13", "nhom 9", "nhóm 8", "Nhóm 11 CNTT K22KL"
    ]

    for i in range(600):
        grp_id = sample_ids[i % len(sample_ids)]
        time_offset = (i * 120_000) if i < 400 else (i * 3_600_000)
        rows.append({
            "id": grp_id,
            "country": "VN" if i % 5 != 0 else ("US" if i % 7 == 0 else "JP"),
            "device": "mobile" if i % 3 == 0 else ("Windows PC" if i % 3 == 1 else "iOS"),
            "time": now_ms - time_offset,
            "ip": f"14.162.{(i % 10)}.{i % 250}",
        })

    rows.append({"id": "test_auto_script", "country": "VN", "device": "bot", "time": now_ms - 50_000, "ip": "127.0.0.1"})
    rows.append({"id": "synthetic-batch-01", "country": "US", "device": "curl", "time": now_ms - 80_000, "ip": "10.0.0.9"})
    rows.append({"id": "nhom_07", "country": "VN", "device": "mobile", "time": 0, "ip": "14.162.1.1"})

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# 3. QUẢN LÝ BỘ NHỚ ĐỆM CỤC BỘ (LOCAL DISK CACHE - KHÔNG TẠO FILE RÁC)
# -----------------------------------------------------------------------------
def clean_stray_cache_files():
    """Đảm bảo thư mục cache chỉ chứa đúng 2 file duy nhất, dọn dẹp mọi file thừa nếu có."""
    if os.path.exists(CACHE_DIR):
        allowed = {"events_cache.parquet", "events_cache_meta.json"}
        for f in os.listdir(CACHE_DIR):
            if f not in allowed:
                try:
                    os.remove(os.path.join(CACHE_DIR, f))
                except Exception:
                    pass


def load_local_cache() -> tuple[pd.DataFrame | None, dict | None]:
    """Đọc dữ liệu từ bộ nhớ đệm ổ cứng cục bộ (tốc độ ~0.02s)."""
    if os.path.exists(CACHE_PARQUET_FILE) and os.path.exists(CACHE_META_FILE):
        try:
            with open(CACHE_META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
            df = pd.read_parquet(CACHE_PARQUET_FILE)
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"])
            return df, meta
        except Exception:
            return None, None
    return None, None


def save_local_cache(df: pd.DataFrame, meta: dict):
    """Ghi đè dữ liệu vào bộ nhớ đệm cục bộ (luôn luôn chỉ giữ 2 file duy nhất)."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        clean_stray_cache_files()
        df.to_parquet(CACHE_PARQUET_FILE, index=False)
        with open(CACHE_META_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# -----------------------------------------------------------------------------
# 4. KẾT NỐI & ĐỌC BẢNG APACHE ICEBERG TỪ CLOUDFLARE R2
# -----------------------------------------------------------------------------
def get_s3_client():
    """Tạo client S3 kết nối tới Cloudflare R2."""
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        region_name="auto",
    )


def latest_metadata_key(s3, known_prefix: str | None = None) -> tuple[str, str]:
    """Tìm file metadata json mới nhất của Apache Iceberg với thuật toán tối ưu tiền tố."""
    # 1. Thử tiền tố đã biết để phản hồi trong 1 request (< 1s)
    if known_prefix:
        try:
            res = s3.list_objects_v2(Bucket=BUCKET, Prefix=known_prefix)
            keys = [o["Key"] for o in res.get("Contents", []) if o["Key"].endswith(".metadata.json")]
            if keys:
                return sorted(keys)[-1], known_prefix
        except Exception:
            pass

    # 2. Dò tìm dưới thư mục catalog tiêu chuẩn
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix="__r2_data_catalog/"):
        keys += [o["Key"] for o in page.get("Contents", []) if o["Key"].endswith(".metadata.json")]
    
    # 3. Quét toàn bộ nếu chưa thấy
    if not keys:
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET):
            keys += [o["Key"] for o in page.get("Contents", []) if o["Key"].endswith(".metadata.json")]
            
    if not keys:
        raise FileNotFoundError(f"Không tìm thấy file .metadata.json nào trong bucket '{BUCKET}'.")

    latest = sorted(keys)[-1]
    discovered_prefix = latest.rsplit("/", 1)[0] + "/"
    return latest, discovered_prefix


def iceberg_events(s3, meta_key: str) -> pd.DataFrame:
    """Truy vấn bảng Apache Iceberg trực tiếp qua pyiceberg và boto3 (tận dụng 32 workers)."""
    from pyiceberg.table import StaticTable

    table = StaticTable.from_metadata(
        f"s3://{BUCKET}/{meta_key}",
        properties={
            "s3.endpoint": R2_ENDPOINT,
            "s3.access-key-id": ACCESS_KEY_ID,
            "s3.secret-access-key": SECRET_ACCESS_KEY,
            "s3.region": "auto",
        },
    )
    df = table.scan(selected_fields=("id", "country", "device", "time", "ip")).to_pandas()
    return df


# -----------------------------------------------------------------------------
# 5. HÀM LÀM SẠCH DỮ LIỆU (THEO QUY CHUẨN MỤC 9.6 TÀI LIỆU HƯỚNG DẪN)
# -----------------------------------------------------------------------------
def clean_events(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats = {"raw": len(df), "invalid_time": 0, "test_data": 0, "clean": 0}
    if df.empty:
        return df, stats

    # 1. Chuẩn hóa thời gian sang datetime
    if pd.api.types.is_numeric_dtype(df["time"]):
        df["datetime"] = pd.to_datetime(df["time"], unit="ms", errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df["time"], errors="coerce")

    # Loại bỏ dòng không có datetime hoặc trước năm 2000 (lỗi epoch 1970)
    valid_time_mask = df["datetime"].notna() & (df["datetime"].dt.year >= 2000)
    stats["invalid_time"] = int((~valid_time_mask).sum())
    df = df[valid_time_mask].copy()

    # 2. Loại bỏ dữ liệu thử nghiệm
    test_prefixes = ("test", "synthetic", "sim-", "probe", "ping-", "web-access-")
    id_series = df["id"].astype(str).str.lower().str.strip()
    is_test_mask = id_series.str.startswith(test_prefixes)
    stats["test_data"] = int(is_test_mask.sum())
    df = df[~is_test_mask].copy()

    # 3. Chuẩn hóa Quốc gia
    def normalize_country(val):
        if pd.isna(val):
            return "KHÁC"
        c = str(val).strip().upper()
        if c in ["VIỆT NAM", "VIET NAM", "VIETNAM", "VN"]:
            return "VN"
        if c in ["UNKNOWN", "ALL", "NONE", "NULL", ""]:
            return "KHÁC"
        return c

    df["country_clean"] = df["country"].apply(normalize_country)

    # 4. Chuẩn hóa Thiết bị (desktop, mobile, tablet, khác)
    def normalize_device(val):
        if pd.isna(val):
            return "khác"
        d = str(val).strip().lower()
        if any(kw in d for kw in ["tablet", "ipad"]):
            return "tablet"
        if any(kw in d for kw in ["mobile", "ios", "iphone", "android", "phone"]):
            return "mobile"
        if any(kw in d for kw in ["desktop", "pc", "windows", "macos", "mac", "linux", "máy tính"]):
            return "desktop"
        return "khác"

    df["device_clean"] = df["device"].apply(normalize_device)
    df["id_clean"] = df["id"].fillna("Không xác định").astype(str).str.strip()
    
    stats["clean"] = len(df)
    return df, stats


def load_and_process_events(use_sample: bool, force_refresh: bool = False):
    """Nạp dữ liệu thông minh: kiểm tra Local Disk Cache trước, chỉ tải từ R2 khi có snapshot mới."""
    if use_sample:
        raw_df = sample_events()
        cleaned_df, clean_stats = clean_events(raw_df)
        return cleaned_df, clean_stats, "sample_snapshot", "sample", "Dữ liệu mẫu"

    s3 = get_s3_client()
    cached_df, cached_meta = load_local_cache()
    known_p = cached_meta.get("prefix") if cached_meta else None

    # Nếu không bắt buộc nạp lại và có file cache cục bộ
    if not force_refresh and cached_df is not None and cached_meta:
        try:
            curr_meta, prefix = latest_metadata_key(s3, known_prefix=known_p)
            # Nếu metadata trên R2 trùng khớp với cache cục bộ: nạp ngay từ SSD (0.02s)
            if curr_meta == cached_meta.get("meta_key"):
                return cached_df, cached_meta.get("clean_stats", {}), curr_meta, prefix, "Cache SSD (0.02s)"
        except Exception:
            # Nếu mất mạng hoặc lỗi kết nối, vẫn dùng được dữ liệu cache đã lưu
            return cached_df, cached_meta.get("clean_stats", {}), cached_meta.get("meta_key", ""), known_p, "Cache Offline"

    # Trường hợp chưa có cache hoặc R2 có dữ liệu mới hoặc ấn nút Nạp Lại
    meta_key, prefix = latest_metadata_key(s3, known_prefix=known_p)
    raw_df = iceberg_events(s3, meta_key)
    cleaned_df, clean_stats = clean_events(raw_df)
    
    # Lưu bản sao sạch vào ổ SSD máy tính (duy trì duy nhất 2 file)
    save_local_cache(cleaned_df, {
        "meta_key": meta_key,
        "prefix": prefix,
        "clean_stats": clean_stats,
        "updated_at": datetime.now().isoformat()
    })
    return cleaned_df, clean_stats, meta_key, prefix, "Tải Mới Từ R2"


# -----------------------------------------------------------------------------
# 6. SIDEBAR: ĐIỀU KHIỂN & BỘ LỌC TINH GỌN (KHÔNG RỐI MẮT)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 Basin Catalog")
    st.caption("Lakehouse Analytics • Cloudflare R2")
    st.markdown("---")

    # MỤC 1: KHOẢNG THỜI GIAN
    # THỨ TỰ CHUẨN XÁC: 24h -> 7 ngày -> 30 ngày -> Toàn bộ thời gian -> Tùy chỉnh
    time_preset = st.selectbox(
        "⏱️ Khoảng thời gian:",
        options=[
            "24 giờ qua (Mặc định)",
            "7 ngày qua",
            "30 ngày qua",
            "Toàn bộ thời gian (Tất cả dữ liệu)",
            "Tùy chỉnh khoảng ngày..."
        ],
        index=0
    )

    custom_start_date = None
    custom_end_date = None
    if time_preset == "Tùy chỉnh khoảng ngày...":
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            custom_start_date = st.date_input("Từ ngày:", value=datetime.now() - timedelta(days=7))
        with col_d2:
            custom_end_date = st.date_input("Đến ngày:", value=datetime.now())

    # MỤC 2: LỌC THEO TỪ KHÓA ID
    search_id_kw = st.text_input("🔍 Tìm nhanh ID / Nhóm:", placeholder="Gõ tên ID (vd: raumaxao)...")

    st.markdown("---")
    
    # MỤC 3: CÀI ĐẶT NGUỒN & ĐỒNG BỘ (GOM GỌN TRONG EXPANDER ĐỂ ĐỠ LOẠN)
    with st.expander("⚙️ Nguồn Dữ Liệu & Live Sync", expanded=False):
        sample_toggle = st.toggle("Dữ liệu mẫu (Demo)", value=DEFAULT_USE_SAMPLE)
        live_sync = st.toggle("Đồng bộ thời gian thực (Live Sync)", value=False)
        sync_interval = 30
        if live_sync:
            sync_interval = st.selectbox(
                "Tần suất kiểm tra:",
                options=[15, 30, 60, 120],
                index=1,
                format_func=lambda s: f"Mỗi {s} giây"
            )

    if st.button("🔄 Nạp Lại Dữ Liệu R2", use_container_width=True):
        st.session_state.pop("cached_df_all", None)
        st.session_state.pop("cached_stats", None)
        st.session_state["force_refresh_r2"] = True
        st.cache_data.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# 7. QUẢN LÝ DỮ LIỆU TỔNG (LƯU TRONG RAM / SESSION_STATE)
# -----------------------------------------------------------------------------
force_r2 = st.session_state.pop("force_refresh_r2", False)
needs_load = (
    force_r2
    or "cached_df_all" not in st.session_state
    or "cached_stats" not in st.session_state
    or st.session_state.get("cached_sample_mode") != sample_toggle
)

# Tự động phát hiện snapshot mới trên R2 nếu bật Live Sync
if not needs_load and not sample_toggle and live_sync and "cached_meta_key" in st.session_state:
    try:
        s3_check = get_s3_client()
        curr_meta, _ = latest_metadata_key(s3_check, known_prefix=st.session_state.get("cached_prefix"))
        if curr_meta != st.session_state.get("cached_meta_key"):
            needs_load = True
            force_r2 = True
            st.session_state["has_new_snapshot_toast"] = True
    except Exception:
        pass

if needs_load:
    try:
        with st.spinner("⚡ Đang nạp dữ liệu tốc độ cao (Local Disk Cache & 32 luồng R2)..."):
            df_all, stats, meta_key, prefix, load_source = load_and_process_events(sample_toggle, force_refresh=force_r2)
            st.session_state["cached_df_all"] = df_all
            st.session_state["cached_stats"] = stats
            st.session_state["cached_meta_key"] = meta_key
            st.session_state["cached_prefix"] = prefix
            st.session_state["cached_load_source"] = load_source
            st.session_state["cached_sample_mode"] = sample_toggle
            st.session_state["cached_time"] = datetime.now()
            if st.session_state.pop("has_new_snapshot_toast", False):
                st.toast("🔔 Đã có dữ liệu mới trên Cloudflare R2! Bảng dữ liệu đã tự động cập nhật.", icon="🚀")
    except Exception as e:
        st.error(f"❌ Không thể tải dữ liệu: {e}")
        st.info("💡 Bạn có thể bật 'Dữ liệu mẫu' ở sidebar bên trái để kiểm tra giao diện.")
        st.stop()
else:
    df_all = st.session_state["cached_df_all"]
    stats = st.session_state["cached_stats"]
    load_source = st.session_state.get("cached_load_source", "Cache")

if df_all.empty:
    st.warning("⚠️ Bảng dữ liệu hiện tại đang trống.")
    st.stop()

# Lọc dữ liệu tức thì trong RAM từ df_all
now_ts = pd.Timestamp.now()
if time_preset == "24 giờ qua (Mặc định)":
    df_filtered = df_all[df_all["datetime"] >= (now_ts - pd.Timedelta(hours=24))].copy()
elif time_preset == "7 ngày qua":
    df_filtered = df_all[df_all["datetime"] >= (now_ts - pd.Timedelta(days=7))].copy()
elif time_preset == "30 ngày qua":
    df_filtered = df_all[df_all["datetime"] >= (now_ts - pd.Timedelta(days=30))].copy()
elif time_preset == "Toàn bộ thời gian (Tất cả dữ liệu)":
    df_filtered = df_all.copy()
else:
    start_ts = pd.to_datetime(custom_start_date)
    end_ts = pd.to_datetime(custom_end_date) + pd.Timedelta(days=1)
    df_filtered = df_all[(df_all["datetime"] >= start_ts) & (df_all["datetime"] < end_ts)].copy()

# Lọc tiếp theo từ khóa ID nếu có
if search_id_kw:
    df_filtered = df_filtered[df_filtered["id_clean"].str.contains(search_id_kw, case=False, na=False)]


# -----------------------------------------------------------------------------
# 8. TIÊU ĐỀ TRANG & THANH TRẠNG THÁI GỌN GÀNG (STATUS CHIP BAR)
# -----------------------------------------------------------------------------
col_header_l, col_header_r = st.columns([3, 1])
with col_header_l:
    st.title("Phân Tích Dữ Liệu Truy Cập Web")
    st.caption("Nền tảng Apache Iceberg Direct Query trên Cloudflare R2 Bucket")

with col_header_r:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if live_sync:
        st.success(f"🔴 Live Sync: {sync_interval}s")
    else:
        st.info("🟢 Chế độ: Đã kết nối")

min_dt_str = df_filtered["datetime"].min().strftime('%d/%m/%Y %H:%M') if not df_filtered.empty else "N/A"
max_dt_str = df_filtered["datetime"].max().strftime('%d/%m/%Y %H:%M') if not df_filtered.empty else "N/A"
source_label = "Dữ liệu mẫu" if sample_toggle else f"R2 ({BUCKET})"

st.markdown(f"""
<div class="status-bar-container">
    <div class="status-chip">⏱️ Khoảng xem: <b>{time_preset}</b> ({min_dt_str} → {max_dt_str})</div>
    <div class="status-chip">🌐 Nguồn: <b>{source_label}</b></div>
    <div class="status-chip">🚀 Tốc độ: <b>{load_source}</b></div>
    <div class="status-chip">📁 Tổng kho: <b>{stats['clean']:,}</b> bản ghi</div>
    <div class="status-chip">⚡ Đang lọc: <b>{len(df_filtered):,}</b> bản ghi</div>
</div>
""", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ Không có bản ghi nào phù hợp với bộ lọc đã chọn. Hãy điều chỉnh khoảng thời gian hoặc từ khóa tìm kiếm ở sidebar bên trái.")
    st.stop()


# -----------------------------------------------------------------------------
# 9. HÀNG 4 THẺ CHỈ SỐ KPI CHÍNH (CÂN ĐỐI, RÕ RÀNG, DỄ NHÌN)
# -----------------------------------------------------------------------------
total_views = len(df_filtered)
unique_ips = df_filtered["ip"].dropna().nunique()
unique_countries = df_filtered["country_clean"].nunique()
unique_ids = df_filtered["id_clean"].nunique()

top_device = df_filtered["device_clean"].mode()[0] if not df_filtered.empty else "N/A"
top_device_pct = (df_filtered["device_clean"].value_counts(normalize=True).iloc[0] * 100) if not df_filtered.empty else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    with st.container(border=True):
        st.metric("TỔNG LƯỢT TRUY CẬP", f"{total_views:,}", f"{unique_ids:,} nhóm/ID")
with k2:
    with st.container(border=True):
        st.metric("KHÁCH DUY NHẤT (IP)", f"{unique_ips:,}", f"{(unique_ips / total_views * 100):.1f}% tỷ lệ IP mới")
with k3:
    with st.container(border=True):
        st.metric("QUỐC GIA PHỦ SÓNG", f"{unique_countries}", f"Top 1: {df_filtered['country_clean'].mode()[0]}")
with k4:
    with st.container(border=True):
        st.metric("THIẾT BỊ PHỔ BIẾN", f"{top_device.upper()}", f"{top_device_pct:.1f}% lưu lượng")


# -----------------------------------------------------------------------------
# 10. PHÂN CHIA NỘI DUNG THEO 4 TAB TRỰC QUAN
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tổng Quan Hệ Thống",
    "🎯 Khảo Sát Theo ID",
    "📋 Dữ Liệu & Xuất File",
    "💡 Đề Xuất Quyết Định"
])


# =============================================================================
# TAB 1: TỔNG QUAN HỆ THỐNG
# =============================================================================
with tab1:
    # 1. Biểu đồ đường Timeline
    with st.container(border=True):
        st.markdown("##### 📈 Diễn Biến Lưu Lượng Truy Cập Theo Thời Gian")
        time_span_hours = (df_filtered["datetime"].max() - df_filtered["datetime"].min()).total_seconds() / 3600
        slot_rule = "h" if time_span_hours <= 48 else "D"
        
        df_filtered["time_slot"] = df_filtered["datetime"].dt.floor(slot_rule)
        timeline_df = df_filtered.groupby(["time_slot", "device_clean"]).size().reset_index(name="Lượt truy cập")
        
        fig_timeline = px.line(
            timeline_df,
            x="time_slot",
            y="Lượt truy cập",
            color="device_clean",
            markers=True,
            labels={"time_slot": "Mốc thời gian", "device_clean": "Thiết bị", "Lượt truy cập": "Lượt truy cập"},
            template=CHART_THEME,
            color_discrete_sequence=COLOR_PALETTE
        )
        fig_timeline.update_layout(
            hovermode="x unified",
            margin=dict(l=15, r=15, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # 2. Hai cột: Quốc gia & Thiết bị
    c_left, c_right = st.columns(2)

    with c_left:
        with st.container(border=True):
            st.markdown("##### 🌍 Phân Bố Theo Quốc Gia (Top 8)")
            country_df = df_filtered["country_clean"].value_counts().reset_index()
            country_df.columns = ["Quốc gia", "Lượt xem"]
            
            fig_country = px.bar(
                country_df.head(8),
                x="Quốc gia",
                y="Lượt xem",
                text="Lượt xem",
                color_discrete_sequence=["#38bdf8"],
                template=CHART_THEME
            )
            fig_country.update_traces(textposition="outside")
            fig_country.update_layout(
                margin=dict(l=10, r=10, t=25, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
            )
            st.plotly_chart(fig_country, use_container_width=True)

    with c_right:
        with st.container(border=True):
            st.markdown("##### 📱 Cơ Cấu Loại Thiết Bị")
            device_df = df_filtered["device_clean"].value_counts().reset_index()
            device_df.columns = ["Thiết bị", "Lượt xem"]
            
            fig_device = px.pie(
                device_df,
                names="Thiết bị",
                values="Lượt xem",
                hole=0.48,
                color_discrete_sequence=COLOR_PALETTE,
                template=CHART_THEME
            )
            fig_device.update_traces(textinfo="percent+label")
            fig_device.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_device, use_container_width=True)

    # 3. Ma trận đối sánh trong Expander gọn gàng
    with st.expander("🔍 Xem Bảng Ma Trận Đối Sánh: Quốc Gia x Loại Thiết Bị"):
        matrix_df = pd.crosstab(df_filtered["country_clean"], df_filtered["device_clean"], margins=True, margins_name="Tổng")
        st.dataframe(matrix_df, use_container_width=True)


# =============================================================================
# TAB 2: KHẢO SÁT & BIỂU ĐỒ CHUYÊN BIỆT THEO ID (MẶC ĐỊNH LÀ "raumaxao")
# =============================================================================
with tab2:
    st.markdown("##### 🎯 Khảo Sát Chi Tiết Từng ID / Mã Nhóm")
    st.caption("Xem hệ thống chỉ số và biểu đồ phân tích chuyên biệt riêng cho từng ID được chọn.")

    # Tạo danh sách các ID từ kho dữ liệu tổng để không bao giờ bị mất ID
    id_counts_map = df_all["id_clean"].value_counts()
    id_display_options = [f"{uid} ({cnt:,} lượt)" for uid, cnt in id_counts_map.items()]

    # Mặc định tìm và chọn "raumaxao"
    default_id_idx = 0
    for idx, opt in enumerate(id_display_options):
        if opt.lower().startswith("raumaxao"):
            default_id_idx = idx
            break

    col_id_sel, col_id_dl = st.columns([3, 1])
    with col_id_sel:
        chosen_display = st.selectbox(
            "📌 Chọn ID muốn xem chi tiết:",
            options=id_display_options,
            index=default_id_idx if id_display_options else 0
        )

    target_id = chosen_display.rsplit(" (", 1)[0] if chosen_display else None

    if target_id:
        # Lấy dữ liệu của ID được chọn
        id_df = df_filtered[df_filtered["id_clean"] == target_id].copy()
        is_showing_all_history = False
        
        # Nếu trong bộ lọc hiện tại (ví dụ 24h) không có bản ghi, tự động lấy toàn bộ lịch sử của ID này
        if id_df.empty:
            id_df = df_all[df_all["id_clean"] == target_id].copy()
            is_showing_all_history = True

        id_total_views = len(id_df)
        id_share_pct = (id_total_views / total_views * 100) if total_views > 0 else 0
        id_ips_count = id_df["ip"].dropna().nunique()
        id_top_dev = id_df["device_clean"].mode()[0] if not id_df.empty else "N/A"
        id_top_country = id_df["country_clean"].mode()[0] if not id_df.empty else "N/A"
        last_seen = id_df["datetime"].max().strftime("%d/%m/%Y %H:%M") if not id_df.empty else "N/A"

        with col_id_dl:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            id_csv = id_df[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].to_csv(index=False).encode("utf-8-sig")
            clean_filename_id = re.sub(r'[^\w\-_.]', '_', target_id)
            st.download_button(
                label=f"📥 Tải CSV ID '{target_id}'",
                data=id_csv,
                file_name=f"id_{clean_filename_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        if is_showing_all_history:
            st.info(f"ℹ️ ID **`{target_id}`** không có lượt truy cập mới trong 24 giờ qua. Hệ thống đang tự động hiển thị **toàn bộ {id_total_views:,} lượt truy cập trong lịch sử** của ID này.")

        # 4 Thẻ KPI riêng của ID
        pi1, pi2, pi3, pi4 = st.columns(4)
        with pi1:
            with st.container(border=True):
                st.metric(f"LƯỢT XEM CỦA '{target_id}'", f"{id_total_views:,}", f"{id_share_pct:.1f}% toàn kho")
        with pi2:
            with st.container(border=True):
                st.metric("ĐỊA CHỈ IP ĐÃ DÙNG", f"{id_ips_count:,}", "IPs độc lập")
        with pi3:
            with st.container(border=True):
                st.metric("THIẾT BỊ HAY DÙNG", f"{id_top_dev.upper()}", f"Quốc gia: {id_top_country}")
        with pi4:
            with st.container(border=True):
                st.metric("HOẠT ĐỘNG GẦN NHẤT", f"{last_seen.split(' ')[1]}", f"Ngày: {last_seen.split(' ')[0]}")

        # Hàng 1: Diễn biến thời gian + Khung giờ hoạt động (Trục thời gian)
        r1_c1, r1_c2 = st.columns([1.6, 1.2])
        with r1_c1:
            with st.container(border=True):
                st.markdown(f"##### 📈 Lịch Sử Truy Cập Của `{target_id}`")
                time_diff = (id_df["datetime"].max() - id_df["datetime"].min()).total_seconds()
                slot_freq = "h" if time_diff <= 86400 * 3 else "D"
                id_df["slot"] = id_df["datetime"].dt.floor(slot_freq)
                id_timeline = id_df.groupby(["slot", "device_clean"]).size().reset_index(name="Lượt truy cập")

                fig_id_timeline = px.line(
                    id_timeline,
                    x="slot",
                    y="Lượt truy cập",
                    color="device_clean",
                    markers=True,
                    template=CHART_THEME,
                    color_discrete_sequence=COLOR_PALETTE
                )
                fig_id_timeline.update_layout(
                    hovermode="x unified",
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
                )
                st.plotly_chart(fig_id_timeline, use_container_width=True)

        with r1_c2:
            with st.container(border=True):
                st.markdown(f"##### ⏰ Khung Giờ Hoạt Động (0h - 23h)")
                id_df["hour_of_day"] = id_df["datetime"].dt.hour
                hourly_hist = id_df.groupby("hour_of_day").size().reindex(range(24), fill_value=0).reset_index()
                hourly_hist.columns = ["Giờ", "Số lượt"]
                hourly_hist["Nhãn"] = hourly_hist["Giờ"].apply(lambda h: f"{h:02d}:00")

                fig_hourly = px.bar(
                    hourly_hist,
                    x="Nhãn",
                    y="Số lượt",
                    color_discrete_sequence=["#818cf8"],
                    template=CHART_THEME
                )
                fig_hourly.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
                )
                st.plotly_chart(fig_hourly, use_container_width=True)

        # Hàng 2: Ba cột phân bổ - Quốc gia, Thiết bị & Địa chỉ IP
        r2_c1, r2_c2, r2_c3 = st.columns(3)

        with r2_c1:
            with st.container(border=True):
                st.markdown(f"##### 🌍 Phân Bố Quốc Gia Của `{target_id}`")
                id_country_df = id_df["country_clean"].value_counts().reset_index()
                id_country_df.columns = ["Quốc gia", "Lượt xem"]

                fig_id_country = px.bar(
                    id_country_df,
                    x="Quốc gia",
                    y="Lượt xem",
                    text="Lượt xem",
                    color_discrete_sequence=["#34d399"],
                    template=CHART_THEME
                )
                fig_id_country.update_traces(textposition="outside")
                fig_id_country.update_layout(
                    margin=dict(l=10, r=10, t=25, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
                )
                st.plotly_chart(fig_id_country, use_container_width=True)

        with r2_c2:
            with st.container(border=True):
                st.markdown(f"##### 📱 Cơ Cấu Thiết Bị Của `{target_id}`")
                id_dev_df = id_df["device_clean"].value_counts().reset_index()
                id_dev_df.columns = ["Thiết bị", "Lượt xem"]
                
                fig_id_dev = px.pie(
                    id_dev_df,
                    names="Thiết bị",
                    values="Lượt xem",
                    hole=0.48,
                    template=CHART_THEME,
                    color_discrete_sequence=COLOR_PALETTE
                )
                fig_id_dev.update_traces(textinfo="percent+label")
                fig_id_dev.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False
                )
                st.plotly_chart(fig_id_dev, use_container_width=True)

        with r2_c3:
            with st.container(border=True):
                st.markdown(f"##### 🌐 Top Địa Chỉ IP Của `{target_id}`")
                id_ip_counts = id_df["ip"].value_counts().head(8).reset_index()
                id_ip_counts.columns = ["Địa chỉ IP", "Lượt xem"]
                
                fig_id_ip = px.bar(
                    id_ip_counts.sort_values(by="Lượt xem", ascending=True),
                    x="Lượt xem",
                    y="Địa chỉ IP",
                    orientation="h",
                    text="Lượt xem",
                    color_discrete_sequence=["#38bdf8"],
                    template=CHART_THEME
                )
                fig_id_ip.update_traces(textposition="outside")
                fig_id_ip.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
                )
                st.plotly_chart(fig_id_ip, use_container_width=True)

        # Bảng chi tiết các lần truy cập
        with st.expander(f"📋 Xem danh sách chi tiết các lần truy cập của '{target_id}'"):
            st.dataframe(
                id_df[["datetime", "ip", "device_clean", "country_clean"]]
                .rename(columns={"datetime": "Thời gian", "ip": "Địa chỉ IP", "device_clean": "Thiết bị", "country_clean": "Quốc gia"})
                .sort_values(by="Thời gian", ascending=False),
                use_container_width=True,
                hide_index=True
            )


# =============================================================================
# TAB 3: DỮ LIỆU & TRUNG TÂM XUẤT FILE
# =============================================================================
with tab3:
    st.markdown("##### 📥 Trung Tâm Xuất Dữ Liệu")
    st.caption("Lựa chọn phương thức xuất dữ liệu phù hợp với nhu cầu phân tích và báo cáo.")

    exp_c1, exp_c2, exp_c3 = st.columns(3)
    
    # CỘT 1: XUẤT TOÀN BỘ CSV
    with exp_c1:
        with st.container(border=True):
            st.markdown("###### 📄 Xuất Toàn Bộ Đang Lọc")
            st.caption(f"Tải về toàn bộ **{len(df_filtered):,}** dòng dữ liệu chuẩn CSV.")
            
            csv_all_data = df_filtered[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                "id_clean": "Mã Nhóm / ID",
                "country_clean": "Quốc Gia",
                "device_clean": "Thiết Bị",
                "datetime": "Thời Gian Truy Cập",
                "ip": "Địa Chỉ IP"
            }).to_csv(index=False).encode("utf-8-sig")
            
            st.download_button(
                label=f"📥 Tải toàn bộ CSV ({len(df_filtered):,})",
                data=csv_all_data,
                file_name=f"basin_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # CỘT 2: XUẤT THEO TỪNG ID
    with exp_c2:
        with st.container(border=True):
            st.markdown("###### 🎯 Xuất Riêng Theo Từng ID")
            st.caption("Chọn 1 ID để xuất file CSV dữ liệu riêng biệt.")
            
            distinct_ids_tab3 = df_filtered["id_clean"].value_counts().index.tolist()
            default_tab3_idx = 0
            for i_idx, i_val in enumerate(distinct_ids_tab3):
                if i_val.lower() == "raumaxao":
                    default_tab3_idx = i_idx
                    break
                    
            selected_id_to_export = st.selectbox(
                "ID cần xuất:",
                options=distinct_ids_tab3,
                index=default_tab3_idx if distinct_ids_tab3 else 0,
                key="tab3_export_id_select"
            )
            
            if selected_id_to_export:
                sub_id_df = df_filtered[df_filtered["id_clean"] == selected_id_to_export][["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                    "id_clean": "Mã Nhóm / ID",
                    "country_clean": "Quốc Gia",
                    "device_clean": "Thiết Bị",
                    "datetime": "Thời Gian Truy Cập",
                    "ip": "Địa Chỉ IP"
                })
                csv_single_id = sub_id_df.to_csv(index=False).encode("utf-8-sig")
                clean_filename_id = re.sub(r'[^\w\-_.]', '_', selected_id_to_export)
                st.download_button(
                    label=f"📥 Tải CSV ID '{selected_id_to_export}'",
                    data=csv_single_id,
                    file_name=f"id_{clean_filename_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # CỘT 3: XUẤT GÓI NÉN ZIP
    with exp_c3:
        with st.container(border=True):
            st.markdown("###### 📦 Xuất Gói Nén ZIP")
            st.caption(f"Tách {df_filtered['id_clean'].nunique()} ID thành các file CSV độc lập.")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for grp_name, grp_df in df_filtered.groupby("id_clean"):
                    safe_grp_name = re.sub(r'[^\w\-_.]', '_', str(grp_name))
                    grp_csv = grp_df[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                        "id_clean": "Mã Nhóm / ID",
                        "country_clean": "Quốc Gia",
                        "device_clean": "Thiết Bị",
                        "datetime": "Thời Gian Truy Cập",
                        "ip": "Địa Chỉ IP"
                    }).to_csv(index=False).encode("utf-8-sig")
                    zip_file.writestr(f"id_{safe_grp_name}.csv", grp_csv)
            
            zip_buffer.seek(0)
            st.download_button(
                label=f"📦 Tải ZIP ({df_filtered['id_clean'].nunique()} file)",
                data=zip_buffer.getvalue(),
                file_name=f"basin_all_ids_separated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown(f"**Xem trước dữ liệu ({min(len(df_filtered), 500):,} / {len(df_filtered):,} bản ghi mới nhất):**")
    export_view = df_filtered[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
        "id_clean": "Mã Nhóm / ID",
        "country_clean": "Quốc Gia",
        "device_clean": "Thiết Bị",
        "datetime": "Thời Gian Truy Cập",
        "ip": "Địa Chỉ IP"
    }).sort_values(by="Thời Gian Truy Cập", ascending=False)
    
    st.dataframe(export_view.head(500), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 4: ĐỀ XUẤT QUYẾT ĐỊNH DỰA TRÊN DỮ LIỆU
# =============================================================================
with tab4:
    mobile_count = df_filtered[df_filtered["device_clean"] == "mobile"].shape[0]
    mobile_pct = (mobile_count / total_views * 100) if total_views > 0 else 0
    desktop_count = df_filtered[df_filtered["device_clean"] == "desktop"].shape[0]
    desktop_pct = (desktop_count / total_views * 100) if total_views > 0 else 0

    top_country_name = country_df.iloc[0]["Quốc gia"] if not country_df.empty else "N/A"
    top_country_pct = (country_df.iloc[0]["Lượt xem"] / total_views * 100) if not country_df.empty and total_views > 0 else 0
    top_group_id = df_filtered["id_clean"].value_counts().index[0] if not df_filtered.empty else "N/A"
    top_group_views = df_filtered["id_clean"].value_counts().iloc[0] if not df_filtered.empty else 0

    d1, d2, d3 = st.columns(3)

    with d1:
        with st.container(border=True):
            st.markdown("#### 🌐 1. Hạ Tầng & CDN")
            st.markdown(f"""
            - **Thực trạng:** Quốc gia **{top_country_name}** chiếm ưu thế với **{top_country_pct:.1f}%** toàn bộ lưu lượng.
            - **Đề xuất hành động:**
              - Bật Cloudflare Edge Caching định tuyến máy chủ tối ưu tại **{top_country_name}** để giảm TTFB xuống dưới 100ms.
              - Cấu hình nén Brotli và bật Cache-Control cho tài nguyên tĩnh để tiết kiệm chi phí băng thông R2.
            """)

    with d2:
        with st.container(border=True):
            st.markdown("#### 📱 2. Thiết Kế & UI/UX")
            st.markdown(f"""
            - **Thực trạng:** Mobile chiếm **{mobile_pct:.1f}%**, Desktop chiếm **{desktop_pct:.1f}%**.
            - **Đề xuất hành động:**
              - **{'Áp dụng triết lý Mobile-First' if mobile_pct >= 50 else 'Tối ưu cân bằng trải nghiệm giữa Desktop và Mobile'}**.
              - Đảm bảo kích thước phím bấm di động chuẩn (tối thiểu 48px) và kiểm thử giao diện kỹ trên Safari iOS và Chrome Android.
            """)

    with d3:
        with st.container(border=True):
            st.markdown("#### 🎯 3. Quản Trị & Khách Hàng")
            st.markdown(f"""
            - **Thực trạng:** ID có tương tác nhiều nhất là **`{top_group_id}`** ({top_group_views:,} lượt).
            - **Đề xuất hành động:**
              - Đưa các nhóm/ID có lưu lượng cao vào danh sách chăm sóc đặc biệt (Tier 1).
              - Thiết lập ngưỡng cảnh báo khi phát hiện ID có lưu lượng tăng đột biến (>300 lượt/phút) để ngăn chặn hành vi spam hoặc cào dữ liệu trái phép.
            """)


# -----------------------------------------------------------------------------
# 11. VÒNG LẶP ĐỒNG BỘ THỜI GIAN THỰC (LIVE SYNC AUTO-POLLING)
# -----------------------------------------------------------------------------
if live_sync:
    time.sleep(sync_interval)
    st.rerun()
