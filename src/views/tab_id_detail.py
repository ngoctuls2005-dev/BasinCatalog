import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COLOR_PALETTE
from src.styles import get_plot_layout_config


def render_tab_id_detail(df_filtered, df_all, total_views, time_preset):
    """Tab 2: Khảo sát chuyên sâu theo ID với đầy đủ 5 biểu đồ (Timeline, Khung giờ, Quốc gia, Thiết bị, IP)."""
    plot_layout = get_plot_layout_config()

    st.markdown("<h5 class='no-select'>🎯 Khảo Sát Chi Tiết Từng ID / Mã Nhóm</h5>", unsafe_allow_html=True)
    st.caption("Xem hệ thống chỉ số và biểu đồ phân tích chuyên biệt riêng cho từng ID được chọn.")

    id_counts_map = df_all["id_clean"].value_counts()
    id_display_options = [f"{uid} ({cnt:,} lượt)" for uid, cnt in id_counts_map.items()]

    default_id_idx = 0
    for idx, opt in enumerate(id_display_options):
        if opt.lower().startswith("raumaxao"):
            default_id_idx = idx
            break

    col_id_sel, col_id_dl = st.columns([3, 1])
    with col_id_sel:
        chosen_display = st.selectbox(
            "📌 Chọn ID muốn xem chi tiết:",
            options=id_display_options,
            index=default_id_idx if id_display_options else 0
        )

    target_id = chosen_display.rsplit(" (", 1)[0] if chosen_display else None

    if not target_id:
        return

    # Lấy dữ liệu của ID được chọn
    id_df = df_filtered[df_filtered["id_clean"] == target_id].copy()
    is_showing_all_history = False
    
    if id_df.empty:
        id_df = df_all[df_all["id_clean"] == target_id].copy()
        is_showing_all_history = True

    id_total_views = len(id_df)
    id_share_pct = (id_total_views / total_views * 100) if total_views > 0 else 0
    id_ips_count = id_df["ip"].dropna().nunique()
    id_top_dev = id_df["device_clean"].mode()[0] if not id_df.empty else "N/A"
    id_top_country = id_df["country_clean"].mode()[0] if not id_df.empty else "N/A"
    last_seen = id_df["datetime"].max().strftime("%d/%m/%Y %H:%M") if not id_df.empty else "N/A"

    with col_id_dl:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        id_csv = id_df[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].to_csv(index=False).encode("utf-8-sig")
        clean_filename_id = re.sub(r'[^\w\-_.]', '_', target_id)
        st.download_button(
            label=f"📥 Tải CSV ID '{target_id}'",
            data=id_csv,
            file_name=f"id_{clean_filename_id}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    if is_showing_all_history:
        st.info(f"ℹ️ ID **`{target_id}`** không có lượt truy cập mới trong 24 giờ qua. Hệ thống đang tự động hiển thị **toàn bộ {id_total_views:,} lượt truy cập trong lịch sử** của ID này.")

    # 4 Thẻ KPI riêng của ID
    pi1, pi2, pi3, pi4 = st.columns(4)
    with pi1:
        with st.container(border=True):
            st.metric(f"LƯỢT XEM CỦA '{target_id}'", f"{id_total_views:,}", f"{id_share_pct:.1f}% toàn kho")
    with pi2:
        with st.container(border=True):
            st.metric("ĐỊA CHỈ IP ĐÃ DÙNG", f"{id_ips_count:,}", "IPs độc lập")
    with pi3:
        with st.container(border=True):
            st.metric("THIẾT BỊ HAY DÙNG", f"{id_top_dev.upper()}", f"Quốc gia: {id_top_country}")
    with pi4:
        with st.container(border=True):
            st.metric("HOẠT ĐỘNG GẦN NHẤT", f"{last_seen.split(' ')[1]}", f"Ngày: {last_seen.split(' ')[0]}")

    # Hàng 1: Diễn biến thời gian + Khung giờ online
    r1_c1, r1_c2 = st.columns([1.6, 1.2])
    with r1_c1:
        with st.container(border=True):
            st.markdown(f"<h5 class='no-select'>📈 Lịch Sử Truy Cập Của `{target_id}`</h5>", unsafe_allow_html=True)
            time_diff = (id_df["datetime"].max() - id_df["datetime"].min()).total_seconds()
            slot_freq = "h" if time_diff <= 86400 * 3 else "D"
            id_df["slot"] = id_df["datetime"].dt.floor(slot_freq)
            id_timeline = id_df.groupby(["slot", "device_clean"]).size().reset_index(name="Lượt truy cập")

            fig_id_timeline = px.line(
                id_timeline,
                x="slot",
                y="Lượt truy cập",
                color="device_clean",
                markers=True,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig_id_timeline.update_layout(
                hovermode="x unified",
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                **plot_layout
            )
            st.plotly_chart(fig_id_timeline, use_container_width=True)

    with r1_c2:
        with st.container(border=True):
            st.markdown(f"<h5 class='no-select'>⏰ Khung Giờ Hoạt Động (0h - 23h)</h5>", unsafe_allow_html=True)
            id_df["hour_of_day"] = id_df["datetime"].dt.hour
            hourly_hist = id_df.groupby("hour_of_day").size().reindex(range(24), fill_value=0).reset_index()
            hourly_hist.columns = ["Giờ", "Số lượt"]
            hourly_hist["Nhãn"] = hourly_hist["Giờ"].apply(lambda h: f"{h:02d}:00")

            fig_hourly = px.bar(
                hourly_hist,
                x="Nhãn",
                y="Số lượt",
                color_discrete_sequence=["#818cf8"],
            )
            fig_hourly.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                **plot_layout
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

    # Hàng 2: Ba cột phân bổ - Quốc gia, Thiết bị & Địa chỉ IP
    r2_c1, r2_c2, r2_c3 = st.columns(3)

    with r2_c1:
        with st.container(border=True):
            st.markdown(f"<h5 class='no-select'>🌍 Phân Bố Quốc Gia Của `{target_id}`</h5>", unsafe_allow_html=True)
            c_cnt = id_df["country_clean"].value_counts()
            id_country_df = pd.DataFrame({
                "Quốc gia": c_cnt.index.tolist(),
                "Lượt xem": c_cnt.values.tolist()
            })

            fig_id_country = px.bar(
                id_country_df,
                x="Quốc gia",
                y="Lượt xem",
                text="Lượt xem",
                color_discrete_sequence=["#34d399"],
            )
            fig_id_country.update_traces(textposition="outside")
            fig_id_country.update_layout(
                margin=dict(l=10, r=10, t=25, b=10),
                **plot_layout
            )
            st.plotly_chart(fig_id_country, use_container_width=True)

    with r2_c2:
        with st.container(border=True):
            st.markdown(f"<h5 class='no-select'>📱 Cơ Cấu Thiết Bị Của `{target_id}`</h5>", unsafe_allow_html=True)
            d_cnt = id_df["device_clean"].value_counts()
            id_dev_df = pd.DataFrame({
                "Thiết bị": d_cnt.index.tolist(),
                "Lượt xem": d_cnt.values.tolist()
            })
            
            fig_id_dev = px.pie(
                id_dev_df,
                names="Thiết bị",
                values="Lượt xem",
                hole=0.48,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig_id_dev.update_traces(textinfo="percent+label")
            fig_id_dev.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif"),
            )
            st.plotly_chart(fig_id_dev, use_container_width=True)

    with r2_c3:
        with st.container(border=True):
            st.markdown(f"<h5 class='no-select'>🌐 Top Địa Chỉ IP Của `{target_id}`</h5>", unsafe_allow_html=True)
            ip_cnt = id_df["ip"].value_counts().head(8)
            id_ip_counts = pd.DataFrame({
                "Địa chỉ IP": ip_cnt.index.tolist(),
                "Lượt xem": ip_cnt.values.tolist()
            })
            
            fig_id_ip = px.bar(
                id_ip_counts.sort_values(by="Lượt xem", ascending=True),
                x="Lượt xem",
                y="Địa chỉ IP",
                orientation="h",
                text="Lượt xem",
                color_discrete_sequence=["#0284c7"],
            )
            fig_id_ip.update_traces(textposition="outside")
            fig_id_ip.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                **plot_layout
            )
            st.plotly_chart(fig_id_ip, use_container_width=True)

    # Bảng chi tiết các lần truy cập
    with st.expander(f"📋 Xem danh sách chi tiết các lần truy cập của '{target_id}'"):
        st.dataframe(
            id_df[["datetime", "ip", "device_clean", "country_clean"]]
            .rename(columns={"datetime": "Thời gian", "ip": "Địa chỉ IP", "device_clean": "Thiết bị", "country_clean": "Quốc gia"})
            .sort_values(by="Thời gian", ascending=False),
            use_container_width=True,
            hide_index=True
        )
