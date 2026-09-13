import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd
import math

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Indeks Pembangunan Ekonomi Inklusif (IPEI)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. FUNGSI PEMUATAN DATA
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df_provinsi = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Provinsi")
    df_kabkota = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Kab_Kota")

    kolom_indikator = ['ipei', 'pilar1', 'pilar2', 'pilar3', 'sp11', 'sp12', 'sp13', 'sp21', 'sp22', 'sp31', 'sp32', 'sp33']
    for df_tmp in [df_provinsi, df_kabkota]:
        df_tmp['kodedaerah'] = df_tmp['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        for col in kolom_indikator:
            if col in df_tmp.columns:
                df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')

    with open("Peta_BPS_Kabupaten.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    fitur_kabkota = []
    for item in raw_data:
        geom_raw = item.get('coordinates')
        if not geom_raw: continue
        try:
            geom_dict = json.loads(geom_raw)
            if 'features' in geom_dict and len(geom_dict['features']) > 0:
                actual_geom = json.loads(geom_dict['features'][0].get('geometry'))
            else: continue
        except Exception: continue

        kode_kab = str(item.get('code', '')).replace('.0', '').strip()
        kode_prov = str(item.get('adm1_code', '')).replace('.0', '').strip()

        if kode_kab and kode_kab.lower() != 'none':
            fitur_kabkota.append({
                "type": "Feature",
                "id": kode_kab, 
                "properties": {
                    "kode_kabupaten": kode_kab,
                    "kode_provinsi": kode_prov, 
                    "namadaerah": item.get('name', '')
                },  
                "geometry": actual_geom
            })

    geojson_kabkota = {"type": "FeatureCollection", "features": fitur_kabkota}

    gdf_kab = gpd.GeoDataFrame.from_features(geojson_kabkota)
    gdf_kab['geometry'] = gdf_kab['geometry'].simplify(tolerance=0.002, preserve_topology=True)
    gdf_prov = gdf_kab.dissolve(by='kode_provinsi').reset_index()

    geojson_prov_dict = json.loads(gdf_prov.to_json())
    for feature in geojson_prov_dict['features']:
        feature['id'] = feature['properties']['kode_provinsi']

    geojson_kab_dict = json.loads(gdf_kab.to_json())
    for feature in geojson_kab_dict['features']:
        feature['id'] = feature['properties']['kode_kabupaten']

    return df_provinsi, df_kabkota, geojson_prov_dict, geojson_kab_dict, gdf_prov

df_provinsi, df_kabkota, geojson_provinsi, geojson_kabkota, gdf_provinsi = load_data()


# -----------------------------------------------------------------------------
# 3. KUSTOMISASI CSS & HEADER (LOGO)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* Sembunyikan elemen bawaan Streamlit (Header & Sidebar) */
        [data-testid="collapsedControl"] {display: none;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
            max-width: 95%;
        }
        /* Perbesar ukuran teks Tab agar lebih proporsional */
        button[data-baseweb="tab"] p {
            font-size: 1.15rem;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Menampilkan Logo Bappenas di atas kiri
try:
    import base64
    with open("logo_bappenas.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(f'<img src="data:image/png;base64,{encoded_string}" width="250" style="margin-bottom: 20px;">', unsafe_allow_html=True)
except FileNotFoundError:
    st.markdown("<h3 style='color:#0b5394; margin-bottom: 20px;'>Kementerian PPN/Bappenas</h3>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. MENU NAVIGASI (MENGGUNAKAN NATIVE TABS STREAMLIT)
# -----------------------------------------------------------------------------
tab_beranda, tab_peta, tab_analisis, tab_tentang = st.tabs([
    "Beranda",
    "Tentang IPEI",
    "Peta IPEI", 
    "Analisis Pilar & Tren"
])

# =========================================================
# ISI TAB: BERANDA (FULL BANNER)
# =========================================================
with tab_beranda:
    hero_html = """
    <style>
    .hero-container {
        background-image: linear-gradient(to right, rgba(13, 71, 161, 0.95), rgba(30, 136, 229, 0.4)), url('https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?q=80&w=2000&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        border-radius: 12px;
        padding: 100px 60px;
        color: white;
        min-height: 65vh; /* Membuat banner besar memakan layar */
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 3.8rem;
        font-weight: 800;
        margin-bottom: 25px;
        line-height: 1.1;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .hero-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        max-width: 900px;
        line-height: 1.7;
        opacity: 0.95;
    }
    </style>
    
    <div class="hero-container">
        <div class="hero-title">Indeks Pembangunan Ekonomi Inklusif (IPEI)</div>
        <div class="hero-subtitle">
            Platform visualisasi interaktif untuk mengevaluasi pemerataan pembangunan dan inklusivitas makroekonomi daerah.<br><br>
            Dasbor ini dirancang untuk mendukung penguatan <i>evidence-based planning</i> dalam pengembangan model pembangunan di seluruh wilayah Indonesia.
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)


# =========================================================
# ISI TAB: PETA IPEI
# =========================================================
with tab_peta:
    st.title("Peta Indeks Pembangunan Ekonomi Inklusif (IPEI)")
    st.markdown("Pemetaan skor tingkat wilayah untuk evaluasi pembangunan makroekonomi.")

    if "tingkat_peta" not in st.session_state:
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    def reset_peta():
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("📅 Pilih Tahun:", [2025, 2024, 2023, 2022, 2021])

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

    st.markdown("---")

    if st.session_state.tingkat_peta == "nasional":
        st.info("💡 **Petunjuk:** Klik pada salah satu area Provinsi di peta untuk melihat detail Kabupaten/Kota di dalamnya.")
        df_prov_filtered = df_provinsi[df_provinsi['tahun'].astype(int) == selected_year].reset_index(drop=True)

        if not df_prov_filtered.empty:
            if hasattr(px, 'choropleth_map'):
                fig_nasional = px.choropleth_map(
                    df_prov_filtered, geojson=geojson_provinsi, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    map_style="carto-positron", opacity=0.8, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_nasional.update_layout(
                    map=dict(center={"lat": -0.789, "lon": 113.921}, zoom=4),
                    margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
                )
            else:
                fig_nasional = px.choropleth_mapbox(
                    df_prov_filtered, geojson=geojson_provinsi, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    mapbox_style="carto-positron", opacity=0.8, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_nasional.update_layout(
                    mapbox=dict(center={"lat": -0.789, "lon": 113.921}, zoom=4),
                    margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
                )

            event = st.plotly_chart(fig_nasional, use_container_width=True, on_select="rerun", selection_mode="points", key="peta_awal")
            
            if event and event.get("selection") and event["selection"].get("points"):
                st.session_state.provinsi_terpilih = event["selection"]["points"][0]["location"]
                st.session_state.tingkat_peta = "provinsi"
                st.rerun()

    elif st.session_state.tingkat_peta == "provinsi":
        st.button("⬅️ Kembali ke Peta Nasional", on_click=reset_peta)
        df_kab_filtered = df_kabkota[df_kabkota['tahun'].astype(int) == selected_year].copy()
        df_kab_filtered['kode_prov'] = df_kab_filtered['kodedaerah'].astype(str).str[:2] + "00"
        df_kab_zoom = df_kab_filtered[df_kab_filtered['kode_prov'] == str(st.session_state.provinsi_terpilih)].reset_index(drop=True)
        
        if not df_kab_zoom.empty:
            st.markdown("### Detail Kabupaten/Kota")

            batas_provinsi = gdf_provinsi[gdf_provinsi['kode_provinsi'] == st.session_state.provinsi_terpilih]
            center_lat, center_lon, zoom_aman = -0.789, 113.921, 5 
            
            if not batas_provinsi.empty:
                minx, miny, maxx, maxy = batas_provinsi.total_bounds
                center_lat = (miny + maxy) / 2
                center_lon = (minx + maxx) / 2
                max_diff = max(maxx - minx, maxy - miny)
                zoom_ideal = math.log2(360 / max_diff) + 1.2 if max_diff > 0 else 8
                zoom_aman = max(4.0, min(zoom_ideal, 9.5))

            if hasattr(px, 'choropleth_map'):
                fig_zoom = px.choropleth_map(
                    df_kab_zoom, geojson=geojson_kabkota, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    map_style="carto-positron", opacity=0.8, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_zoom.update_layout(
                    map=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom_aman),
                    margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
                )
            else:
                fig_zoom = px.choropleth_mapbox(
                    df_kab_zoom, geojson=geojson_kabkota, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    mapbox_style="carto-positron", opacity=0.8, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_zoom.update_layout(
                    mapbox=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom_aman),
                    margin={"r":0,"t":0,"l":0,"b":0},
                    coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
                )
            st.plotly_chart(fig_zoom, use_container_width=True, key="peta_zoom")


# =========================================================
# ISI TAB: ANALISIS PILAR & TREN
# =========================================================
with tab_analisis:
    st.title("Analisis Tren dan Pilar Ekonomi Inklusif")
    col1, col2 = st.columns(2)
    with col1:
        daerah_list = df_kabkota['namadaerah'].dropna().unique().tolist()
        daerah_list.sort()
        selected_daerah = st.selectbox("Pilih Kabupaten/Kota:", daerah_list)

    df_daerah = df_kabkota[df_kabkota['namadaerah'] == selected_daerah].sort_values('tahun')

    if not df_daerah.empty:
        fig_trend = px.line(df_daerah, x='tahun', y='ipei', markers=True, title=f"Tren IPEI - {selected_daerah}")
        fig_trend.update_xaxes(dtick=1) 
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("---")
        tahun_terakhir = df_daerah['tahun'].max()
        df_pilar = df_daerah[df_daerah['tahun'] == tahun_terakhir]
        if not df_pilar.empty:
            df_chart_pilar = pd.DataFrame({'Pilar': ['Pilar 1', 'Pilar 2', 'Pilar 3'], 'Skor': [df_pilar['pilar1'].values[0], df_pilar['pilar2'].values[0], df_pilar['pilar3'].values[0]]})
            fig_bar = px.bar(df_chart_pilar, x='Pilar', y='Skor', color='Pilar', title=f"Skor per Pilar (Tahun {tahun_terakhir})")
            st.plotly_chart(fig_bar, use_container_width=True)


# =========================================================
# ISI TAB: TENTANG IPEI
# =========================================================
with tab_tentang:
    st.title("Tentang Indeks Pembangunan Ekonomi Inklusif")
    st.markdown("""
    <style>
    .hero-banner-info {
        background: linear-gradient(135deg, #0b5394 0%, #3d85c6 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .hero-title-info {
        font-size: 2.2em;
        font-weight: 700;
        margin-bottom: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .hero-text-info {
        font-size: 1.15em;
        line-height: 1.6;
        margin-bottom: 0;
        opacity: 0.95;
    }
    .card-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 25px 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border: 1px solid #f0f2f6;
        height: 100%;
        transition: transform 0.3s ease;
    }
    .card-container:hover {
        transform: translateY(-5px);
    }
    .card-title {
        color: #0b5394;
        font-size: 1.25em;
        font-weight: 700;
        margin-bottom: 20px;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 12px;
        line-height: 1.4;
    }
    .sub-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-size: 1.05em;
        color: #444444;
        font-weight: 500;
    }
    .sub-icon {
        margin-right: 12px;
        font-size: 1.3em;
        background-color: #f0f8ff;
        padding: 5px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-banner-info">
        <div class="hero-title-info">Indeks Pembangunan Ekonomi Inklusif (IPEI)</div>
        <div class="hero-text-info">
            Indeks Pembangunan Ekonomi Inklusif (IPEI) merupakan alat ukur komprehensif untuk memantau tingkat inklusivitas pembangunan ekonomi suatu wilayah. Indeks ini dirancang untuk memastikan bahwa pertumbuhan ekonomi berjalan selaras dengan pemerataan pendapatan, pengurangan kemiskinan, serta perluasan akses dan kesempatan bagi seluruh lapisan masyarakat.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Komponen Pembentuk IPEI")
    st.markdown("Struktur penilaian IPEI didasarkan pada **3 (tiga) pilar utama** dan **8 (delapan) sub-pilar** penggerak, yaitu:")
    st.write("") 

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Pilar 1:<br>Pertumbuhan & Perkembangan Ekonomi</div>
            <div class="sub-item"><span class="sub-icon">📊</span> Sub-Pilar 1.1: Pertumbuhan Ekonomi</div>
            <div class="sub-item"><span class="sub-icon">💼</span> Sub-Pilar 1.2: Kesempatan Kerja</div>
            <div class="sub-item"><span class="sub-icon">🏗️</span> Sub-Pilar 1.3: Infrastruktur</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Pilar 2:<br>Pemerataan Pendapatan & Pengurangan Kemiskinan</div>
            <div class="sub-item"><span class="sub-icon">📉</span> Sub-Pilar 2.1: Ketimpangan</div>
            <div class="sub-item"><span class="sub-icon">🛡️</span> Sub-Pilar 2.2: Kemiskinan</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card-container">
            <div class="card-title">Pilar 3:<br>Perluasan Akses & Kesempatan</div>
            <div class="sub-item"><span class="sub-icon">🎓</span> Sub-Pilar 3.1: Kapabilitas Manusia</div>
            <div class="sub-item"><span class="sub-icon">🏥</span> Sub-Pilar 3.2: Infrastruktur Dasar</div>
            <div class="sub-item"><span class="sub-icon">💳</span> Sub-Pilar 3.3: Keuangan Inklusif</div>
        </div>
        """, unsafe_allow_html=True)
