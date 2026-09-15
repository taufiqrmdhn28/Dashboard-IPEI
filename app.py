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
        /* Sembunyikan elemen bawaan Streamlit */
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
            transform: translateY(-2px);
        }
        
        /* Animasi Mengambang (Floating) untuk Gambar 3D */
        @keyframes float-animation {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
        }
        .floating-img {
            width: 100%;
            max-width: 650px;
            animation: float-animation 4s ease-in-out infinite;
            filter: drop-shadow(0px 15px 25px rgba(0,0,0,0.15));
            display: block;
            margin: auto;
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
tab_beranda, tab_tentang, tab_peta, tab_analisis, tab_metadata  = st.tabs([
    "Beranda",
    "Tentang IPEI",
    "Peta IPEI", 
    "Analisis Pilar & Tren",
    "Metadata"
])

# =========================================================
# ISI TAB: BERANDA (FULL BANNER)
# =========================================================
with tab_beranda:
    # Menggunakan st.columns agar ukurannya otomatis sama persis dengan batas tab (tidak melebar)
    col_teks, col_gambar = st.columns([1.2, 1], gap="large")
    
    with col_teks:
        st.markdown("<br><br>", unsafe_allow_html=True) # Spacer vertikal agar seimbang
        st.markdown("""
        <h1 style="color: #083c6b; font-size: 3.5rem; font-weight: 800; line-height: 1.2; margin-bottom: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            Indeks Pembangunan Ekonomi Inklusif <span style="color: #2196f3;">(IPEI)</span>
        </h1>
        <p style="color: #4a5568; font-size: 1.15rem; line-height: 1.7; margin-bottom: 30px;">
            Tingkatkan evaluasi pembangunan makroekonomi daerah dengan analitik spasial yang komprehensif. Jaga fokus analisis strategis sekaligus wujudkan ekosistem pertumbuhan yang inklusif dan berwawasan lingkungan.
        </p>
        """, unsafe_allow_html=True)
        
        # Tombol Aksi
        btn1, btn2, _ = st.columns([1.2, 1.2, 1]) # Kolom kosong di kanan agar tombol tidak terlalu panjang
        
        with btn1:
            if st.button("Eksplorasi Peta", type="primary", use_container_width=True):
                # Injeksi JS untuk langsung mengklik tab "Peta IPEI"
                js = """
                <script>
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                for (var i=0; i<tabs.length; i++) {
                    if (tabs[i].innerText.includes('Peta IPEI')) {
                        tabs[i].click();
                        break;
                    }
                }
                </script>
                """
                st.components.v1.html(js, height=0)
                
        with btn2:
            if st.button("Lihat Metadata", use_container_width=True):
                # Injeksi JS untuk langsung mengklik tab "Metadata"
                js = """
                <script>
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                for (var i=0; i<tabs.length; i++) {
                    if (tabs[i].innerText.includes('Metadata')) {
                        tabs[i].click();
                        break;
                    }
                }
                </script>
                """
                st.components.v1.html(js, height=0)
    
    with col_gambar:
        # Menyisipkan gambar ipei_inklusif.png dengan CSS class untuk animasi melayang
        try:
            with open("ipei_inklusif.png", "rb") as img_file:
                encoded_img = base64.b64encode(img_file.read()).decode()
            st.markdown(f'<img src="data:image/png;base64,{encoded_img}" class="floating-img">', unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("⚠️ File 'ipei_inklusif.png' tidak ditemukan. Pastikan file ada di folder yang sama.")

# =========================================================
# ISI TAB: PETA IPEI
# =========================================================
with tab_peta:
    # 1. Custom Premium Header
    st.markdown("""
    <div style="margin-bottom: 25px; margin-top: 10px;">
        <h2 style="color: #083c6b; font-weight: 800; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-bottom: 8px;">
            Eksplorasi Spasial IPEI
        </h2>
        <p style="color: #4a5568; font-size: 1.1rem; line-height: 1.6;">
            Analisis geospasial interaktif pencapaian pembangunan makroekonomi wilayah. 
            Sajikan data dengan presisi tinggi untuk mendukung pengambilan keputusan strategis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "tingkat_peta" not in st.session_state:
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    def reset_peta():
        st.session_state.tingkat_peta = "nasional"
        st.session_state.provinsi_terpilih = None

    # 2. Control Panel (Filter) dengan desain menyatu
    st.markdown("""
        <style>
        .filter-panel {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px 25px 0px 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        </style>
        <div class="filter-panel">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("📅 Periode Analisis:", [2025, 2024, 2023, 2022, 2021])

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
        selected_label = st.selectbox("🎯 Indikator Pemetaan:", list(indikator_dict.keys()))
        selected_kolom = indikator_dict[selected_label]
        
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Pengaturan Desain Peta Plotly (Lebih Tinggi & Elegan)
    fig_layout_updates = dict(
        margin={"r":0,"t":0,"l":0,"b":0},
        height=620, # Peta dibuat jauh lebih tinggi agar terlihat megah
        coloraxis_colorbar=dict(
            title=dict(text="Skor", font=dict(size=14, color='#083c6b', family="Segoe UI")), 
            yanchor="middle", y=0.5, 
            ticks="outside",
            bgcolor="rgba(255,255,255,0.85)", # Latar belakang legenda semi-transparan
            bordercolor="#cbd5e1",
            borderwidth=1,
            thickness=15,
            len=0.8
        )
    )

    if st.session_state.tingkat_peta == "nasional":
        # Interactive Guide Box
        st.markdown("""
            <div style="background-color: #e6f2ff; border-left: 5px solid #2196f3; padding: 12px 20px; border-radius: 4px; margin-bottom: 25px;">
                <span style="color: #0b5394; font-weight: 700;">💡 Interactive Guide:</span> <span style="color: #334155; font-weight: 500;">Klik pada area Provinsi mana pun di peta untuk melakukan <i>drill-down</i> interaktif ke tingkat Kabupaten/Kota.</span>
            </div>
        """, unsafe_allow_html=True)
        
        df_prov_filtered = df_provinsi[df_provinsi['tahun'].astype(int) == selected_year].reset_index(drop=True)

        if not df_prov_filtered.empty:
            if hasattr(px, 'choropleth_map'):
                fig_nasional = px.choropleth_map(
                    df_prov_filtered, geojson=geojson_provinsi, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    map_style="carto-positron", opacity=0.85, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_nasional.update_layout(map=dict(center={"lat": -0.789, "lon": 113.921}, zoom=4.2), **fig_layout_updates)
            else:
                fig_nasional = px.choropleth_mapbox(
                    df_prov_filtered, geojson=geojson_provinsi, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    mapbox_style="carto-positron", opacity=0.85, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_nasional.update_layout(mapbox=dict(center={"lat": -0.789, "lon": 113.921}, zoom=4.2), **fig_layout_updates)

            # 4. Membungkus Peta dalam wadah berbayang (Shadow Box) agar sekelas dashboard UI premium
            st.markdown('<div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 4px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); background-color: white;">', unsafe_allow_html=True)
            event = st.plotly_chart(fig_nasional, use_container_width=True, on_select="rerun", selection_mode="points", key="peta_awal")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if event and event.get("selection") and event["selection"].get("points"):
                st.session_state.provinsi_terpilih = event["selection"]["points"][0]["location"]
                st.session_state.tingkat_peta = "provinsi"
                st.rerun()

    elif st.session_state.tingkat_peta == "provinsi":
        # Desain tombol kembali (Back Button) dan Judul yang rapi
        col_back, col_title = st.columns([1, 4])
        with col_back:
            st.button("🔙 Kembali ke Nasional", on_click=reset_peta, use_container_width=True)
        with col_title:
            st.markdown(f"<h3 style='margin-top: 5px; color: #083c6b; font-weight: 700;'>Detail Analisis Kabupaten/Kota</h3>", unsafe_allow_html=True)
        
        st.write("") # Spacer

        df_kab_filtered = df_kabkota[df_kabkota['tahun'].astype(int) == selected_year].copy()
        df_kab_filtered['kode_prov'] = df_kab_filtered['kodedaerah'].astype(str).str[:2] + "00"
        df_kab_zoom = df_kab_filtered[df_kab_filtered['kode_prov'] == str(st.session_state.provinsi_terpilih)].reset_index(drop=True)
        
        if not df_kab_zoom.empty:
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
                    map_style="carto-positron", opacity=0.85, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_zoom.update_layout(map=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom_aman), **fig_layout_updates)
            else:
                fig_zoom = px.choropleth_mapbox(
                    df_kab_zoom, geojson=geojson_kabkota, locations='kodedaerah',            
                    color=selected_kolom, color_continuous_scale="RdYlGn",  
                    mapbox_style="carto-positron", opacity=0.85, hover_name='namadaerah',
                    labels={selected_kolom: selected_label}
                )
                fig_zoom.update_layout(mapbox=dict(center={"lat": center_lat, "lon": center_lon}, zoom=zoom_aman), **fig_layout_updates)
            
            # Membungkus peta zoom dengan Shadow Box yang sama
            st.markdown('<div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 4px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); background-color: white;">', unsafe_allow_html=True)
            st.plotly_chart(fig_zoom, use_container_width=True, key="peta_zoom")
            st.markdown('</div>', unsafe_allow_html=True)


with tab_analisis:
    st.markdown("""
        <style>
        .analytics-header { margin-bottom: 25px; margin-top: 10px; }
        .analytics-title { color: #083c6b; font-weight: 800; font-size: 2.2rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin-bottom: 8px; }
        .analytics-subtitle { color: #4a5568; font-size: 1.1rem; line-height: 1.6; }
        .chart-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 25px; }
        .history-table::-webkit-scrollbar { width: 6px; }
        .history-table::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
        </style>
        <div class="analytics-header">
            <div class="analytics-title">Analisis Tren & Komposisi Pilar</div>
            <div class="analytics-subtitle">
                Pantau pergerakan deret waktu (*time-series*) dan bedah dekomposisi pilar penyusun ekonomi inklusif secara mendalam dari tahun 2011 - 2025.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Hierarki Indikator
    hierarki_indikator = {
        "Skor Total IPEI": {
            "kolom": "ipei",
            "komponen": {
                "Pilar 1: Pertumbuhan & Perkembangan": "pilar1",
                "Pilar 2: Kesetaraan & Inklusi": "pilar2",
                "Pilar 3: Kemiskinan & Pekerjaan": "pilar3"
            }
        },
        "Pilar 1: Pertumbuhan dan Perkembangan Ekonomi": {
            "kolom": "pilar1",
            "komponen": {
                "Sub 1.1: Pertumbuhan Ekonomi": "sp11", 
                "Sub 1.2: Kesempatan Kerja": "sp12", 
                "Sub 1.3: Infrastruktur": "sp13"
            }
        },
        "Pilar 2: Kesetaraan dan Inklusi": {
            "kolom": "pilar2",
            "komponen": {
                "Sub 2.1: Ketimpangan": "sp21", 
                "Sub 2.2: Kemiskinan": "sp22"
            }
        },
        "Pilar 3: Kemiskinan dan Kondisi Pekerjaan": {
            "kolom": "pilar3",
            "komponen": {
                "Sub 3.1: Kapabilitas Manusia": "sp31", 
                "Sub 3.2: Infrastruktur Dasar": "sp32", 
                "Sub 3.3: Keuangan Inklusif": "sp33"
            }
        }
    }

    subtab_prov, subtab_kab = st.tabs(["🏛️ Tingkat Provinsi", "🏙️ Tingkat Kabupaten/Kota"])

    # --- FUNGSI HELPER GRAFIK AREA ---
    def buat_grafik_area(df, y_col, judul):
        fig = px.area(df, x='tahun', y=y_col, markers=True)
        fig.update_traces(
            line_color='#0ea5e9', 
            fillcolor='rgba(14, 165, 233, 0.15)',
            marker=dict(size=8, color='#0284c7', line=dict(width=2, color='white'))
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title="", tickmode='linear', dtick=1),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title="", rangemode='tozero'),
            height=350, hovermode="x unified"
        )
        return fig

    # --- FUNGSI HELPER TABEL HISTORIS PROGRESS BAR (ANTI-BOCOR) ---
    def buat_tabel_historis(df, komponen):
        komponen_cols = list(komponen.values())
        max_val_data = df[komponen_cols].max().max() if not df.empty else 10
        max_val_bar = max(10, max_val_data * 1.15) 

        # Menggunakan List untuk menyusun HTML dalam satu baris murni tanpa "enter" yang bikin error di Streamlit
        html = []
        html.append('<div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-top: 5px;">')
        html.append('<div style="margin-bottom:15px; font-weight:800; color:#083c6b; font-size:1.15rem;">Rincian Historis Komposisi Penyusun (2011 - 2025)</div>')
        html.append('<div style="display: flex; align-items: flex-end; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 5px;">')
        html.append('<div style="width: 70px; font-weight: 700; color: #475569; font-size: 0.85rem;">Tahun</div>')
        
        for label in komponen.keys():
            html.append(f'<div style="flex: 1; padding: 0 15px; font-weight: 700; color: #475569; font-size: 0.85rem; line-height: 1.3;">{label}</div>')
        html.append('</div><div class="history-table" style="max-height: 450px; overflow-y: auto; padding-right: 5px;">')
        
        # Looping urut tahun terbaru ke paling lama
        for yr in sorted(df['tahun'].unique(), reverse=True):
            df_yr = df[df['tahun'] == yr]
            html.append(f'<div style="display: flex; align-items: center; border-bottom: 1px solid #f8fafc; padding: 12px 0; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor=\'#f1f5f9\'" onmouseout="this.style.backgroundColor=\'transparent\'">')
            html.append(f'<div style="width: 70px; font-weight: 800; color: #64748b; font-size: 0.95rem;">{int(yr)}</div>')
            
            for label, col in komponen.items():
                val = df_yr[col].values[0] if not df_yr.empty else 0
                pct = min((val / max_val_bar) * 100, 100)
                # Tag HTML dipadatkan agar tidak dibaca sebagai paragraf oleh Streamlit
                html.append(f'<div style="flex: 1; padding: 0 15px;"><div style="font-size: 0.9rem; color: #0f172a; font-weight: 700; margin-bottom: 5px;">{val:.2f}</div><div style="width: 100%; background: #e2e8f0; height: 7px; border-radius: 4px;"><div style="width: {pct}%; background: linear-gradient(90deg, #0ea5e9, #2563eb); height: 100%; border-radius: 4px;"></div></div></div>')
            
            html.append('</div>')
        
        html.append('</div></div>')
        return "".join(html)


    # ==========================================
    # SUB-TAB 1: PROVINSI
    # ==========================================
    with subtab_prov:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            list_provinsi = ["Nasional (Rata-rata)"] + sorted(df_provinsi['namadaerah'].dropna().unique().tolist())
            pilihan_prov = st.selectbox("📍 Pilih Provinsi:", list_provinsi, key="pil_prov")
        with col_f2:
            pilihan_ind = st.selectbox("🎯 Pilih Indikator:", list(hierarki_indikator.keys()), key="ind_prov")

        if pilihan_prov == "Nasional (Rata-rata)":
            df_prov_chart = df_provinsi.groupby('tahun').mean(numeric_only=True).reset_index()
        else:
            df_prov_chart = df_provinsi[df_provinsi['namadaerah'] == pilihan_prov].sort_values('tahun')

        if not df_prov_chart.empty:
            kolom_target = hierarki_indikator[pilihan_ind]["kolom"]
            komponen = hierarki_indikator[pilihan_ind]["komponen"]
            
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            # 1. Grafik Area Line
            st.plotly_chart(buat_grafik_area(df_prov_chart, kolom_target, pilihan_ind), use_container_width=True)
            # 2. Tabel Grid Historis 2011-2025
            st.markdown(buat_tabel_historis(df_prov_chart, komponen), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- FITUR DOWNLOAD FULL DATA (MENGABAIKAN FILTER) ---
            csv_prov_all = df_provinsi.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Seluruh Data Provinsi (CSV)",
                data=csv_prov_all,
                file_name="Data_IPEI_Seluruh_Provinsi.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.warning("Data tidak tersedia untuk wilayah ini.")


    # ==========================================
    # SUB-TAB 2: KABUPATEN/KOTA
    # ==========================================
    with subtab_kab:
        map_provinsi = dict(zip(df_provinsi['kodedaerah'].str[:2] + '00', df_provinsi['namadaerah']))
        df_kabkota['nama_provinsi'] = df_kabkota['kodedaerah'].str[:2] + '00'
        df_kabkota['nama_provinsi'] = df_kabkota['nama_provinsi'].map(map_provinsi)

        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            list_filter_prov = sorted(df_kabkota['nama_provinsi'].dropna().unique().tolist())
            filter_prov = st.selectbox("📍 Filter Provinsi:", list_filter_prov, key="filt_prov_kab")
        with col_k2:
            df_kab_filtered = df_kabkota[df_kabkota['nama_provinsi'] == filter_prov]
            list_kab = sorted(df_kab_filtered['namadaerah'].dropna().unique().tolist())
            pilihan_kab = st.selectbox("🏙️ Pilih Kabupaten/Kota:", list_kab, key="pil_kab")
        with col_k3:
            pilihan_ind_kab = st.selectbox("🎯 Pilih Indikator:", list(hierarki_indikator.keys()), key="ind_kab")

        df_kab_chart = df_kab_filtered[df_kab_filtered['namadaerah'] == pilihan_kab].sort_values('tahun')

        if not df_kab_chart.empty:
            kolom_target_kab = hierarki_indikator[pilihan_ind_kab]["kolom"]
            komponen_kab = hierarki_indikator[pilihan_ind_kab]["komponen"]
            
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            # 1. Grafik Area Line
            st.plotly_chart(buat_grafik_area(df_kab_chart, kolom_target_kab, pilihan_ind_kab), use_container_width=True)
            # 2. Tabel Grid Historis 2011-2025
            st.markdown(buat_tabel_historis(df_kab_chart, komponen_kab), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # --- FITUR DOWNLOAD FULL DATA (MENGABAIKAN FILTER) ---
            csv_kab_all = df_kabkota.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Seluruh Data Kabupaten/Kota (CSV)",
                data=csv_kab_all,
                file_name="Data_IPEI_Seluruh_Kabupaten.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.warning("Data tidak tersedia untuk wilayah ini.")


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
# =========================================================
# ISI TAB: METADATA (DESAIN DOKUMENTASI MODERN)
# =========================================================
with tab_metadata:
    # 1. Kustomisasi CSS Khusus untuk Expander & Gambar Sticky
    st.markdown("""
    <style>
    [data-testid="stExpander"] {
        border: none;
        border-bottom: 1px solid #f0f2f6;
        border-radius: 0;
        box-shadow: none;
        background-color: transparent;
    }
    [data-testid="stExpander"] summary { padding: 20px 0; }
    [data-testid="stExpander"] summary p {
        font-size: 1.15rem; font-weight: 600; color: #0f172a;
    }
    [data-testid="stExpander"] svg { color: #0ea5e9; width: 1.5rem; height: 1.5rem; }
    .meta-desc { color: #475569; font-size: 1rem; line-height: 1.6; margin-bottom: 15px; }
    .meta-badge {
        background-color: #f1f5f9; color: #0b5394; padding: 3px 8px;
        border-radius: 6px; font-weight: 700; font-size: 0.85rem; margin-right: 8px;
    }
    
    /* Membuat wadah abu-abu ikut terscroll (Sticky) */
    .sticky-right-container {
        position: -webkit-sticky;
        position: sticky;
        top: 80px; /* Jarak dari atas layar saat menempel */
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        padding: 40px 30px;
        border-radius: 20px;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        z-index: 10;
    }
    
    /* Animasi Mengambang (Floating) untuk Gambar 3D */
    @keyframes float-meta {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-12px); }
        100% { transform: translateY(0px); }
    }
    .floating-meta-img {
        width: 100%;
        max-width: 450px;
        animation: float-meta 4s ease-in-out infinite;
        filter: drop-shadow(0 15px 25px rgba(0,0,0,0.15));
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #083c6b; font-weight: 800; margin-bottom: 5px;'>Kamus Data & Metadata Indikator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; margin-bottom: 25px;'>Pelajari definisi, metode perhitungan, dan sumber data dari seluruh 21 indikator penyusun IPEI.</p>", unsafe_allow_html=True)

    # 2. Navigasi Pemilihan Pilar
    pilihan_pilar = st.radio(
        "Pilih Pilar Analisis:",
        ["Pilar 1: Pertumbuhan & Perkembangan Ekonomi", 
         "Pilar 2: Pemerataan Pendapatan & Kemiskinan", 
         "Pilar 3: Perluasan Akses & Kesempatan"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("<hr style='margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)

    # 3. Tata Letak Split-Layout
    col_kiri, col_kanan = st.columns([1.3, 1], gap="large")

    with col_kiri:
        if pilihan_pilar == "Pilar 1: Pertumbuhan & Perkembangan Ekonomi":
            st.markdown("<h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 1.1: Pertumbuhan Ekonomi</h4>", unsafe_allow_html=True)
            with st.expander("01. Indikator 1.1.1: Pertumbuhan PDRB riil per kapita"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Ukuran pertumbuhan ekonomi individu secara rata-rata di suatu wilayah[cite: 1]. Semakin tinggi, semakin baik kesejahteraan individu[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $Pertumbuhan~PDRB~per~kapita=\frac{Y_{t}-Y_{t-1}}{Y_{t-1}}\times100\%$[cite: 1]. Angka ini didapatkan dari nilai PDB/PDRB harga konstan dibagi jumlah penduduk[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik Nasional[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("02. Indikator 1.1.2: Share manufaktur terhadap PDRB"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Persentase porsi sektor industri manufaktur/pengolahan terhadap keseluruhan PDB/PDRB[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{PDB(PDRB)~Industri~Pengolahan}{Total~PDB(PDRB)}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik Nasional[cite: 1].</div>", unsafe_allow_html=True)
                
            with st.expander("03. Indikator 1.1.3: Rasio Kredit Perbankan terhadap PDRB Nominal"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Perbandingan antara total pemberian kredit terhadap produktivitas ekonomi[cite: 1]. Menilai seberapa besar pinjaman atas total produksi[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Total~Kredit}{Total~PDB(PDRB)}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Otoritas Jasa Keuangan[cite: 1].</div>", unsafe_allow_html=True)

            st.markdown("<br><h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 1.2: Kesempatan Kerja</h4>", unsafe_allow_html=True)
            with st.expander("04. Indikator 1.2.1: Tingkat kesempatan kerja"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Menggambarkan peluang seorang individu yang termasuk dalam angkatan kerja untuk bisa terserap dalam pasar kerja atau dapat bekerja[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{penduduk~bekerja}{angkatan~kerja}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Sakernas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("05. Indikator 1.2.2: Persentase Penduduk Bekerja Penuh"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Pekerja penuh adalah pekerja yang jam kerjanya $\ge$ 35 jam per minggu (pekerja formal) yang menunjukkan pekerjaan relatif stabil[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Penduduk~Bekerja~\ge~35~jam/mg}{Penduduk~bekerja}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Sakernas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("06. Indikator 1.2.3: Persentase Tenaga Kerja dg Pendidikan Menengah ke Atas"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Tenaga kerja dengan ijazah terakhir SMA/SMK/MA/Sederajat atau lebih tinggi yang menunjukkan kualitas pekerja yang lebih baik[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Tenaga~kerja~dg~tk~Pendidikan~Menengah~ke~Atas}{Penduduk~bekerja}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Sakernas)[cite: 1].</div>", unsafe_allow_html=True)

            st.markdown("<br><h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 1.3: Infrastruktur Ekonomi</h4>", unsafe_allow_html=True)
            with st.expander("07. Indikator 1.3.1: Persentase Rumah Tangga yang Menggunakan Listrik/PLN"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Persentase rumah tangga yang di rumahnya sudah tersedia jaringan listrik/PLN terhadap total rumah tangga secara keseluruhan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Rumah~tangga~dengan~akses~listrik~(PLN)}{Rumah~tangga}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("08. Indikator 1.3.2: Persentase Penduduk yang Memiliki Telepon Genggam"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Persentase penduduk yang memiliki atau menguasai telepon seluler, menunjukkan kecakapan penggunaan perangkat telekomunikasi[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Penduduk~yang~memiliki~ponsel}{Penduduk}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("09. Indikator 1.3.3: Persentase Jalan dengan Kondisi Baik dan Sedang"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Persentase diukur dari total panjang jalan dengan kondisi baik dan sedang terhadap luas wilayah[cite: 1]. Mencerminkan keterjangkauan infrastruktur jalan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Panjang~jalan~baik}{Total~Luas~Wilayah}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Kementerian Pekerjaan Umum, Dinas PU)[cite: 1].</div>", unsafe_allow_html=True)

        elif pilihan_pilar == "Pilar 2: Pemerataan Pendapatan & Kemiskinan":
            st.markdown("<h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 2.1: Ketimpangan</h4>", unsafe_allow_html=True)
            with st.expander("01. Indikator 2.1.1: Rasio Pendapatan Gini"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Indikator yang menunjukkan tingkat ketimpangan pendapatan secara menyeluruh berdasarkan pengukuran luas kurva Lorenz[cite: 1]. Nilai berkisar antara 0 - 1[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $GR=1-\Sigma_{i=1}^{n}P_{i}(F_{i}+F_{i-1})$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("02. Indikator 2.1.2: Sumbangan Pendapatan Perempuan"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Indikator yang menggambarkan seberapa besar diskriminasi upah yang terjadi antara laki-laki dan perempuan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $X=AK_{f}\times Rasio~W_{f}$[cite: 1]. Dihitung dari proporsi angkatan kerja perempuan dikalikan rasio upah perempuan terhadap rata-rata upah[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Sakernas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("03. Indikator 2.1.3: Rasio Rata-rata Pengeluaran Rumah Tangga Desa & Kota"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Menunjukkan perbandingan rata-rata pengeluaran rumah tangga pedesaan terhadap rumah tangga perkotaan, yang menggambarkan disparitas wilayah[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{rata-rata~pengeluaran~penduduk~desa}{rata-rata~pengeluaran~penduduk~kota}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            st.markdown("<br><h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 2.2: Kemiskinan</h4>", unsafe_allow_html=True)
            with st.expander("04. Indikator 2.2.1: Persentase Penduduk Miskin"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Persentase penduduk miskin merupakan jumlah orang yang hidup di bawah garis kemiskinan per kapita per bulan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Jumlah~penduduk~miskin}{Jumlah~penduduk}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("05. Indikator 2.2.2: Rata-rata Konsumsi Protein per kapita per hari"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Jumlah konsumsi protein dari komoditi pangan yang dikonsumsi penduduk di satu wilayah secara rata-rata[cite: 1]. Menunjukkan perbaikan kesejahteraan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Jumlah~konsumsi~protein}{Jumlah~penduduk}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

        elif pilihan_pilar == "Pilar 3: Perluasan Akses & Kesempatan":
            st.markdown("<h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 3.1: Kapabilitas Manusia</h4>", unsafe_allow_html=True)
            with st.expander("01. Indikator 3.1.1: Angka Harapan Lama Sekolah"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Lamanya sekolah yang diharapkan akan dirasakan oleh anak pada umur tertentu (7 tahun ke atas) di masa mendatang[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $HLS_{a}^{t}=FK\times\Sigma_{i=a}^{n}\frac{E_{i}^{c}}{P_{i}^{t}}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("02. Indikator 3.1.2: Persentase Balita Mendapatkan Imunisasi Dasar Lengkap"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Menggambarkan tingkat pelayanan imunisasi dasar lengkap (DPT, polio, BCG, campak) pada balita di bawah usia 5 tahun[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Jumlah~balita~dengan~imunisasi~dasar~lengkap}{Jumlah~anak~usia<5~tahun}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas / Riskesdas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("03. Indikator 3.1.3: Persentase Penduduk yang Memiliki Jaminan Kesehatan"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Besaran cakupan jaminan kesehatan pada masyarakat yang bersifat sebagai jaring pengaman ketika mengalami kendala kesehatan[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Jumlah~Penduduk~yang~Memiliki~Jaminan~Kesehatan}{Jumlah~Penduduk}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            st.markdown("<br><h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 3.2: Infrastruktur Dasar</h4>", unsafe_allow_html=True)
            with st.expander("04. Indikator 3.2.1: Persentase Rumah Tangga dengan Sumber Air Minum Layak"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Proporsi rumah tangga dengan akses berkelanjutan terhadap air minum berkualitas/layak dibandingkan rumah tangga seluruhnya[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Rumah~Tangga~dengan~air~minum~layak}{Rumah~tangga~seluruhnya}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("05. Indikator 3.2.2: Rumah Tangga dengan Fasilitas Tempat Buang Air Sendiri"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Proporsi rumah tangga memiliki fasilitas buang air sendiri (jamban/toilet) sebagai salah satu syarat sanitasi yang layak[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Rumah~Tangga~dengan~fasilitas~buang~air~sendiri}{Rumah~tangga~seluruhnya}\times100\%$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Badan Pusat Statistik (Susenas)[cite: 1].</div>", unsafe_allow_html=True)

            st.markdown("<br><h4 style='color: #0ea5e9; font-weight: 700; margin-bottom: 10px;'>Sub-Pilar 3.3: Keuangan Inklusif</h4>", unsafe_allow_html=True)
            with st.expander("06. Indikator 3.3.1: Rasio Jumlah Rekening DPK terhadap Penduduk Usia Produktif"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Pembagian jumlah total rekening Dana Pihak Ketiga (DPK) perbankan terhadap jumlah penduduk dewasa (usia di atas 15 tahun)[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Total~rekening~DPK~perbankan}{Total~penduduk~dewasa}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Otoritas Jasa Keuangan / Bank Indonesia[cite: 1].</div>", unsafe_allow_html=True)

            with st.expander("07. Indikator 3.3.2: Rasio Kredit Perbankan UMKM"):
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Konsep</span> Perbandingan antara jumlah rekening kredit perbankan yang disalurkan untuk pembiayaan kegiatan UMKM terhadap total rekening kredit perbankan seluruhnya[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Metode</span> $\frac{Jumlah~rekening~kredit~UMKM}{Total~rekening~kredit~perbankan}$[cite: 1].</div>", unsafe_allow_html=True)
                st.markdown(r"<div class='meta-desc'><span class='meta-badge'>Sumber</span> Otoritas Jasa Keuangan / Bank Indonesia[cite: 1].</div>", unsafe_allow_html=True)

    with col_kanan:
        # 4. Rendering Gambar Dinamis dengan Sticky Behavior
        # File gambar dinamakan sesuai pilar: Pilar 1.png, Pilar 2.png, Pilar 3.png
        if pilihan_pilar == "Pilar 1: Pertumbuhan & Perkembangan Ekonomi":
            nama_file_gambar = "Pilar 1.png"
        elif pilihan_pilar == "Pilar 2: Pemerataan Pendapatan & Kemiskinan":
            nama_file_gambar = "Pilar 2.png"
        else:
            nama_file_gambar = "Pilar 3.png"

        try:
            with open(nama_file_gambar, "rb") as img_file:
                encoded_img = base64.b64encode(img_file.read()).decode()
            
            st.markdown(f'''
            <div class="sticky-right-container">
                <img src="data:image/png;base64,{encoded_img}" class="floating-meta-img" alt="{nama_file_gambar}">
            </div>
            ''', unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning(f"⚠️ File '{nama_file_gambar}' tidak ditemukan di folder. Pastikan penamaan file sudah persis sama.")

