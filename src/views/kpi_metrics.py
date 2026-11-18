import streamlit as st


def render_kpi_metrics(df_filtered):
    """Hiển thị hàng 4 thẻ chỉ số KPI cân đối, rõ ràng và chống bôi đen nhầm."""
    total_views = len(df_filtered)
    unique_ips = df_filtered["ip"].dropna().nunique()
    unique_countries = df_filtered["country_clean"].nunique()
    unique_ids = df_filtered["id_clean"].nunique()

    top_device = df_filtered["device_clean"].mode()[0] if not df_filtered.empty else "N/A"
    top_device_pct = (df_filtered["device_clean"].value_counts(normalize=True).iloc[0] * 100) if not df_filtered.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        with st.container(border=True):
            st.metric("TỔNG LƯỢT TRUY CẬP", f"{total_views:,}", f"{unique_ids:,} nhóm/ID")
    with k2:
        with st.container(border=True):
            st.metric("KHÁCH DUY NHẤT (IP)", f"{unique_ips:,}", f"{(unique_ips / total_views * 100):.1f}% tỷ lệ IP mới")
    with k3:
        with st.container(border=True):
            st.metric("QUỐC GIA PHỦ SÓNG", f"{unique_countries}", f"Top 1: {df_filtered['country_clean'].mode()[0]}")
    with k4:
        with st.container(border=True):
            st.metric("THIẾT BỊ PHỔ BIẾN", f"{top_device.upper()}", f"{top_device_pct:.1f}% lưu lượng")

    return total_views, unique_ips, unique_countries, unique_ids
