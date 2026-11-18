@echo off
chcp 65001 >nul
echo ========================================================
echo    BASIN CATALOG - KHỞI ĐỘNG HỆ THỐNG PHÂN TÍCH
echo ========================================================
echo.

IF NOT EXIST ".venv" (
    echo [1/3] Đang tự động tạo môi trường ảo .venv...
    python -m venv .venv
    echo [2/3] Đang cài đặt các thư viện cần thiết...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
) ELSE (
    echo [1/2] Môi trường ảo .venv đã sẵn sàng.
)

echo.
echo [2/2] Đang khởi động Streamlit server tại http://localhost:8501 ...
.\.venv\Scripts\streamlit.exe run app.py --server.port 8501
pause
