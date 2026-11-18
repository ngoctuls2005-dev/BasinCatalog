import json
import os
import time
from datetime import datetime
import pandas as pd

from src.config import (
    ACCOUNT_ID,
    ACCESS_KEY_ID,
    SECRET_ACCESS_KEY,
    BUCKET,
    R2_ENDPOINT,
    CACHE_DIR,
    CACHE_PARQUET_FILE,
    CACHE_META_FILE,
)


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


def clean_events(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Quy chuẩn làm sạch dữ liệu: lọc epoch 1970, test data, chuẩn hóa quốc gia và thiết bị."""
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
            if curr_meta == cached_meta.get("meta_key"):
                return cached_df, cached_meta.get("clean_stats", {}), curr_meta, prefix, "Cache SSD (0.02s)"
        except Exception:
            return cached_df, cached_meta.get("clean_stats", {}), cached_meta.get("meta_key", ""), known_p, "Cache Offline"

    meta_key, prefix = latest_metadata_key(s3, known_prefix=known_p)
    raw_df = iceberg_events(s3, meta_key)
    cleaned_df, clean_stats = clean_events(raw_df)
    
    save_local_cache(cleaned_df, {
        "meta_key": meta_key,
        "prefix": prefix,
        "clean_stats": clean_stats,
        "updated_at": datetime.now().isoformat()
    })
    return cleaned_df, clean_stats, meta_key, prefix, "Tải Mới Từ R2"
