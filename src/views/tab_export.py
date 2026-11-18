import io
import os
import re
import zipfile
from datetime import datetime
import streamlit as st


def render_tab_export(df_filtered):
    """Tab 4: Trung tâm xuất file đa năng (Toàn bộ CSV, Từng ID, Gói nén ZIP) và xem trước bảng dữ liệu."""
    st.markdown("<h5 class='no-select'>📥 Trung Tâm Xuất Dữ Liệu</h5>", unsafe_allow_html=True)
    st.caption("Lựa chọn phương thức xuất dữ liệu phù hợp với nhu cầu phân tích và báo cáo.")

    exp_c1, exp_c2, exp_c3 = st.columns(3)
    
    # CỘT 1: XUẤT TOÀN BỘ CSV
    with exp_c1:
        with st.container(border=True):
            st.markdown("###### 📄 Xuất Toàn Bộ Đang Lọc")
            st.caption(f"Tải về toàn bộ **{len(df_filtered):,}** dòng dữ liệu chuẩn CSV.")
            
            csv_all_data = df_filtered[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                "id_clean": "Mã Nhóm / ID",
                "country_clean": "Quốc Gia",
                "device_clean": "Thiết Bị",
                "datetime": "Thời Gian Truy Cập",
                "ip": "Địa Chỉ IP"
            }).to_csv(index=False).encode("utf-8-sig")
            
            st.download_button(
                label=f"📥 Tải toàn bộ CSV ({len(df_filtered):,})",
                data=csv_all_data,
                file_name=f"basin_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # CỘT 2: XUẤT THEO TỪNG ID
    with exp_c2:
        with st.container(border=True):
            st.markdown("###### 🎯 Xuất Riêng Theo Từng ID")
            st.caption("Chọn 1 ID để xuất file CSV dữ liệu riêng biệt.")
            
            distinct_ids_tab3 = df_filtered["id_clean"].value_counts().index.tolist()
            default_tab3_idx = 0
            for i_idx, i_val in enumerate(distinct_ids_tab3):
                if i_val.lower() == "raumaxao":
                    default_tab3_idx = i_idx
                    break
                    
            selected_id_to_export = st.selectbox(
                "ID cần xuất:",
                options=distinct_ids_tab3,
                index=default_tab3_idx if distinct_ids_tab3 else 0,
                key="tab3_export_id_select"
            )
            
            if selected_id_to_export:
                sub_id_df = df_filtered[df_filtered["id_clean"] == selected_id_to_export][["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                    "id_clean": "Mã Nhóm / ID",
                    "country_clean": "Quốc Gia",
                    "device_clean": "Thiết Bị",
                    "datetime": "Thời Gian Truy Cập",
                    "ip": "Địa Chỉ IP"
                })
                csv_single_id = sub_id_df.to_csv(index=False).encode("utf-8-sig")
                clean_filename_id = re.sub(r'[^\w\-_.]', '_', selected_id_to_export)
                st.download_button(
                    label=f"📥 Tải CSV ID '{selected_id_to_export}'",
                    data=csv_single_id,
                    file_name=f"id_{clean_filename_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # CỘT 3: XUẤT GÓI NÉN ZIP
    with exp_c3:
        with st.container(border=True):
            st.markdown("###### 📦 Xuất Gói Nén ZIP")
            st.caption(f"Tách {df_filtered['id_clean'].nunique()} ID thành các file CSV độc lập.")
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for grp_name, grp_df in df_filtered.groupby("id_clean"):
                    safe_grp_name = re.sub(r'[^\w\-_.]', '_', str(grp_name))
                    grp_csv = grp_df[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
                        "id_clean": "Mã Nhóm / ID",
                        "country_clean": "Quốc Gia",
                        "device_clean": "Thiết Bị",
                        "datetime": "Thời Gian Truy Cập",
                        "ip": "Địa Chỉ IP"
                    }).to_csv(index=False).encode("utf-8-sig")
                    zip_file.writestr(f"id_{safe_grp_name}.csv", grp_csv)
            
            zip_buffer.seek(0)
            st.download_button(
                label=f"📦 Tải ZIP ({df_filtered['id_clean'].nunique()} file)",
                data=zip_buffer.getvalue(),
                file_name=f"basin_all_ids_separated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown(f"**Xem trước dữ liệu ({min(len(df_filtered), 500):,} / {len(df_filtered):,} bản ghi mới nhất):**")
    export_view = df_filtered[["id_clean", "country_clean", "device_clean", "datetime", "ip"]].rename(columns={
        "id_clean": "Mã Nhóm / ID",
        "country_clean": "Quốc Gia",
        "device_clean": "Thiết Bị",
        "datetime": "Thời Gian Truy Cập",
        "ip": "Địa Chỉ IP"
    }).sort_values(by="Thời Gian Truy Cập", ascending=False)
    
    st.dataframe(export_view.head(500), use_container_width=True, hide_index=True)
