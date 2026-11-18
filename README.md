# Basin Catalog — Web Access Analytics Dashboard

Hệ thống phân tích và trực quan hóa dữ liệu truy cập web xây dựng trên nền tảng **Python**, **Streamlit**, **Apache Iceberg (PyIceberg)** và **Cloudflare R2 Lakehouse**.

---

## 🌟 Tính Năng Nổi Bật

1. **Phân tích truy cập web thời gian thực (Real-time Lakehouse Analytics):**
   * Kết nối và truy vấn trực tiếp (**Direct Query**) vào bảng Apache Iceberg trên Cloudflare R2 bucket `visitors`.
   * Trả lời tức thì 3 câu hỏi cốt lõi: Số lượng truy cập theo khung giờ, nguồn gốc quốc gia, cơ cấu thiết bị (Mobile vs Desktop vs Tablet).
2. **Khảo sát chuyên sâu từng ID:**
   * Hồ sơ biểu đồ chuyên biệt cho từng mã ID (mặc định: `raumaxao`).
   * Phân tích khung giờ online trong ngày (0h - 23h), lịch sử truy cập, cơ cấu thiết bị và danh sách địa chỉ IP đã sử dụng.
3. **Trung tâm xuất dữ liệu đa năng:**
   * Xuất toàn bộ bảng dữ liệu ra CSV (UTF-8-BOM tương thích Microsoft Excel).
   * Xuất file CSV riêng cho từng ID được chọn.
   * Xuất gói nén **ZIP** tự động tách riêng mỗi ID thành 1 file CSV độc lập.
4. **Tối ưu hóa tốc độ siêu tốc:**
   * Tải song song **32 luồng (PyIceberg Multi-threading)**.
   * Bộ nhớ đệm cục bộ (**Local Disk Cache**) nạp dữ liệu tức thì trong **0.02 giây**.
   * Tự động phát hiện snapshot mới trên Cloudflare R2 khi có commit mới (**Live Sync**).

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Cục Bộ (Local)

### 1. Yêu cầu môi trường
* Python 3.9 - 3.11 (Khuyến nghị **Python 3.11**).
* Git.

### 2. Cài đặt nhanh
```bash
# 1. Clone repository
git clone https://github.com/ngoctuls2005-dev/BasinCatalog.git
cd BasinCatalog

# 2. Tạo môi trường ảo
python -m venv .venv

# Kích hoạt trên Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Hoặc trên macOS/Linux:
source .venv/bin/activate

# 3. Cài đặt các thư viện
pip install -r requirements.txt

# 4. Cấu hình biến môi trường
cp .env.example .env
# (Mở file .env và điền thông tin R2 credentials của bạn)

# 5. Khởi động ứng dụng
streamlit run app.py
```
Ứng dụng sẽ tự động mở tại: `http://localhost:8501`.

---

## ☁️ Hướng Dẫn Deploy Lên Streamlit Community Cloud (Miễn Phí 24/7)

1. Truy cập [share.streamlit.io](https://share.streamlit.io) và đăng nhập bằng tài khoản GitHub.
2. Nhấp **New app**:
   * **Repository:** `ngoctuls2005-dev/BasinCatalog`
   * **Branch:** `main`
   * **Main file path:** `app.py`
3. Nhấp vào **Advanced settings...** $\rightarrow$ mục **Secrets**, dán cấu hình sau:
```toml
R2_ACCOUNT_ID = "your_cloudflare_account_id"
R2_BUCKET = "visitors"
R2_ACCESS_KEY_ID = "your_r2_access_key_id"
R2_SECRET_ACCESS_KEY = "your_r2_secret_access_key"
USE_SAMPLE = "0"
```
4. Nhấp **Deploy**! Ứng dụng sẽ tự động khởi tạo và chạy online 24/7.
