# Hướng Dẫn Cài Đặt, Khởi Động & Sử Dụng Hệ Thống Basin Catalog

Tài liệu này hướng dẫn chi tiết cách cài đặt, khởi động và khai thác hệ thống phân tích dữ liệu truy cập web **Basin Catalog** xây dựng trên nền tảng **Python**, **Streamlit**, **PyIceberg** và **Cloudflare R2 (Apache Iceberg Lakehouse)**.

---

## 1. Yêu Cầu Hệ Thống

| Thành phần | Yêu cầu khuyến nghị |
|---|---|
| **Hệ điều hành** | Windows 10/11, macOS, hoặc Linux |
| **Python** | Python 3.9 đến 3.11 (Khuyến nghị **Python 3.11**) |
| **pip** | Đi kèm Python |
| **Mạng Internet** | Cần để tải thư viện từ PyPI và kết nối tới Cloudflare R2 |

---

## 2. Cấu Trúc Dự Án Module Hóa Chuẩn Mực

Mã nguồn dự án đã được chia nhỏ thành các module chức năng độc lập giúp việc bảo trì và nâng cấp dễ dàng:

```text
BasinCatalog/
├── app.py                         # Điểm khởi chạy ứng dụng chính (Entry point)
├── requirements.txt               # Danh sách thư viện Python
├── .env.example                   # Mẫu cấu hình biến môi trường
├── run.bat                        # File khởi động nhanh 1-Click trên Windows
├── HUONG_DAN_CHAY_BASIN_CATALOG.md# Hướng dẫn chi tiết
├── README.md                      # Tài liệu tổng quan dự án
└── src/                           # Thư mục mã nguồn module
    ├── config.py                  # Cấu hình, biến môi trường, màu sắc & hằng số
    ├── styles.py                  # Giao diện thích ứng (Light/Dark mode) & Chặn bôi đen
    ├── data_loader.py             # Đọc Iceberg R2, nạp 32 luồng & Local Disk Cache
    ├── analytics.py               # Giải thuật phát hiện bất thường, khách quay lại, Subnet
    └── views/                     # Các thành phần giao diện
        ├── sidebar.py             # Bộ lọc Sidebar
        ├── header.py              # Tiêu đề & thanh trạng thái
        ├── kpi_metrics.py         # 4 thẻ chỉ số KPI chính
        ├── tab_overview.py        # Tab 1: Tổng quan hệ thống
        ├── tab_id_detail.py       # Tab 2: Khảo sát chuyên sâu theo ID (5 biểu đồ)
        ├── tab_analytics.py       # Tab 3: Bộ công cụ phân tích dữ liệu nâng cao
        ├── tab_export.py          # Tab 4: Trung tâm xuất file (CSV, ZIP)
        └── tab_insights.py        # Tab 5: Đề xuất quyết định hành động
```

---

## 3. Khởi Động Nhanh (1-Click Cho Windows)

1. Nhấp đúp chuột vào tệp **`run.bat`**.
2. Hệ thống sẽ tự động tạo môi trường ảo `.venv`, cài đặt thư viện và mở dashboard tại: **`http://localhost:8501`**.

---

## 4. Các Tính Năng Đột Phá Mới

### 4.1. Thích Ứng Hoàn Hảo Cả Chế Độ Sáng & Tối (Light & Dark Mode)
* Hệ thống màu sắc được thiết kế động theo biến môi trường Streamlit (`CSS variables`).
* Không bị lỗi màu hay tương phản kém khi người dùng chuyển sang Light Mode.

### 4.2. Bảo Vệ Giao Diện (Chặn Bôi Đen & Sao Chép Không Cần Thiết)
* Chặn thao tác vô tình bôi đen xanh làm xấu giao diện ở các vùng: Thẻ KPI, Tiêu đề biểu đồ, Thanh trạng thái, Nút điều hướng tab.
* Các bảng số liệu, bảng tra cứu chi tiết và mã ID vẫn cho phép bôi đen để sao chép thuận tiện khi cần.

### 4.3. Tab 3 Mới: Phân Tích Chuyên Sâu (Analytics Pro)
1. **Phát hiện đột biến lưu lượng (Z-score Anomaly Detection):** Tự động phát hiện các khung giờ có lưu lượng tăng vọt bất thường.
2. **Cảnh báo IP nghi vấn (Bot/Crawler Detection):** Phát hiện IP chiếm tỷ trọng quá lớn hoặc gửi request dày đặc trong thời gian ngắn.
3. **Phân tích lòng trung thành (Visitor Retention):** Phân loại khách vãng lai (1 lần), khách khám phá (2-5 lần), khách nòng cốt (>15 lần).
4. **Phân tích dải mạng (Subnet /24 Clustering):** Thống kê dải mạng IPv4 phổ biến và tỷ lệ IPv4 vs IPv6.
5. **Bàn so sánh đối kháng A/B giữa 2 ID:** Đặt 2 nhóm/ID cạnh nhau để so sánh trực quan về lưu lượng, thiết bị và số lượng IP.
