import streamlit as st
import pandas as pd
from collections import defaultdict
from io import BytesIO

def count_multiple_choices(df, columns_to_process):
    """Memproses kolom multiple choice dan return Excel dalam BytesIO"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for column in columns_to_process:
            counter = defaultdict(int)
            
            for responses in df[column]:
                if pd.notna(responses):
                    choices = [choice.strip().lower() for choice in str(responses).split(",")]
                    for choice in choices:
                        if choice:
                            counter[choice] += 1
            
            result_df = pd.DataFrame(
                list(counter.items()),
                columns=['Opsi', 'Jumlah']
            ).sort_values('Jumlah', ascending=False)
            
            sheet_name = column[:31]
            result_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output

def main():
    st.set_page_config(page_title="Fast Tabulasi", layout="wide")
    st.title("📊 Aplikasi Fast Tabulasi by Firstat")
    
    # Initialize session state
    if 'output_files' not in st.session_state:
        st.session_state.output_files = {}

    # Upload file
    uploaded_file = st.file_uploader("UPLOAD FILE EXCEL", type=["xlsx", "xls"])
    
    if not uploaded_file:
        st.info("Silahkan upload file Excel terlebih dahulu")
        return
    
    try:
        df = pd.read_excel(uploaded_file)
        st.success(f"File berhasil diupload! ({len(df)} baris)")
        st.write("Preview Data:", df.head(2))
    except Exception as e:
        st.error(f"Gagal membaca file: {str(e)}")
        return

    # Sidebar untuk pilih kolom
    st.sidebar.header("⚙️ Pengaturan Kolom")
    all_columns = df.columns.tolist()
    
    one_way_columns = st.sidebar.multiselect(
        "Variabel Satu Arah",
        all_columns,
        help="Pilih kolom untuk tabulasi frekuensi"
    )
    
    demographic_columns = st.sidebar.multiselect(
        "Variabel Demografi", 
        all_columns,
        help="Pilih kolom untuk analisis silang"
    )
    
    multiple_col = st.sidebar.multiselect(
        "Multiple Choice",
        all_columns,
        help="Pilih kolom dengan jawaban ganda (pisah dengan koma)"
    )

    # Tombol proses
    if st.button("🚀 PROSES DATA", type="primary", use_container_width=True):
        st.session_state.output_files = {}  # Reset output sebelumnya
        
        with st.spinner("Sedang memproses..."):
            try:
                # 1. Proses Satu Arah
                if one_way_columns:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for col in one_way_columns:
                            tabulasi = (
                                df[col]
                                .value_counts()
                                .reset_index()
                                .rename(columns={'index': col, col: 'Jumlah'})
                            )
                            tabulasi.to_excel(writer, sheet_name=col[:31], index=False)
                    output.seek(0)
                    st.session_state.output_files["satu_arah"] = {
                        "data": output.getvalue(),
                        "name": "output_satu_arah.xlsx"
                    }

                # 2. Proses Dua Arah
                if demographic_columns and one_way_columns:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for demo_col in demographic_columns:
                            for target_col in one_way_columns:
                                crosstab = pd.crosstab(
                                    index=df[demo_col],
                                    columns=df[target_col],
                                    margins=True,
                                    margins_name="Total"
                                )
                                sheet_name = f"{demo_col[:15]}_{target_col[:15]}"
                                crosstab.to_excel(writer, sheet_name=sheet_name[:31])
                    output.seek(0)
                    st.session_state.output_files["dua_arah"] = {
                        "data": output.getvalue(),
                        "name": "output_dua_arah.xlsx"
                    }

                # 3. Proses Multiple Choice
                if multiple_col:
                    processed_data = count_multiple_choices(df, multiple_col)
                    st.session_state.output_files["multi"] = {
                        "data": processed_data.getvalue(),
                        "name": "output_multiple_choice.xlsx"
                    }

                st.success("Proses selesai! Silahkan download file di bawah ↓")

            except Exception as e:
                st.error(f"Terjadi kesalahan: {str(e)}")

    # Tampilkan tombol download dari session state
    if st.session_state.output_files:
        st.divider()
        st.subheader("📥 Download Hasil")
        
        cols = st.columns(3)
        download_types = {
            "satu_arah": "Satu Arah",
            "dua_arah": "Dua Arah", 
            "multi": "Multiple Choice"
        }
        
        for i, (key, label) in enumerate(download_types.items()):
            if key in st.session_state.output_files:
                with cols[i]:
                    data = st.session_state.output_files[key]["data"]
                    file_name = st.session_state.output_files[key]["name"]
                    st.download_button(
                        label=f"**{label}**",
                        data=data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{key}",
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()
