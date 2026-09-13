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
# 3. KUSTOMISASI CSS GLOBAL
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
        
        /* Mempercantik ukuran teks Tab agar rapi */
        button[data-baseweb="tab"] p {
            font-size: 1.15rem;
            font-weight: 600;
        }
        
        /* Memaksa tombol utama (primary) menjadi warna Biru Bappenas */
        button[kind="primary"] {
            background-color: #0b5394 !important;
            border-color: #0b5394 !important;
            transition: all 0.3s ease;
        }
        button[kind="primary"]:hover {
            background-color: #083c6b !important;
            border-color: #083c6b !important;
        }
        
        /* Membuat ujung gambar (image) melengkung elegan */
        .stImage > img {
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
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
# 4. MENU NAVIGASI NATIVE (ST.TABS)
# -----------------------------------------------------------------------------
# PERUBAHAN: Posisi "Tentang IPEI" digeser menjadi urutan ke-2
tab_beranda, tab_tentang, tab_peta, tab_analisis, tab_metadata = st.tabs([
    "Beranda", 
    "Tentang IPEI",
    "Peta IPEI", 
    "Analisis Pilar & Tren", 
    "Metadata"
])


# =========================================================
# ISI TAB: BERANDA
# =========================================================
with tab_beranda:
    # -----------------------------------------------------
    # CSS KHUSUS HERO BERANDA
    # -----------------------------------------------------
    st.markdown("""
    <style>

    /* =====================================================
       HERO BERANDA IPEI
       ===================================================== */

    .st-key-hero_ipei {
        position: relative;
        overflow: hidden;

        background:
            radial-gradient(
                circle at 82% 22%,
                rgba(255,255,255,0.95) 0%,
                rgba(255,255,255,0.30) 20%,
                rgba(255,255,255,0) 42%
            ),
            linear-gradient(
                180deg,
                #ffffff 0%,
                #f2f9ff 18%,
                #d9edfc 42%,
                #acd8f5 70%,
                #74b6e6 100%
            );

        border-radius: 28px;
        padding: 58px 58px 52px 58px;
        margin-top: 18px;
        margin-bottom: 30px;

        min-height: 570px;

        box-shadow:
            0 18px 45px rgba(11, 83, 148, 0.15);

        border: 1px solid rgba(11, 83, 148, 0.08);
    }


    /* Dekorasi background */
    .st-key-hero_ipei::before {
        content: "";
        position: absolute;

        width: 500px;
        height: 500px;

        right: -170px;
        top: -200px;

        border-radius: 50%;

        background:
            radial-gradient(
                circle,
                rgba(255,255,255,0.40),
                rgba(255,255,255,0)
            );

        pointer-events: none;
    }


    /* -----------------------------------------------------
       JUDUL HERO
       ----------------------------------------------------- */

    .ipei-hero-title {

        color: #123b5d;

        font-family:
            'Segoe UI',
            Arial,
            sans-serif;

        font-size: clamp(3rem, 4.2vw, 5rem);

        line-height: 1.04;

        letter-spacing: -2px;

        font-weight: 750;

        margin-top: 18px;
        margin-bottom: 28px;

        max-width: 760px;
    }


    .ipei-highlight {

        color: #0b5394;

        font-weight: 800;
    }


    /* -----------------------------------------------------
       DESKRIPSI
       ----------------------------------------------------- */

    .ipei-hero-description {

        color: #40566a;

        font-size: 1.20rem;

        line-height: 1.72;

        max-width: 700px;

        margin-bottom: 24px;

        font-family:
            'Segoe UI',
            Arial,
            sans-serif;
    }


    /* -----------------------------------------------------
       BUTTON PETA
       ----------------------------------------------------- */

    .st-key-hero_btn_peta button {

        background: #0b5394 !important;

        color: #ffffff !important;

        border: 1px solid #0b5394 !important;

        border-radius: 999px !important;

        min-height: 54px;

        font-size: 1.03rem !important;

        font-weight: 700 !important;

        padding-left: 22px !important;
        padding-right: 22px !important;

        box-shadow:
            0 7px 18px rgba(11,83,148,0.22);

        transition:
            transform .20s ease,
            box-shadow .20s ease,
            background .20s ease;
    }


    .st-key-hero_btn_peta button:hover {

        background: #083c6b !important;

        border-color: #083c6b !important;

        transform: translateY(-2px);

        box-shadow:
            0 10px 24px rgba(11,83,148,0.28);
    }


    /* -----------------------------------------------------
       BUTTON METADATA
       ----------------------------------------------------- */

    .st-key-hero_btn_metadata button {

        background: rgba(255,255,255,0.48) !important;

        color: #163e61 !important;

        border: 1px solid rgba(11,83,148,0.14) !important;

        border-radius: 999px !important;

        min-height: 54px;

        font-size: 1.03rem !important;

        font-weight: 700 !important;

        padding-left: 22px !important;
        padding-right: 22px !important;

        backdrop-filter: blur(8px);

        transition:
            transform .20s ease,
            background .20s ease;
    }


    .st-key-hero_btn_metadata button:hover {

        background: rgba(255,255,255,0.75) !important;

        transform: translateY(-2px);

        color: #0b5394 !important;
    }


    /* -----------------------------------------------------
       GAMBAR HERO
       ----------------------------------------------------- */

    .st-key-hero_ipei [data-testid="stImage"] img {

        border-radius: 0 !important;

        box-shadow: none !important;

        object-fit: contain;

        max-height: 470px;
    }


    /* -----------------------------------------------------
       FALLBACK ILLUSTRATION
       ----------------------------------------------------- */

    .inclusive-illustration {

        width: 100%;

        display: flex;

        justify-content: center;

        align-items: center;

        min-height: 430px;
    }


    /* -----------------------------------------------------
       RESPONSIVE
       ----------------------------------------------------- */

    @media (max-width: 900px) {

        .st-key-hero_ipei {

            padding:
                36px 28px 32px 28px;

            border-radius: 22px;

            min-height: auto;
        }


        .ipei-hero-title {

            font-size: 3rem;

            letter-spacing: -1px;
        }


        .ipei-hero-description {

            font-size: 1.05rem;
        }

    }

    </style>
    """, unsafe_allow_html=True)


    # -----------------------------------------------------
    # HERO CONTAINER
    # -----------------------------------------------------

    with st.container(key="hero_ipei"):

        col_teks, col_gambar = st.columns(
            [1.18, 0.82],
            gap="large"
        )


        # =================================================
        # BAGIAN KIRI
        # =================================================

        with col_teks:

            st.markdown("""
            <div style="height:15px;"></div>

            <div class="ipei-hero-title">

                Indeks Pembangunan<br>
                Ekonomi Inklusif

                <span class="ipei-highlight">
                    (IPEI)
                </span>

            </div>


            <div class="ipei-hero-description">

                Tingkatkan evaluasi pembangunan makroekonomi daerah
                dengan analitik spasial yang komprehensif.

                Jaga fokus analisis strategis sekaligus wujudkan
                ekosistem pertumbuhan yang inklusif dan
                berwawasan lingkungan.

            </div>

            """, unsafe_allow_html=True)


            # ---------------------------------------------
            # BUTTON
            # ---------------------------------------------

            btn_peta, btn_metadata = st.columns(
                [1.05, 0.95],
                gap="small"
            )


            with btn_peta:

                st.button(
                    "🗺️  Eksplorasi Peta",
                    type="primary",
                    use_container_width=True,
                    key="hero_btn_peta",
                    on_click=pindah_tab,
                    args=("Peta IPEI",)
                )


            with btn_metadata:

                st.button(
                    "📄  Metadata",
                    use_container_width=True,
                    key="hero_btn_metadata",
                    on_click=pindah_tab,
                    args=("Metadata",)
                )


        # =================================================
        # BAGIAN KANAN — ILUSTRASI
        # =================================================

        with col_gambar:

            # -------------------------------------------------
            # Jika Anda memiliki gambar sendiri:
            #
            # Simpan file sebagai:
            #
            # assets/hero_ipei.png
            #
            # Lalu ganti blok SVG di bawah menjadi:
            #
            # st.image(
            #     "assets/hero_ipei.png",
            #     use_container_width=True
            # )
            # -------------------------------------------------


            # Ilustrasi sementara:
            # pertumbuhan ekonomi + masyarakat + inklusivitas

            st.markdown("""
            <div class="inclusive-illustration">

            <svg
                width="100%"
                viewBox="0 0 600 500"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >

            <!-- BACKGROUND GLOW -->

            <circle
                cx="320"
                cy="240"
                r="205"
                fill="white"
                fill-opacity="0.25"
            />


            <circle
                cx="320"
                cy="240"
                r="165"
                fill="white"
                fill-opacity="0.20"
            />


            <!-- PLATFORM -->

            <ellipse
                cx="315"
                cy="405"
                rx="225"
                ry="45"
                fill="#0B5394"
                fill-opacity="0.12"
            />


            <!-- BAR CHART -->

            <rect
                x="205"
                y="275"
                width="62"
                height="120"
                rx="14"
                fill="#66B7E8"
            />

            <rect
                x="285"
                y="220"
                width="62"
                height="175"
                rx="14"
                fill="#2986CC"
            />

            <rect
                x="365"
                y="150"
                width="62"
                height="245"
                rx="14"
                fill="#0B5394"
            />


            <!-- TREND LINE -->

            <path
                d="
                M175 300
                C240 285,
                 275 230,
                 315 235
                C360 240,
                 390 165,
                 455 130
                "
                stroke="#083C6B"
                stroke-width="12"
                stroke-linecap="round"
                fill="none"
            />


            <!-- ARROW -->

            <path
                d="M430 119 L463 126 L448 158"
                stroke="#083C6B"
                stroke-width="12"
                stroke-linecap="round"
                stroke-linejoin="round"
            />


            <!-- PERSON LEFT -->

            <circle
                cx="135"
                cy="220"
                r="28"
                fill="#F6C66C"
            />

            <rect
                x="104"
                y="252"
                width="62"
                height="86"
                rx="28"
                fill="#FFFFFF"
            />

            <path
                d="M112 275 L75 322"
                stroke="#FFFFFF"
                stroke-width="20"
                stroke-linecap="round"
            />

            <path
                d="M159 275 L190 320"
                stroke="#FFFFFF"
                stroke-width="20"
                stroke-linecap="round"
            />


            <!-- PERSON RIGHT -->

            <circle
                cx="490"
                cy="260"
                r="28"
                fill="#E5A35A"
            />

            <rect
                x="459"
                y="292"
                width="62"
                height="86"
                rx="28"
                fill="#DDF2FF"
            />

            <path
                d="M465 310 L430 345"
                stroke="#DDF2FF"
                stroke-width="20"
                stroke-linecap="round"
            />

            <path
                d="M515 310 L548 344"
                stroke="#DDF2FF"
                stroke-width="20"
                stroke-linecap="round"
            />


            <!-- PERSON TOP -->

            <circle
                cx="290"
                cy="86"
                r="27"
                fill="#F2BB67"
            />

            <rect
                x="260"
                y="116"
                width="60"
                height="72"
                rx="28"
                fill="#FFFFFF"
                fill-opacity="0.94"
            />


            <!-- CONNECTION NODES -->

            <circle
                cx="135"
                cy="220"
                r="46"
                stroke="#FFFFFF"
                stroke-opacity="0.50"
                stroke-width="3"
            />

            <circle
                cx="490"
                cy="260"
                r="46"
                stroke="#FFFFFF"
                stroke-opacity="0.50"
                stroke-width="3"
            />

            <circle
                cx="290"
                cy="86"
                r="45"
                stroke="#FFFFFF"
                stroke-opacity="0.50"
                stroke-width="3"
            />


            <!-- CONNECTION LINES -->

            <path
                d="M170 200 L260 115"
                stroke="#FFFFFF"
                stroke-opacity="0.50"
                stroke-width="3"
                stroke-dasharray="8 8"
            />

            <path
                d="M320 105 L460 230"
                stroke="#FFFFFF"
                stroke-opacity="0.50"
                stroke-width="3"
                stroke-dasharray="8 8"
            />

            </svg>

            </div>
            """, unsafe_allow_html=True)


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
# ISI TAB: METADATA
# =========================================================
with tab_metadata:
    st.title("Metadata Indikator IPEI")
    st.info("Halaman penjelasan dan kamus data Metadata sedang dalam tahap pengembangan dan akan segera ditambahkan di sini.")
