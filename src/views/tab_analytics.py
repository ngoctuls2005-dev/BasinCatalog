import pandas as pd
import plotly.express as px
import streamlit as st
from src.analytics import (
    detect_traffic_anomalies,
    detect_suspicious_ips,
    calculate_visitor_retention,
    analyze_ip_subnets,
)
from src.config import COLOR_PALETTE
from src.styles import get_plot_layout_config


def render_tab_analytics(df_filtered, df_all):
    """Tab 3: Bộ công cụ phân tích dữ liệu chuyên nghiệp (Phát hiện bất thường, Khách quay lại, Subnet, So sánh A/B)."""
    plot_layout = get_plot_layout_config()

    st.markdown("<h5 class='no-select'>🔬 Bộ Công Cụ Phân Tích Chuyên Sâu (Analytics Pro)</h5>", unsafe_allow_html=True)
    st.caption("Ứng dụng các giải thuật thống kê, phát hiện bất thường và phân loại hành vi người dùng.")

    # PHẦN 1: PHÁT HIỆN ĐỘT BIẾN LƯU LƯỢNG & IP BẤT THƯỜNG
    st.markdown("<h6 class='no-select' style='margin-top: 10px;'>⚡ 1. Phát Hiện Bất Thường (Anomaly & Bot Detection)</h6>", unsafe_allow_html=True)
    col_anom1, col_anom2 = st.columns(2)

    with col_anom1:
        with st.container(border=True):
            st.markdown("**Đột biến lưu lượng theo giờ (Z-score > 2.0)**")
            anomalies = detect_traffic_anomalies(df_filtered, freq="1h")
            if anomalies.empty:
                st.success("✅ Không phát hiện khung giờ nào có lưu lượng tăng đột biến bất thường.")
            else:
                st.warning(f"⚠️ Phát hiện **{len(anomalies)}** mốc thời gian có lưu lượng tăng vọt bất thường!")
                st.dataframe(
                    anomalies[["datetime", "count", "z_score", "severity"]].rename(columns={
                        "datetime": "Mốc thời gian",
                        "count": "Số lượt xem",
                        "z_score": "Độ lệch Z-score",
                        "severity": "Mức độ cảnh báo"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

    with col_anom2:
        with st.container(border=True):
            st.markdown("**Địa chỉ IP có dấu hiệu cào dữ liệu / Spam**")
            suspicious = detect_suspicious_ips(df_filtered)
            if suspicious.empty:
                st.success("✅ Không phát hiện địa chỉ IP nào có tần suất gửi request đáng ngờ.")
            else:
                st.warning(f"⚠️ Phát hiện **{len(suspicious)}** địa chỉ IP cần lưu tâm giám sát:")
                st.dataframe(
                    suspicious[["ip", "requests", "share_pct", "unique_ids", "risk_eval"]].rename(columns={
                        "ip": "Địa chỉ IP",
                        "requests": "Lượt gửi",
                        "share_pct": "Tỷ trọng (%)",
                        "unique_ids": "Số ID truy cập",
                        "risk_eval": "Dấu hiệu nghi vấn"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

    st.markdown("---")

    # PHẦN 2: LÒNG TRUNG THÀNH KHÁCH HÀNG & DẢI MẠNG SUB-NET
    st.markdown("<h6 class='no-select'>📊 2. Phân Khúc Khách Hàng & Dải Mạng IP</h6>", unsafe_allow_html=True)
    col_ret1, col_ret2 = st.columns(2)

    with col_ret1:
        with st.container(border=True):
            st.markdown("**Phân khúc người dùng theo tần suất tương tác**")
            retention_df = calculate_visitor_retention(df_filtered)
            if not retention_df.empty:
                fig_ret = px.pie(
                    retention_df,
                    names="Phân khúc khách truy cập",
                    values="Số lượng IP",
                    hole=0.45,
                    color_discrete_sequence=COLOR_PALETTE
                )
                fig_ret.update_traces(textinfo="percent+label")
                fig_ret.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans, sans-serif"),
                )
                st.plotly_chart(fig_ret, use_container_width=True)

    with col_ret2:
        with st.container(border=True):
            st.markdown("**Top dải mạng (Subnet /24) có lượt xem lớn nhất**")
            subnets_df, ip_summary = analyze_ip_subnets(df_filtered)
            st.caption(f"Tỷ lệ hạ tầng: **IPv4: {ip_summary['ipv4_pct']:.1f}%** ({ip_summary['ipv4']:,} reqs) | **IPv6: {ip_summary['ipv6_pct']:.1f}%** ({ip_summary['ipv6']:,} reqs)")
            if not subnets_df.empty:
                fig_sub = px.bar(
                    subnets_df.head(6),
                    x="Lượt truy cập",
                    y="Dải mạng (Subnet)",
                    orientation="h",
                    text="Lượt truy cập",
                    color_discrete_sequence=["#0284c7"],
                )
                fig_sub.update_traces(textposition="outside")
                fig_sub.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    **plot_layout
                )
                st.plotly_chart(fig_sub, use_container_width=True)

    st.markdown("---")

    # PHẦN 3: BÀN SO SÁNH ĐỐI KHÁNG A/B GIỮA 2 ID
    st.markdown("<h6 class='no-select'>⚖️ 3. Bàn So Sánh Đối Kháng A/B Giữa 2 ID</h6>", unsafe_allow_html=True)
    with st.container(border=True):
        all_ids_list = df_all["id_clean"].value_counts().index.tolist()
        if len(all_ids_list) >= 2:
            col_cmp_sel1, col_cmp_sel2 = st.columns(2)
            with col_cmp_sel1:
                id_a = st.selectbox("Chọn ID Nhóm A:", options=all_ids_list, index=0, key="cmp_id_a")
            with col_cmp_sel2:
                id_b = st.selectbox("Chọn ID Nhóm B:", options=all_ids_list, index=1 if len(all_ids_list) > 1 else 0, key="cmp_id_b")

            if id_a and id_b and id_a != id_b:
                df_a = df_all[df_all["id_clean"] == id_a]
                df_b = df_all[df_all["id_clean"] == id_b]

                ca1, ca2, ca3, ca4 = st.columns(4)
                with ca1:
                    diff_views = len(df_a) - len(df_b)
                    st.metric(f"LƯỢT XEM: {id_a}", f"{len(df_a):,}", f"{diff_views:+d} so với B")
                with ca2:
                    st.metric(f"LƯỢT XEM: {id_b}", f"{len(df_b):,}")
                with ca3:
                    st.metric(f"SỐ IP: {id_a}", f"{df_a['ip'].nunique()}")
                with ca4:
                    st.metric(f"SỐ IP: {id_b}", f"{df_b['ip'].nunique()}")

                # So sánh thiết bị giữa 2 nhóm
                col_bar_a, col_bar_b = st.columns(2)
                with col_bar_a:
                    st.caption(f"Cơ cấu thiết bị của **{id_a}**")
                    dev_a = df_a["device_clean"].value_counts().reset_index()
                    dev_a.columns = ["Thiết bị", "Lượt"]
                    fig_a = px.bar(dev_a, x="Thiết bị", y="Lượt", color_discrete_sequence=["#0284c7"])
                    fig_a.update_layout(margin=dict(l=5, r=5, t=10, b=10), **plot_layout)
                    st.plotly_chart(fig_a, use_container_width=True)

                with col_bar_b:
                    st.caption(f"Cơ cấu thiết bị của **{id_b}**")
                    dev_b = df_b["device_clean"].value_counts().reset_index()
                    dev_b.columns = ["Thiết bị", "Lượt"]
                    fig_b = px.bar(dev_b, x="Thiết bị", y="Lượt", color_discrete_sequence=["#818cf8"])
                    fig_b.update_layout(margin=dict(l=5, r=5, t=10, b=10), **plot_layout)
                    st.plotly_chart(fig_b, use_container_width=True)
            elif id_a == id_b:
                st.info("💡 Vui lòng chọn 2 ID khác nhau để bắt đầu so sánh đối kháng.")
