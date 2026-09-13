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
# 2. FUNGSI PEMUATAN DATA (CACHING) DENGAN PEMBERSIH ERROR
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Load data Excel
    df = pd.read_excel("Data_Dummy_IPEI.xlsx")
    
    # 1. Pastikan kodedaerah bersih (tanpa spasi dan tanpa .0 di belakangnya)
    df['kodedaerah'] = df['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    # Pastikan kolom-kolom indikator terbaca sebagai angka (bukan teks) agar peta bisa merender warna
    kolom_indikator = ['ipei', 'pilar1', 'pilar2', 'pilar3', 'sp11', 'sp12', 'sp13', 'sp21', 'sp22', 'sp31', 'sp32', 'sp33']
    for col in kolom_indikator:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Load file GeoJSON
    with open("38_Provinsi_Indonesia_Kabupaten_Adjusted.json", "r", encoding="utf-8") as f:
        geojson = json.load(f)
        
    # 2. Sisir file JSON untuk mencegah AttributeError jika ada area yang properties-nya Null
    for feature in geojson.get('features', []):
        # Jika properties kosong/null, paksa menjadi dictionary kosong
        if 'properties' not in feature or feature['properties'] is None:
            feature['properties'] = {}
            
        # Ambil nilai kodedaerah, jika tidak ada, beri nama "UNKNOWN"
        val = feature['properties'].get('kodedaerah_kabkota', 'UNKNOWN')
        # Ubah jadi teks dan bersihkan
        feature['properties']['kodedaerah_kabkota'] = str(val).replace('.0', '').strip()
            
    return df, geojson

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
    
    # KONTROL FILTER (TAHUN & INDIKATOR)
    col1, col2 = st.columns(2)
    
    with col1:
        # Menampilkan HANYA tahun 2024 dan 2025
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
    
    # Filter data berdasarkan tahun yang dipilih
    df_filtered = df[df['tahun'].astype(int) == selected_year]
    
    # Validasi ketersediaan data
    if df_filtered.empty:
        st.warning(f"⚠️ Data untuk tahun {selected_year} tidak ditemukan di file Excel.")
    else:
        # MEMBUAT PETA INTERAKTIF
        fig_map = px.choropleth_mapbox(
            df_filtered,
            geojson=geojson,
            locations='kodedaerah',           
            featureidkey='properties.kodedaerah_kabkota',   
            color=selected_kolom,             
            color_continuous_scale="RdYlGn",  
            mapbox_style="carto-positron",
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
        
        # Tampilkan Peta
        st.plotly_chart(fig_map, use_container_width=True)
        st.info(f"Visualisasi menampilkan sebaran **{selected_label}** untuk tahun **{selected_year}**.")

elif menu == "📈 Analisis Pilar & Tren":
    st.title("Analisis Tren dan Pilar Ekonomi Inklusif")
    st.markdown("Tinjauan deret waktu (*time-series*) dan dekomposisi pilar penyusun IPEI.")
    
    col1, col2 = st.columns(2)
    with col1:
        # Hapus duplikat dan NaN dari daftar nama daerah
        daerah_list = df['namadaerah'].dropna().unique().tolist()
        daerah_list.sort()
        selected_daerah = st.selectbox("Pilih Kabupaten/Kota:", daerah_list)
    
    # Filter data untuk daerah yang dipilih
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
        # Paksa sumbu X agar menampilkan tahun tanpa koma (contoh: bukan 2,024 tapi 2024)
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
    
    *Dashboard ini dirancang untuk memfasilitasi analisis kebijakan dan pemantauan dinamika makroekonomi wilayah secara efisien.*
    """)
