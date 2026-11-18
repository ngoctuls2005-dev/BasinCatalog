import os
import streamlit as st
from dotenv import load_dotenv

# Kích hoạt 32 luồng tải song song cho PyIceberg
os.environ["PYICEBERG_MAX_WORKERS"] = "32"

# Nạp file .env từ thư mục gốc dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

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

# Cấu hình kết nối Cloudflare R2
ACCOUNT_ID = get_config("R2_ACCOUNT_ID", "")
BUCKET = get_config("R2_BUCKET", "visitors")
ACCESS_KEY_ID = get_config("R2_ACCESS_KEY_ID", "")
SECRET_ACCESS_KEY = get_config("R2_SECRET_ACCESS_KEY", "")
DEFAULT_USE_SAMPLE = get_config("USE_SAMPLE", "0") == "1"
R2_ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

# Đường dẫn lưu trữ bộ nhớ đệm cục bộ
CACHE_DIR = os.path.join(BASE_DIR, ".cache")
CACHE_PARQUET_FILE = os.path.join(CACHE_DIR, "events_cache.parquet")
CACHE_META_FILE = os.path.join(CACHE_DIR, "events_cache_meta.json")

# Bảng màu sắc cao cấp chuẩn mực
COLOR_PALETTE = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f472b6", "#a78bfa"]

# Danh sách tùy chọn thời gian chuẩn xác
TIME_PRESETS = [
    "24 giờ qua (Mặc định)",
    "7 ngày qua",
    "30 ngày qua",
    "Toàn bộ thời gian (Tất cả dữ liệu)",
    "Tùy chỉnh khoảng ngày..."
]
