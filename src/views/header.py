import streamlit as st


def render_header(
    df_filtered,
    stats,
    time_preset,
    sample_toggle,
    live_sync,
    sync_interval,
    load_source,
    bucket_name
):
    """Hiển thị Header và thanh trạng thái Status Chip Bar thích ứng."""
    col_header_l, col_header_r = st.columns([3, 1])
    with col_header_l:
        st.markdown("<h1 class='no-select' style='margin-bottom: 0px;'>Phân Tích Dữ Liệu Truy Cập Web</h1>", unsafe_allow_html=True)
        st.caption("Nền tảng Apache Iceberg Direct Query trên Cloudflare R2 Bucket")

    with col_header_r:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if live_sync:
            st.success(f"🔴 Live Sync: {sync_interval}s")
        else:
            st.info("🟢 Chế độ: Đã kết nối")

    min_dt_str = df_filtered["datetime"].min().strftime('%d/%m/%Y %H:%M') if not df_filtered.empty else "N/A"
    max_dt_str = df_filtered["datetime"].max().strftime('%d/%m/%Y %H:%M') if not df_filtered.empty else "N/A"
    source_label = "Dữ liệu mẫu" if sample_toggle else f"R2 ({bucket_name})"

    st.markdown(f"""
    <div class="status-bar-container no-select">
        <div class="status-chip">⏱️ Khoảng xem: <b>{time_preset}</b> ({min_dt_str} → {max_dt_str})</div>
        <div class="status-chip">🌐 Nguồn: <b>{source_label}</b></div>
        <div class="status-chip">🚀 Tốc độ: <b>{load_source}</b></div>
        <div class="status-chip">📁 Tổng kho: <b>{stats.get('clean', 0):,}</b> bản ghi</div>
        <div class="status-chip">⚡ Đang lọc: <b>{len(df_filtered):,}</b> bản ghi</div>
    </div>
    """, unsafe_allow_html=True)
