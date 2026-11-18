# Basin Catalog — Web Access Analytics Dashboard

Hệ thống phân tích và trực quan hóa dữ liệu truy cập web xây dựng trên nền tảng **Python**, **Streamlit**, **Apache Iceberg (PyIceberg)** và **Cloudflare R2 Lakehouse**.

---

## 🌟 Tính Năng Nổi Bật

1. **Kiến trúc Module hóa (Clean Architecture):**
   * Tách nhỏ mã nguồn thành các module độc lập trong thư mục `src/` (`config`, `styles`, `data_loader`, `analytics`, `views/`).
2. **Giao diện thích ứng thông minh (Light & Dark Mode):**
   * Hỗ trợ mượt mà cả chế độ sáng (Light Mode) và chế độ tối (Dark Mode) mà không bị lỗi màu.
   * Chặn bôi đen và sao chép ở các vùng thẻ số liệu, tiêu đề và thanh trạng thái.
3. **Phân tích truy cập web thời gian thực (Real-time Lakehouse Analytics):**
   * Kết nối và truy vấn trực tiếp (**Direct Query**) vào bảng Apache Iceberg trên Cloudflare R2 bucket `visitors`.
   * Bộ nhớ đệm cục bộ (**Local Disk Cache**) nạp dữ liệu tức thì trong **0.02 giây**.
4. **Hệ thống 5 Tab chuyên nghiệp:**
   * **Tab 1: Tổng Quan Hệ Thống:** Diễn biến theo thời gian, Top quốc gia, Cơ cấu thiết bị.
   * **Tab 2: Khảo Sát Theo ID:** Đầy đủ 5 biểu đồ chuyên sâu cho từng ID (Timeline, Khung giờ, Quốc gia, Thiết bị, IP).
   * **Tab 3: Phân Tích Chuyên Sâu (Analytics Pro):** Phát hiện bất thường Z-score, cảnh báo Bot/Spam, phân tích khách quay lại, dải mạng Subnet /24, và bàn so sánh đối kháng A/B giữa 2 ID.
   * **Tab 4: Dữ Liệu & Xuất File:** Xuất CSV toàn bộ, CSV từng ID, hoặc gói ZIP tách riêng từng ID.
   * **Tab 5: Đề Xuất Quyết Định:** Khuyến nghị thực tế cho Hạ tầng CDN, UI/UX và Vận hành.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Cục Bộ (Local)

```bash
# 1. Clone repository
git clone https://github.com/ngoctuls2005-dev/BasinCatalog.git
cd BasinCatalog

# 2. Tạo môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate    # macOS/Linux

# 3. Cài đặt các thư viện
pip install -r requirements.txt

# 4. Cấu hình biến môi trường
cp .env.example .env
# (Điền thông tin R2 credentials của bạn vào file .env)

# 5. Khởi động ứng dụng
streamlit run app.py
```

---

## ☁️ Hướng Dẫn Deploy Lên Streamlit Community Cloud (Miễn Phí 24/7)

1. Truy cập [share.streamlit.io](https://share.streamlit.io) và đăng nhập bằng tài khoản GitHub.
2. Nhấp **New app**:
   * **Repository:** `ngoctuls2005-dev/BasinCatalog`
   * **Branch:** `main`
   * **Main file path:** `app.py`
3. Nhấp vào **Advanced settings...** $\rightarrow$ mục **Secrets**, dán cấu hình R2 credentials của bạn vào rồi bấm **Deploy!**
