import streamlit as st

def apply_custom_styles():
    """Áp dụng hệ thống CSS thích ứng thông minh (Adaptive Theme cho cả Dark Mode & Light Mode)

    Đồng thời chặn bôi đen/sao chép ở các thành phần giao diện không cần thiết.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* 1. KHU VỰC CHẶN BÔI ĐEN VÀ SAO CHÉP (USER-SELECT: NONE) */
        .no-select,
        .status-bar-container,
        .status-chip,
        div[data-testid="stMetric"],
        div[data-testid="stMetricLabel"],
        div[data-testid="stMetricValue"],
        div[data-testid="stMetricDelta"],
        .stTabs [data-baseweb="tab-list"],
        .stTabs [data-baseweb="tab"],
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stCaption,
        .chart-header-no-select {
            user-select: none !important;
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
        }

        /* 2. BỐ CỤC TRANG GỌN GÀNG */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 1440px;
        }

        /* 3. THANH TRẠNG THÁI (STATUS CHIP BAR) - TỰ ĐỘNG THÍCH ỨNG LIGHT / DARK */
        .status-bar-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            padding: 8px 14px;
            background: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 10px;
            margin-bottom: 1.2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(128, 128, 128, 0.12) !important;
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-color) !important;
        }
        .status-chip b {
            color: #0284c7 !important; /* Sky Blue đậm rõ trên cả nền sáng và tối */
        }
        @media (prefers-color-scheme: dark) {
            .status-chip b {
                color: #38bdf8 !important;
            }
        }

        /* 4. CONTAINER CARD CÓ VIỀN - THÍCH ỨNG LIGHT & DARK */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        /* 5. METRIC CARDS - THÍCH ỨNG LIGHT & DARK */
        div[data-testid="stMetric"] {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            border-radius: 10px;
            padding: 12px 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-color) !important;
            opacity: 0.75;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.75rem !important;
            font-weight: 700 !important;
            color: #0284c7 !important;
        }
        @media (prefers-color-scheme: dark) {
            div[data-testid="stMetricValue"] {
                color: #38bdf8 !important;
            }
        }

        /* 6. TABS ĐỒNG BỘ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: var(--secondary-background-color) !important;
            padding: 6px;
            border-radius: 10px;
            border: 1px solid rgba(128, 128, 128, 0.18);
            margin-bottom: 1.2rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 38px;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: 600;
            color: var(--text-color) !important;
            opacity: 0.8;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(128, 128, 128, 0.2) !important;
            opacity: 1 !important;
            color: #0284c7 !important;
        }
        @media (prefers-color-scheme: dark) {
            .stTabs [aria-selected="true"] {
                color: #38bdf8 !important;
            }
        }

        /* 7. SIDEBAR VIỀN MỎNG THOÁNG ĐÃNG */
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }
    </style>
    """, unsafe_allow_html=True)


def get_plot_layout_config():
    """Cung cấp cấu hình layout chuẩn cho biểu đồ Plotly để hiển thị hoàn hảo ở cả Light và Dark mode."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.12)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.12)"),
    )
