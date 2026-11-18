import time
from datetime import datetime
import pandas as pd
import streamlit as st

from src.config import BUCKET
from src.styles import apply_custom_styles
from src.data_loader import load_and_process_events, get_s3_client, latest_metadata_key
from src.views.sidebar import render_sidebar
from src.views.header import render_header
from src.views.kpi_metrics import render_kpi_metrics
from src.views.tab_overview import render_tab_overview
from src.views.tab_id_detail import render_tab_id_detail
from src.views.tab_analytics import render_tab_analytics
from src.views.tab_export import render_tab_export
from src.views.tab_insights import render_tab_insights

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG VÀ GIAO DIỆN CHUẨN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Basin Catalog — Phân Tích Truy Cập Web",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Áp dụng giao diện thích ứng (Adaptive Dark/Light) & Chặn bôi đen/sao chép nhầm
apply_custom_styles()

# -----------------------------------------------------------------------------
# 2. KHỞI TẠO BỘ ĐIỀU KHIỂN SIDEBAR
# -----------------------------------------------------------------------------
(
    time_preset,
    custom_start_date,
    custom_end_date,
    search_id_kw,
    sample_toggle,
    live_sync,
    sync_interval,
    force_r2,
) = render_sidebar()

# -----------------------------------------------------------------------------
# 3. QUẢN LÝ DỮ LIỆU TỔNG (LOCAL DISK CACHE & SESSION_STATE)
# -----------------------------------------------------------------------------
force_refresh = st.session_state.pop("force_refresh_r2", False)
needs_load = (
    force_refresh
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
            force_refresh = True
            st.session_state["has_new_snapshot_toast"] = True
    except Exception:
        pass

if needs_load:
    try:
        with st.spinner("⚡ Đang nạp dữ liệu tốc độ cao (Local Disk Cache & 32 luồng R2)..."):
            df_all, stats, meta_key, prefix, load_source = load_and_process_events(
                sample_toggle, force_refresh=force_refresh
            )
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

# -----------------------------------------------------------------------------
# 4. LỌC DỮ LIỆU TỨC THÌ TRONG BỘ NHỚ RAM
# -----------------------------------------------------------------------------
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

if search_id_kw:
    df_filtered = df_filtered[df_filtered["id_clean"].str.contains(search_id_kw, case=False, na=False)]

# -----------------------------------------------------------------------------
# 5. TIÊU ĐỀ & THANH TRẠNG THÁI
# -----------------------------------------------------------------------------
render_header(
    df_filtered,
    stats,
    time_preset,
    sample_toggle,
    live_sync,
    sync_interval,
    load_source,
    BUCKET
)

if df_filtered.empty:
    st.warning("⚠️ Không có bản ghi nào phù hợp với bộ lọc đã chọn. Hãy điều chỉnh khoảng thời gian hoặc từ khóa tìm kiếm ở sidebar bên trái.")
    st.stop()

# -----------------------------------------------------------------------------
# 6. HÀNG 4 THẺ CHỈ SỐ KPI CHÍNH
# -----------------------------------------------------------------------------
total_views, unique_ips, unique_countries, unique_ids = render_kpi_metrics(df_filtered)

# -----------------------------------------------------------------------------
# 7. PHÂN CHIA HỆ THỐNG 5 TAB CHUYÊN NGHIỆP
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tổng Quan Hệ Thống",
    "🎯 Khảo Sát Theo ID",
    "🔬 Phân Tích Chuyên Sâu",
    "📋 Dữ Liệu & Xuất File",
    "💡 Đề Xuất Quyết Định"
])

with tab1:
    country_df = render_tab_overview(df_filtered)

with tab2:
    render_tab_id_detail(df_filtered, df_all, total_views, time_preset)

with tab3:
    render_tab_analytics(df_filtered, df_all)

with tab4:
    render_tab_export(df_filtered)

with tab5:
    render_tab_insights(df_filtered, total_views, country_df)

# -----------------------------------------------------------------------------
# 8. VÒNG LẶP ĐỒNG BỘ THỜI GIAN THỰC (LIVE SYNC AUTO-POLLING)
# -----------------------------------------------------------------------------
if live_sync:
    time.sleep(sync_interval)
    st.rerun()
