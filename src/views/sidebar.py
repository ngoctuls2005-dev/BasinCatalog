from datetime import datetime, timedelta
import streamlit as st
from src.config import TIME_PRESETS, DEFAULT_USE_SAMPLE


def render_sidebar():
    """Hiển thị thanh điều khiển Sidebar gọn gàng, tinh tế và không rối mắt."""
    with st.sidebar:
        st.markdown("<h3 class='no-select'>📊 Basin Catalog</h3>", unsafe_allow_html=True)
        st.caption("Lakehouse Analytics • Cloudflare R2")
        st.markdown("---")

        # 1. KHOẢNG THỜI GIAN
        time_preset = st.selectbox(
            "⏱️ Khoảng thời gian:",
            options=TIME_PRESETS,
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

        # 2. TÌM NHANH ID
        search_id_kw = st.text_input("🔍 Tìm nhanh ID / Nhóm:", placeholder="Gõ tên ID (vd: raumaxao)...")

        st.markdown("---")
        
        # 3. NGUỒN DỮ LIỆU & LIVE SYNC (GOM GỌN TRONG EXPANDER)
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

        force_r2 = False
        if st.button("🔄 Nạp Lại Dữ Liệu R2", use_container_width=True):
            st.session_state.pop("cached_df_all", None)
            st.session_state.pop("cached_stats", None)
            st.session_state["force_refresh_r2"] = True
            st.cache_data.clear()
            st.rerun()

        return (
            time_preset,
            custom_start_date,
            custom_end_date,
            search_id_kw,
            sample_toggle,
            live_sync,
            sync_interval,
            force_r2,
        )
