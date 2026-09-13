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

# Kamus Nama Provinsi BPS untuk mempercantik Dropdown
PROVINSI_MAP = {
    "1100": "Aceh", "1200": "Sumatera Utara", "1300": "Sumatera Barat", "1400": "Riau", "1500": "Jambi",
    "1600": "Sumatera Selatan", "1700": "Bengkulu", "1800": "Lampung", "1900": "Kep. Bangka Belitung", "2100": "Kep. Riau",
    "3100": "DKI Jakarta", "3200": "Jawa Barat", "3300": "Jawa Tengah", "3400": "DI Yogyakarta", "3500": "Jawa Timur", "3600": "Banten",
    "5100": "Bali", "5200": "Nusa Tenggara Barat", "5300": "Nusa Tenggara Timur",
    "6100": "Kalimantan Barat", "6200": "Kalimantan Tengah", "6300": "Kalimantan Selatan", "6400": "Kalimantan Timur", "6500": "Kalimantan Utara",
    "7100": "Sulawesi Utara", "7200": "Sulawesi Tengah", "7300": "Sulawesi Selatan", "7400": "Sulawesi Tenggara", "7500": "Gorontalo", "7600": "Sulawesi Barat",
    "8100": "Maluku", "8200": "Maluku Utara", "9100": "Papua Barat", "9400": "Papua"
}

# -----------------------------------------------------------------------------
# 2. FUNGSI PEMUATAN DATA
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1. Load data Excel KHUSUS dari sheet "Kab_Kota"
    df = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Kab_Kota")

    # 2. Bersihkan kode daerah di Excel
    df['kodedaerah'] = df['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    # [BARU] 2b. Buat kolom identitas provinsi induk (2 digit awal + "00")
    df['kode_provinsi_induk'] = df['kodedaerah'].str[:2] + "00"
    df['nama_provinsi'] = df['kode_provinsi_induk'].map(PROVINSI_MAP).fillna(df['kode_provinsi_induk'])

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
            
        # Ekstraksi Geometri Asli
        try:
            geom_dict = json.loads(geom_raw)
            if 'features' in geom_dict and len(geom_dict['features']) > 0:
                geom_str = geom_dict['features'][0].get('geometry')
                actual_geom = json.loads(geom_str)
            else:
                continue
        except Exception:
            continue

        kode = str(item.get('code', '')).replace('.0', '').strip()

        if kode and kode.lower() != 'none':
            feature = {
                "type": "Feature",
                "id": kode,
                "properties": item,  
                "geometry": actual_geom  
            }
            geojson['features'].append(feature)

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
    st.markdown("Pemetaan skor tingkat wilayah untuk evaluasi pembangunan makroekonomi.")

    # --- INISIALISASI SESSION STATE UNTUK KLIK PETA ---
    if "tingkat_peta" not in st.session_state:
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    def reset_peta():
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    # --- FILTER TAHUN DAN INDIKATOR ---
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


    # =========================================================
    # LOGIKA 1: TAMPILAN AWAL (PETA NASIONAL DENGAN BATAS PROVINSI)
    # =========================================================
    if st.session_state.tingkat_peta == "nasional":
        st.info("💡 **Petunjuk:** Klik pada salah satu area Provinsi di peta untuk melihat detail Kabupaten/Kota di dalamnya.")
        
        # Filter data provinsi (Pastikan kamu sudah membuat df_provinsi di load_data)
        df_prov_filtered = df_provinsi[df_provinsi['tahun'].astype(int) == selected_year].reset_index(drop=True)

        if not df_prov_filtered.empty:
            fig_nasional = px.choropleth_map(
                df_prov_filtered,
                geojson=geojson_provinsi, # Pastikan variabel ini memuat JSON Provinsi
                locations='kodedaerah',            
                color=selected_kolom,              
                color_continuous_scale="RdYlGn",  
                map_style="carto-positron",        
                zoom=4,
                center={"lat": -0.789, "lon": 113.921}, 
                opacity=0.8,
                hover_name='namadaerah',
                labels={selected_kolom: selected_label}
            )

            fig_nasional.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

            # Tampilkan peta dan tangkap event klik dengan on_select="rerun"
            event = st.plotly_chart(fig_nasional, use_container_width=True, on_select="rerun", selection_mode="points", key="peta_awal")
            
            # Jika ada provinsi yang diklik, proses id-nya
            if event and event.get("selection") and event["selection"].get("points"):
                kode_prov_diklik = event["selection"]["points"][0]["location"]
                
                # Simpan ke session state dan muat ulang halaman
                st.session_state.provinsi_terpilih = kode_prov_diklik
                st.session_state.tingkat_peta = "provinsi"
                st.rerun()

    # =========================================================
    # LOGIKA 2: TAMPILAN ZOOM (PETA KABUPATEN DI DALAM 1 PROVINSI)
    # =========================================================
    elif st.session_state.tingkat_peta == "provinsi":
        st.button("⬅️ Kembali ke Peta Nasional", on_click=reset_peta)
        
        # Filter data kabupaten untuk tahun terpilih
        df_kab_filtered = df_kabkota[df_kabkota['tahun'].astype(int) == selected_year].copy()
        
        # Ekstrak 2 digit pertama dari kode kabupaten untuk mencocokkan dengan kode provinsi
        df_kab_filtered['kode_prov'] = df_kab_filtered['kodedaerah'].astype(str).str[:2] + "00"
        
        # Saring hanya kabupaten yang berada di provinsi yang diklik
        df_kab_zoom = df_kab_filtered[df_kab_filtered['kode_prov'] == str(st.session_state.provinsi_terpilih)].reset_index(drop=True)
        
        if not df_kab_zoom.empty:
            fig_zoom = px.choropleth_map(
                df_kab_zoom,
                geojson=geojson_kabkota, # Pastikan variabel ini memuat JSON Kabupaten
                locations='kodedaerah',            
                color=selected_kolom,              
                color_continuous_scale="RdYlGn",  
                map_style="carto-positron",        
                opacity=0.8,
                hover_name='namadaerah',
                labels={selected_kolom: selected_label}
            )

            # Fitur Auto-Zoom berdasarkan lokasi yang difilter
            fig_zoom.update_geos(fitbounds="locations", visible=False)
            fig_zoom.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

            st.plotly_chart(fig_zoom, use_container_width=True, key="peta_zoom")
        else:
            st.warning("Data Kabupaten/Kota untuk Provinsi ini belum tersedia.")

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
