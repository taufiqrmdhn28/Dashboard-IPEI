import streamlit as st
import pandas as pd
import plotly.express as px
import json

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Indeks Pembangunan Ekonomi Inklusif (IPEI)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. FUNGSI PEMUATAN DATA (PERBAIKAN EKSTRAKSI GEOMETRI JSON)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1. Load data Excel KHUSUS dari sheet "Kab_Kota"
    df = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Kab_Kota")

    # 2. Bersihkan kode daerah di Excel
    df['kodedaerah'] = df['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    # 3. Paksa kolom indikator menjadi numerik
    kolom_indikator = ['ipei', 'pilar1', 'pilar2', 'pilar3', 'sp11', 'sp12', 'sp13', 'sp21', 'sp22', 'sp31', 'sp32', 'sp33']
    for col in kolom_indikator:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 4. Load file Peta BPS
    with open("Peta_BPS_Kabupaten.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 5. Transformasi format
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for item in raw_data:
        geom_raw = item.get('coordinates')
        if not geom_raw:
            continue
            
        # --- BAGIAN PERBAIKAN UTAMA: EKSTRAKSI GEOMETRI ASLI ---
        try:
            # Tahap 1: Ubah string JSON terluar menjadi dictionary
            geom_dict = json.loads(geom_raw)
            
            # Tahap 2: Gali ke dalam 'features' untuk mengambil 'geometry'
            if 'features' in geom_dict and len(geom_dict['features']) > 0:
                geom_str = geom_dict['features'][0].get('geometry')
                
                # Tahap 3: Ubah lagi string di dalamnya menjadi dictionary geometri asli
                actual_geom = json.loads(geom_str)
            else:
                continue
        except Exception:
            # Abaikan baris ini jika struktur koordinatnya rusak
            continue
        # --------------------------------------------------------

        # Gunakan 'code' untuk level Kabupaten/Kota
        kode = str(item.get('code', '')).replace('.0', '').strip()

        if kode and kode.lower() != 'none':
            feature = {
                "type": "Feature",
                "id": kode,
                "properties": item,  
                "geometry": actual_geom  # Masukkan geometri yang sudah bersih dan valid
            }
            geojson['features'].append(feature)

    return df, geojson

# ---> PASTIKAN BARIS INI TETAP ADA (Jangan sampai terhapus atau menjorok ke dalam) <---
df, geojson = load_data()
# -----------------------------------------------------------------------------
# 3. STRUKTUR MENU (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.title("Navigasi Dashboard")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    ("🏠 Halaman Utama (Peta IPEI)", "📈 Analisis Pilar & Tren", "ℹ️ Tentang IPEI")
)

# -----------------------------------------------------------------------------
# 4. KONTEN HALAMAN
# -----------------------------------------------------------------------------

if menu == "🏠 Halaman Utama (Peta IPEI)":
    st.title("Peta Indeks Pembangunan Ekonomi Inklusif (IPEI)")
    st.markdown("Pemetaan skor tingkat Kabupaten/Kota untuk evaluasi pembangunan makroekonomi wilayah.")
    
    col1, col2 = st.columns(2)
    with col1:
        tahun_tersedia = [2025, 2024]
        selected_year = st.selectbox("📅 Pilih Tahun:", tahun_tersedia)
        
    with col2:
        indikator_dict = {
            "Skor Total IPEI": "ipei",
            "Pilar 1: Pertumbuhan dan Perkembangan Ekonomi": "pilar1",
            "Pilar 2: Kesetaraan dan Inklusi": "pilar2",
            "Pilar 3: Kemiskinan dan Kondisi Pekerjaan": "pilar3",
            "Sub-Pilar 1.1": "sp11", "Sub-Pilar 1.2": "sp12", "Sub-Pilar 1.3": "sp13",
            "Sub-Pilar 2.1": "sp21", "Sub-Pilar 2.2": "sp22",
            "Sub-Pilar 3.1": "sp31", "Sub-Pilar 3.2": "sp32", "Sub-Pilar 3.3": "sp33"
        }
        selected_label = st.selectbox("🎯 Pilih Indikator yang Dipetakan:", list(indikator_dict.keys()))
        selected_kolom = indikator_dict[selected_label]
    
    df_filtered = df[df['tahun'].astype(int) == selected_year].reset_index(drop=True)
    
    if df_filtered.empty:
        st.warning(f"⚠️ Data untuk tahun {selected_year} tidak ditemukan di file Excel.")
    else:
        # PETA SUDAH MENGGUNAKAN ID INJEKSI (Parameter featureidkey dihilangkan)
        fig_map = px.choropleth_map(
            df_filtered,
            geojson=geojson,
            locations='kodedaerah',            
            color=selected_kolom,              
            color_continuous_scale="RdYlGn",  
            map_style="carto-positron",        
            zoom=4,
            center={"lat": -0.789, "lon": 113.921}, 
            opacity=0.8,
            hover_name='namadaerah',
            hover_data={
                'kodedaerah': False, 
                'ipei': True, 
                'pilar1': True, 
                'pilar2': True, 
                'pilar3': True
            },
            labels={selected_kolom: selected_label}
        )
        
        fig_map.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            coloraxis_colorbar=dict(
                title="Nilai",
                thicknessmode="pixels", thickness=15,
                lenmode="pixels", len=300,
                yanchor="top", y=1,
                ticks="outside"
            )
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        st.info(f"Visualisasi menampilkan sebaran **{selected_label}** untuk tahun **{selected_year}**.")
        
        # --- FITUR DEBUGGING (CEK KECOCOKAN DATA) ---
        with st.expander("🛠️ Cek Sinkronisasi Data (Jika Peta Masih Polos)"):
            sampel_excel = df_filtered['kodedaerah'].head(5).tolist()
            sampel_json = [f['id'] for f in geojson['features'][:5]]
            st.write(f"**Contoh Kode di Excel:** {sampel_excel}")
            st.write(f"**Contoh Kode di JSON:** {sampel_json}")
            st.caption("Pastikan format kedua kode di atas sama persis (contoh: sama-sama '1101'). Jika beda, peta tidak akan berwarna.")

elif menu == "📈 Analisis Pilar & Tren":
    st.title("Analisis Tren dan Pilar Ekonomi Inklusif")
    st.markdown("Tinjauan deret waktu (*time-series*) dan dekomposisi pilar penyusun IPEI.")
    
    col1, col2 = st.columns(2)
    with col1:
        daerah_list = df['namadaerah'].dropna().unique().tolist()
        daerah_list.sort()
        selected_daerah = st.selectbox("Pilih Kabupaten/Kota:", daerah_list)
    
    df_daerah = df[df['namadaerah'] == selected_daerah].sort_values('tahun')
    
    if not df_daerah.empty:
        st.subheader(f"Tren IPEI - {selected_daerah}")
        fig_trend = px.line(
            df_daerah, 
            x='tahun', 
            y='ipei', 
            markers=True,
            title="Perkembangan Skor IPEI"
        )
        fig_trend.update_xaxes(dtick=1) 
        st.plotly_chart(fig_trend, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("Komposisi Pilar (Tahun Terakhir)")
        tahun_terakhir = df_daerah['tahun'].max()
        df_pilar = df_daerah[df_daerah['tahun'] == tahun_terakhir]
        
        if not df_pilar.empty:
            pilar_data = {
                'Pilar': ['Pilar 1', 'Pilar 2', 'Pilar 3'],
                'Skor': [df_pilar['pilar1'].values[0], df_pilar['pilar2'].values[0], df_pilar['pilar3'].values[0]]
            }
            df_chart_pilar = pd.DataFrame(pilar_data)
            
            fig_bar = px.bar(
                df_chart_pilar, 
                x='Pilar', 
                y='Skor', 
                color='Pilar',
                title=f"Skor per Pilar untuk {selected_daerah} (Tahun {tahun_terakhir})"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Data untuk daerah yang dipilih tidak tersedia.")

elif menu == "ℹ️ Tentang IPEI":
    st.title("Tentang Indeks Pembangunan Ekonomi Inklusif")
    
    st.markdown("""
    **Indeks Pembangunan Ekonomi Inklusif (IPEI)** adalah instrumen pengukuran untuk melihat seberapa inklusif pertumbuhan ekonomi di suatu wilayah.
    
    ### Komponen Utama:
    * **Pilar 1:** Pertumbuhan dan Perkembangan Ekonomi
    * **Pilar 2:** Kesetaraan dan Inklusi
    * **Pilar 3:** Kemiskinan dan Kondisi Pekerjaan
    """)
