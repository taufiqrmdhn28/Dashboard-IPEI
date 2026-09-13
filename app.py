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
# 2. FUNGSI PEMUATAN DATA (CACHING)
# Menggunakan st.cache_data agar aplikasi tidak lambat saat memuat ulang
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Load data Excel
    df = pd.read_excel("Data_Dummy_IPEI.xlsx")
    
    # Pastikan kodedaerah menjadi teks (string) agar bisa dicocokkan dengan JSON
    df['kodedaerah'] = df['kodedaerah'].astype(str)
    
    # Load file GeoJSON
    with open("38_Provinsi_Indonesia_Kabupaten_Adjusted.json", "r", encoding="utf-8") as f:
        geojson = json.load(f)
        
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
    
    # 1. KONTROL FILTER (TAHUN & INDIKATOR)
    col1, col2 = st.columns(2)
    
    with col1:
        # Menampilkan HANYA tahun 2024 dan 2025 secara statis sesuai permintaan
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
    # Memastikan tipe data dicocokkan sebagai integer
    df_filtered = df[df['tahun'].astype(int) == selected_year]
    
    # Validasi apakah data untuk tahun tersebut tersedia
    if df_filtered.empty:
        st.warning(f"⚠️ Data untuk tahun {selected_year} tidak ditemukan di file Excel. Pastikan data sudah tersedia.")
    else:
        try:
            # 2. MEMBUAT PETA INTERAKTIF DENGAN PLOTLY
            fig_map = px.choropleth_mapbox(
                df_filtered,
                geojson=geojson,
                locations='kodedaerah',           
                featureidkey='properties.KODE',   # -> CEK CATATAN DI BAWAH JIKA MASIH ERROR
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
            
        except AttributeError:
            st.error("Terjadi AttributeError pada perenderan peta.")
            st.markdown("""
            **Tindakan Perbaikan:**
            1. Periksa file `38_Provinsi_Indonesia_Kabupaten_Adjusted.json` Anda (buka menggunakan Notepad/VS Code).
            2. Cari struktur `"properties": { ... }`.
            3. Pastikan atribut kode daerahnya benar-benar bernama `"KODE"`. Jika di JSON namanya adalah `"WADMKK"` atau `"KABKOT"`, maka ubah baris `featureidkey='properties.KODE'` di skrip `app.py` menjadi `featureidkey='properties.WADMKK'` (sesuaikan dengan nama aslinya).
            """)
        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")

elif menu == "📈 Analisis Pilar & Tren":
    st.title("Analisis Tren dan Pilar Ekonomi Inklusif")
    st.markdown("Tinjauan deret waktu (*time-series*) dan dekomposisi pilar penyusun IPEI.")
    
    # Layout kolom untuk filter
    col1, col2 = st.columns(2)
    with col1:
        daerah_list = df['namadaerah'].unique().tolist()
        selected_daerah = st.selectbox("Pilih Kabupaten/Kota:", daerah_list)
    
    # Filter data untuk daerah yang dipilih
    df_daerah = df[df['namadaerah'] == selected_daerah].sort_values('tahun')
    
    # Grafik Garis: Tren IPEI dari waktu ke waktu
    st.subheader(f"Tren IPEI - {selected_daerah}")
    fig_trend = px.line(
        df_daerah, 
        x='tahun', 
        y='ipei', 
        markers=True,
        title=f"Perkembangan Skor IPEI (2011 - Sekarang)"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    
    # Grafik Batang: Perbandingan Pilar (Tahun Terbaru)
    st.subheader("Komposisi Pilar (Tahun Terakhir)")
    tahun_terakhir = df_daerah['tahun'].max()
    df_pilar = df_daerah[df_daerah['tahun'] == tahun_terakhir]
    
    if not df_pilar.empty:
        # Menyiapkan data untuk grafik batang
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

elif menu == "ℹ️ Tentang IPEI":
    st.title("Tentang Indeks Pembangunan Ekonomi Inklusif")
    
    # Tempat untuk menaruh gambar logo jika ada
    # st.image("logo_bappenas.png", width=200)
    
    st.markdown("""
    **Indeks Pembangunan Ekonomi Inklusif (IPEI)** adalah instrumen pengukuran untuk melihat seberapa inklusif pertumbuhan ekonomi di suatu wilayah.
    
    ### Komponen Utama:
    * **Pilar 1:** Pertumbuhan dan Perkembangan Ekonomi
    * **Pilar 2:** Kesetaraan dan Inklusi
    * **Pilar 3:** Kemiskinan dan Kondisi Pekerjaan
    
    *Dashboard ini dirancang untuk memfasilitasi analisis kebijakan dan pemantauan dinamika makroekonomi wilayah secara efisien.*
    """)
