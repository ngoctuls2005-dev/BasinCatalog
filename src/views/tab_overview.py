import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COLOR_PALETTE
from src.styles import get_plot_layout_config


def render_tab_overview(df_filtered):
    """Tab 1: Tổng quan hệ thống - Biểu đồ Timeline, Quốc gia, Thiết bị & Ma trận đối sánh."""
    plot_layout = get_plot_layout_config()

    # 1. Biểu đồ đường Timeline
    with st.container(border=True):
        st.markdown("<h5 class='no-select'>📈 Diễn Biến Lưu Lượng Truy Cập Theo Thời Gian</h5>", unsafe_allow_html=True)
        time_span_hours = (df_filtered["datetime"].max() - df_filtered["datetime"].min()).total_seconds() / 3600
        slot_rule = "h" if time_span_hours <= 48 else "D"
        
        df_filtered["time_slot"] = df_filtered["datetime"].dt.floor(slot_rule)
        timeline_df = df_filtered.groupby(["time_slot", "device_clean"]).size().reset_index(name="Lượt truy cập")
        
        fig_timeline = px.line(
            timeline_df,
            x="time_slot",
            y="Lượt truy cập",
            color="device_clean",
            markers=True,
            labels={"time_slot": "Mốc thời gian", "device_clean": "Thiết bị", "Lượt truy cập": "Lượt truy cập"},
            color_discrete_sequence=COLOR_PALETTE
        )
        fig_timeline.update_layout(
            hovermode="x unified",
            margin=dict(l=15, r=15, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            **plot_layout
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # 2. Hai cột: Quốc gia & Thiết bị
    c_left, c_right = st.columns(2)

    with c_left:
        with st.container(border=True):
            st.markdown("<h5 class='no-select'>🌍 Phân Bố Theo Quốc Gia (Top 8)</h5>", unsafe_allow_html=True)
            c_counts = df_filtered["country_clean"].value_counts()
            country_df = pd.DataFrame({
                "Quốc gia": c_counts.index.tolist(),
                "Lượt xem": c_counts.values.tolist()
            })
            
            fig_country = px.bar(
                country_df.head(8),
                x="Quốc gia",
                y="Lượt xem",
                text="Lượt xem",
                color_discrete_sequence=["#0284c7"],
            )
            fig_country.update_traces(textposition="outside")
            fig_country.update_layout(
                margin=dict(l=10, r=10, t=25, b=10),
                **plot_layout
            )
            st.plotly_chart(fig_country, use_container_width=True)

    with c_right:
        with st.container(border=True):
            st.markdown("<h5 class='no-select'>📱 Cơ Cấu Loại Thiết Bị</h5>", unsafe_allow_html=True)
            d_counts = df_filtered["device_clean"].value_counts()
            device_df = pd.DataFrame({
                "Thiết bị": d_counts.index.tolist(),
                "Lượt xem": d_counts.values.tolist()
            })
            
            fig_device = px.pie(
                device_df,
                names="Thiết bị",
                values="Lượt xem",
                hole=0.48,
                color_discrete_sequence=COLOR_PALETTE,
            )
            fig_device.update_traces(textinfo="percent+label")
            fig_device.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif"),
            )
            st.plotly_chart(fig_device, use_container_width=True)

    # 3. Ma trận đối sánh trong Expander gọn gàng
    with st.expander("🔍 Xem Bảng Ma Trận Đối Sánh: Quốc Gia x Loại Thiết Bị"):
        matrix_df = pd.crosstab(df_filtered["country_clean"], df_filtered["device_clean"], margins=True, margins_name="Tổng")
        st.dataframe(matrix_df, use_container_width=True)

    return country_df
