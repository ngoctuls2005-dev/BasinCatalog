# Hướng Dẫn Cài Đặt, Khởi Động & Sử Dụng Hệ Thống Basin Catalog

Tài liệu này hướng dẫn chi tiết cách cài đặt, khởi động và khai thác hệ thống phân tích dữ liệu truy cập web **Basin Catalog** xây dựng trên nền tảng **Python**, **Streamlit**, **PyIceberg** và **Cloudflare R2 (Apache Iceberg Lakehouse)**.

---

## 1. Yêu Cầu Hệ Thống

| Thành phần | Yêu cầu khuyến nghị |
|---|---|
| **Hệ điều hành** | Windows 10/11, macOS, hoặc Linux |
| **Python** | Python 3.9 đến 3.11 (Khuyến nghị **Python 3.11** để tương thích tốt nhất với PyIceberg và PyArrow) |
| **pip** | Đi kèm Python |
| **Mạng Internet** | Cần để tải thư viện từ PyPI và kết nối tới Cloudflare R2 khi `USE_SAMPLE=0` |

Kiểm tra phiên bản Python trên máy tính:
```bash
python --version
```

---

## 2. Cấu Trúc Dự Án Đóng Gói

Gói thư mục phân phối chuẩn gồm các tệp:
```text
BasinCatalog/
├── app.py                         # Ứng dụng Dashboard Streamlit hoàn chỉnh
├── requirements.txt               # Danh sách thư viện Python cần thiết
├── .env                           # File cấu hình khóa kết nối Cloudflare R2
├── run.bat                        # File khởi động nhanh 1-Click trên Windows
├── HUONG_DAN_CHAY_BASIN_CATALOG.md# Hướng dẫn chi tiết này
└── BasinCatalog_Package.zip       # Gói nén cài đặt sẵn sàng gửi cho người khác
```

Danh sách thư viện trong [requirements.txt](requirements.txt):
* `streamlit`: Nền tảng giao diện web dashboard và máy chủ ứng dụng.
* `python-dotenv`: Đọc biến môi trường từ tệp `.env`.
* `pandas`: Xử lý và làm sạch dữ liệu bảng.
* `pyiceberg[pyarrow]`: Thư viện đọc và quét bảng Apache Iceberg trực tiếp từ Object Storage.
* `boto3`: Thư viện AWS SDK dùng để kết nối S3 API của Cloudflare R2.
* `plotly`: Vẽ biểu đồ tương tác cao cấp (Line, Bar, Donut, Heatmap).

---

## 3. Khởi Động Nhanh (1-Click Cho Windows)

Nếu bạn dùng hệ điều hành Windows:
1. Giải nén thư mục `BasinCatalog`.
2. Nhấp đúp chuột vào tệp **`run.bat`**.
   * Hệ thống sẽ tự động tạo môi trường ảo `.venv`, tự động cài đặt toàn bộ thư viện nếu chưa có, và tự động mở dashboard tại địa chỉ: **`http://localhost:8501`**.

---

## 4. Cài Đặt Thủ Công (Mọi Hệ Điều Hành)

Mở Terminal (macOS/Linux) hoặc PowerShell (Windows) tại thư mục dự án:

### Bước 4.1: Tạo và kích hoạt môi trường ảo (`.venv`)
* **Trên Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **Trên macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Bước 4.2: Cài đặt các thư viện cần thiết
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 4.3: Khởi động máy chủ Streamlit
```bash
streamlit run app.py
```
Mở trình duyệt web tại địa chỉ: **`http://localhost:8501`**.

---

## 5. Cấu Hình Biến Môi Trường ([.env](.env))

Tệp `.env` nằm trong thư mục gốc và được ứng dụng tự động nạp khi khởi động:

```ini
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_BUCKET=visitors
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
USE_SAMPLE=0
```

* **`USE_SAMPLE=0`**: Đọc trực tiếp dữ liệu thực từ bảng Apache Iceberg trên bucket Cloudflare R2.
* **`USE_SAMPLE=1`**: Dùng dữ liệu giả lập sinh tự động trong bộ nhớ (dùng để kiểm thử offline khi không có internet).
* **Lưu ý quan trọng về Secret Key:** `R2_SECRET_ACCESS_KEY` phải dài đúng 64 ký tự và nằm trên **một dòng duy nhất** (không được ngắt dòng để tránh lỗi xác thực `SignatureDoesNotMatch`).

---

## 6. Hướng Dẫn Sử Dụng Các Tính Năng Trên Dashboard

### 6.1. Tăng Tốc Truy Xuất Siêu Tốc (Local Disk Cache & 32 Luồng Tải Song Song)
* **Khởi động tức thì (0.02s):** Hệ thống lưu bản sao sạch vào thư mục ẩn `.cache/` (chỉ gồm đúng 2 tệp `events_cache.parquet` và `events_cache_meta.json`, không bao giờ sinh tệp rác).
* **Kiểm tra thông minh:** Khi mở ứng dụng, hệ thống chỉ kiểm tra mã snapshot metadata trên Cloudflare R2:
  * Nếu không có commit mới: Nạp trực tiếp từ ổ SSD chỉ mất **0.02 giây**.
  * Nếu phát hiện có dữ liệu mới trên R2: Tự động kích hoạt **32 luồng tải song song (PyIceberg 32 workers)** để kéo dữ liệu trong ~1.5 giây và làm mới bộ nhớ đệm.
* **Mặc định:** Hệ thống luôn khởi động với mốc thời gian **"24 giờ qua (Mặc định)"**.
* **Thứ tự lựa chọn chuẩn xác:**
  1. `24 giờ qua (Mặc định)`
  2. `7 ngày qua`
  3. `30 ngày qua`
  4. `Toàn bộ thời gian (Tất cả dữ liệu)` *(nằm ở giữa 30 ngày qua và Tùy chỉnh)*
  5. `Tùy chỉnh khoảng ngày...`
* **Tối ưu hóa RAM Caching:** Toàn bộ data tổng từ Cloudflare R2 được nạp sẵn vào RAM (`st.session_state`). Khi bạn chuyển đổi giữa các mốc thời gian, ứng dụng lọc tức thì trong RAM dưới 0.01s mà **hoàn toàn không phải truy xuất lại R2**.

---

### 6.2. Chế Độ Truy Xuất Thời Gian Thực (🔴 Live Sync)
* **Khả năng thời gian thực:** Bạn có thể bật tính năng **"🔴 Truy xuất theo thời gian thực (Live Sync)"** tại thanh Sidebar bên trái.
* **Cơ chế hoạt động:**
  * Cho phép chọn chu kỳ kiểm tra tự động: **15 giây**, **30 giây**, **60 giây** hoặc **120 giây**.
  * Hệ thống quét định kỳ tệp snapshot metadata mới nhất trên Cloudflare R2 (`*.metadata.json`).
  * Nếu phát hiện có bản ghi mới được commit vào bảng Iceberg, hệ thống sẽ tự động cập nhật ngay dữ liệu vào RAM và vẽ lại toàn bộ biểu đồ mà không cần người dùng thao tác.

---

### 6.3. Tab 1: Phân Tích & Biểu Đồ Toàn Cục
* **5 Thẻ Chỉ Số KPI**: Tổng lượt xem, Số IP duy nhất, Số quốc gia, Thiết bị phổ biến nhất, Số lượng ID/Nhóm.
* **Biểu Đồ Timeline**: Diễn biến số lượng truy cập theo giờ/ngày phân tách theo từng thiết bị.
* **Biểu Đồ Quốc Gia**: Phân bổ top 10 quốc gia có lưu lượng cao nhất.
* **Biểu Đồ Thiết Bị (Donut Chart)**: Tỷ trọng phần trăm Mobile, Desktop, Tablet.
* **Ma Trận Đối Sánh**: Bảng thống kê chéo giữa Quốc Gia $\times$ Thiết Bị.

---

### 6.4. Tab 2: Biểu Đồ Chi Tiết Dành Riêng Cho Từng ID
* Mặc định được thiết lập cho ID **`raumaxao`** (hoặc bạn có thể chọn bất kỳ ID nào trong 247 nhóm tại dropdown).
* **5 Biểu Đồ Riêng Biệt Cho ID Được Chọn**:
  1. *Diễn biến thời gian truy cập của riêng ID*: Xem tần suất hoạt động theo ngày/giờ của ID đó.
  2. *Cơ cấu loại thiết bị của riêng ID*: Tỷ trọng % Mobile vs Desktop của riêng ID đó.
  3. *Top Địa Chỉ IP của riêng ID*: Thống kê các IP (IPv4 / IPv6) mà ID này đã sử dụng.
  4. *Khung giờ online trong ngày (0h - 23h)*: Nhận diện thói quen hoạt động theo từng khung giờ trong ngày của ID.
  5. *Phân bố quốc gia*: Các quốc gia ghi nhận request của ID này.
* **Nhật ký truy cập chi tiết**: Toàn bộ lịch sử các phiên truy cập của riêng ID này kèm nút tải file CSV riêng.

---

### 6.5. Tab 3: Bảng Dữ Liệu Đầy Đủ & 3 Chế Độ Xuất File
Phần bảng dữ liệu cung cấp 3 tùy chọn xuất tệp:
1. **Xuất toàn bộ bản ghi (`📥 Tải toàn bộ CSV`)**: Tải về toàn bộ dữ liệu đang hiển thị theo bộ lọc.
2. **Xuất riêng theo từng ID cụ thể (`📥 Tải CSV ID: [tên ID]`)**: Chọn bất kỳ ID nào từ danh sách và tải file CSV chỉ chứa dữ liệu của riêng ID đó.
3. **Xuất gói file ZIP (`📦 Tải ZIP (Tất cả ID tách riêng từng file CSV)`)**: Hệ thống tự động phân tách toàn bộ dữ liệu thành từng file CSV độc lập theo từng ID (`id_raumaxao.csv`, `id_nhom_07.csv`,...) và nén lại thành 1 file ZIP duy nhất để tải về.

---

### 6.6. Tab 4: Đề Xuất Ra Quyết Định Dựa Trên Dữ Liệu (Actionable Decisions)
Tự động tính toán các số liệu định lượng để đưa ra khuyến nghị thực tế:
* **Hạ tầng & CDN**: Thiết lập Edge Cache cho các quốc gia dẫn đầu để giảm độ trễ (TTFB).
* **Giao diện & UI/UX**: Ưu tiên chiến lược Mobile-First hoặc Desktop-First tùy theo tỷ lệ thiết bị thực tế.
* **Vận hành & Tiếp thị**: Định vị nhóm khách hàng trọng điểm dựa trên tần suất truy cập của từng ID.

---

## 7. Quy Trình Làm Sạch Dữ Liệu (`clean_events`)

Ứng dụng tự động chuẩn hóa dữ liệu theo các quy tắc nghiêm ngặt:
* **Lỗi thời gian**: Loại bỏ các dòng `time` bị trống hoặc trước năm 2000 (xóa sạch các dòng bị lỗi epoch 1970).
* **Lọc dữ liệu rác/thử nghiệm**: Loại bỏ dòng có mã `id` bắt đầu bằng `test`, `synthetic`, `sim-`, `probe`, `ping-`, `web-access-`.
* **Chuẩn hóa Quốc gia**: Viết hoa; gộp `Việt Nam`, `Vietnam`, `Viet Nam` $\rightarrow$ `VN`; gộp `unknown`, `all` $\rightarrow$ `KHÁC`.
* **Chuẩn hóa Thiết bị**: Gom về 4 nhóm chuẩn: `desktop`, `mobile`, `tablet`, `khác` theo từ khóa nhận diện.

---

## 8. Hướng Dẫn Đóng Gói & Chia Sẻ Cho Người Khác

Gói tệp tin nén **`BasinCatalog_Package.zip`** đã được tạo sẵn tại thư mục dự án. Để chia sẻ cho đồng nghiệp hoặc người dùng khác:
1. Gửi tệp **`BasinCatalog_Package.zip`**.
2. Người nhận chỉ cần giải nén thư mục ra máy tính của họ.
3. Nhấp đúp vào **`run.bat`** (Windows) hoặc chạy `streamlit run app.py` (macOS/Linux) là hệ thống sẽ tự động chạy ngay lập tức.
