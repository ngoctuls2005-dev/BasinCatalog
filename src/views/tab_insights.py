import streamlit as st


def render_tab_insights(df_filtered, total_views, country_df):
    """Tab 5: Đề xuất hành động và quyết định tối ưu hóa dựa trên số liệu thực tế."""
    mobile_count = df_filtered[df_filtered["device_clean"] == "mobile"].shape[0]
    mobile_pct = (mobile_count / total_views * 100) if total_views > 0 else 0
    desktop_count = df_filtered[df_filtered["device_clean"] == "desktop"].shape[0]
    desktop_pct = (desktop_count / total_views * 100) if total_views > 0 else 0

    top_country_name = country_df.iloc[0]["Quốc gia"] if not country_df.empty else "N/A"
    top_country_pct = (country_df.iloc[0]["Lượt xem"] / total_views * 100) if not country_df.empty and total_views > 0 else 0
    top_group_id = df_filtered["id_clean"].value_counts().index[0] if not df_filtered.empty else "N/A"
    top_group_views = df_filtered["id_clean"].value_counts().iloc[0] if not df_filtered.empty else 0

    d1, d2, d3 = st.columns(3)

    with d1:
        with st.container(border=True):
            st.markdown("#### 🌐 1. Hạ Tầng & CDN")
            st.markdown(f"""
            - **Thực trạng:** Quốc gia **{top_country_name}** chiếm ưu thế với **{top_country_pct:.1f}%** toàn bộ lưu lượng.
            - **Đề xuất hành động:**
              - Bật Cloudflare Edge Caching định tuyến máy chủ tối ưu tại **{top_country_name}** để giảm TTFB xuống dưới 100ms.
              - Cấu hình nén Brotli và bật Cache-Control cho tài nguyên tĩnh để tiết kiệm chi phí băng thông R2.
            """)

    with d2:
        with st.container(border=True):
            st.markdown("#### 📱 2. Thiết Kế & UI/UX")
            st.markdown(f"""
            - **Thực trạng:** Mobile chiếm **{mobile_pct:.1f}%**, Desktop chiếm **{desktop_pct:.1f}%**.
            - **Đề xuất hành động:**
              - **{'Áp dụng triết lý Mobile-First' if mobile_pct >= 50 else 'Tối ưu cân bằng trải nghiệm giữa Desktop và Mobile'}**.
              - Đảm bảo kích thước phím bấm di động chuẩn (tối thiểu 48px) và kiểm thử giao diện kỹ trên Safari iOS và Chrome Android.
            """)

    with d3:
        with st.container(border=True):
            st.markdown("#### 🎯 3. Quản Trị & Khách Hàng")
            st.markdown(f"""
            - **Thực trạng:** ID có tương tác nhiều nhất là **`{top_group_id}`** ({top_group_views:,} lượt).
            - **Đề xuất hành động:**
              - Đưa các nhóm/ID có lưu lượng cao vào danh sách chăm sóc đặc biệt (Tier 1).
              - Thiết lập ngưỡng cảnh báo khi phát hiện ID có lưu lượng tăng đột biến (>300 lượt/phút) để ngăn chặn hành vi spam hoặc cào dữ liệu trái phép.
            """)
