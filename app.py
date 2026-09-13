import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd

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
# 2. FUNGSI PEMUATAN DATA (OPTIMASI KECEPATAN & AUTO-ZOOM)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # --- A. BACA DATA EXCEL ---
    df_provinsi = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Provinsi")
    df_kabkota = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Kab_Kota")

    kolom_indikator = ['ipei', 'pilar1', 'pilar2', 'pilar3', 'sp11', 'sp12', 'sp13', 'sp21', 'sp22', 'sp31', 'sp32', 'sp33']
    for df_tmp in [df_provinsi, df_kabkota]:
        df_tmp['kodedaerah'] = df_tmp['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        for col in kolom_indikator:
            if col in df_tmp.columns:
                df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')

    # --- B. BACA FILE PETA BPS ---
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
                "properties": {"kode_provinsi": kode_prov, "namadaerah": item.get('name', '')},  
                "geometry": actual_geom
            })

    geojson_kabkota = {"type": "FeatureCollection", "features": fitur_kabkota}

    # --- C. OPTIMASI GEOPANDAS (SIMPLIFIKASI & DISSOLVE) ---
    gdf_kab = gpd.GeoDataFrame.from_features(geojson_kabkota)
    
    # ⚡ PERBAIKAN LOADING: Menyederhanakan poligon agar loading peta 10x lebih cepat
    gdf_kab['geometry'] = gdf_kab['geometry'].simplify(tolerance=0.005, preserve_topology=True)
    
    # Leburkan batas kabupaten menjadi provinsi
    gdf_prov = gdf_kab.dissolve(by='kode_provinsi').reset_index()

    # Ubah GDF ke String JSON, lalu jadikan Dictionary JSON agar bisa dibaca Plotly
    geojson_prov_dict = json.loads(gdf_prov.to_json())
    for feature in geojson_prov_dict['features']:
        feature['id'] = feature['properties']['kode_provinsi'] # Set ID untuk provinsi

    geojson_kab_dict = json.loads(gdf_kab.to_json())

    # Return juga Geodataframe-nya (gdf_prov) agar kita bisa pakai untuk menghitung ZOOM
    return df_provinsi, df_kabkota, geojson_prov_dict, geojson_kab_dict, gdf_prov

# Eksekusi Cache Data
df_provinsi, df_kabkota, geojson_provinsi, geojson_kabkota, gdf_provinsi = load_data()


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

    # =========================================================
    # TAMPILAN AWAL (NASIONAL)
    # =========================================================
    if st.session_state.tingkat_peta == "nasional":
        st.info("💡 **Petunjuk:** Klik pada salah satu area Provinsi di peta untuk melihat detail Kabupaten/Kota di dalamnya.")
        
        df_prov_filtered = df_provinsi[df_provinsi['tahun'].astype(int) == selected_year].reset_index(drop=True)

        if not df_prov_filtered.empty:
            fig_nasional = px.choropleth_map(
                df_prov_filtered,
                geojson=geojson_provinsi, 
                locations='kodedaerah',            
                color=selected_kolom,              
                color_continuous_scale="RdYlGn",  
                map_style="carto-positron",        
                opacity=0.8,
                hover_name='namadaerah',
                labels={selected_kolom: selected_label}
            )

            # Atur posisi zoom default awal Indonesia
            fig_nasional.update_layout(
                map=dict(center={"lat": -0.789, "lon": 113.921}, zoom=4), # Mengatur tampilan awal
                margin={"r":0,"t":0,"l":0,"b":0},
                coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
            )

            event = st.plotly_chart(fig_nasional, use_container_width=True, on_select="rerun", selection_mode="points", key="peta_awal")
            
            if event and event.get("selection") and event["selection"].get("points"):
                st.session_state.provinsi_terpilih = event["selection"]["points"][0]["location"]
                st.session_state.tingkat_peta = "provinsi"
                st.rerun()

    # =========================================================
    # TAMPILAN ZOOM (KABUPATEN DI DALAM 1 PROVINSI)
    # =========================================================
    elif st.session_state.tingkat_peta == "provinsi":
        st.button("⬅️ Kembali ke Peta Nasional", on_click=reset_peta)
        
        df_kab_filtered = df_kabkota[df_kabkota['tahun'].astype(int) == selected_year].copy()
        df_kab_filtered['kode_prov'] = df_kab_filtered['kodedaerah'].astype(str).str[:2] + "00"
        df_kab_zoom = df_kab_filtered[df_kab_filtered['kode_prov'] == str(st.session_state.provinsi_terpilih)].reset_index(drop=True)
        
        if not df_kab_zoom.empty:
            st.markdown("### Detail Kabupaten/Kota")

            fig_zoom = px.choropleth_map(
                df_kab_zoom,
                geojson=geojson_kabkota, 
                locations='kodedaerah',            
                color=selected_kolom,              
                color_continuous_scale="RdYlGn",  
                map_style="carto-positron",        
                opacity=0.8,
                hover_name='namadaerah',
                labels={selected_kolom: selected_label}
            )

            # 🎯 KUNCI AUTO-ZOOM BARU: Hitung koordinat batas provinsi menggunakan Geopandas
            batas_provinsi = gdf_provinsi[gdf_provinsi['kode_provinsi'] == st.session_state.provinsi_terpilih]
            if not batas_provinsi.empty:
                minx, miny, maxx, maxy = batas_provinsi.total_bounds
                
                # Paksa Plotly untuk zoom ke kotak koordinat provinsi tersebut
                fig_zoom.update_layout(
                    map=dict(bounds={"west": minx, "east": maxx, "south": miny, "north": maxy}),
                    mapbox=dict(bounds={"west": minx, "east": maxx, "south": miny, "north": maxy}) # Untuk kompabilitas Plotly lama
                )

            fig_zoom.update_layout(
                margin={"r":0,"t":0,"l":0,"b":0},
                coloraxis_colorbar=dict(title="Nilai", yanchor="top", y=1, ticks="outside")
            )

            st.plotly_chart(fig_zoom, use_container_width=True, key="peta_zoom")

# -----------------------------------------------------------------------------
# MENU LAIN (ANALISIS & TENTANG IPEI) TETAP SAMA DENGAN SEBELUMNYA
# -----------------------------------------------------------------------------
elif menu == "📈 Analisis Pilar & Tren":
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

elif menu == "ℹ️ Tentang IPEI":
    st.title("Tentang Indeks Pembangunan Ekonomi Inklusif")
    st.markdown("**Indeks Pembangunan Ekonomi Inklusif (IPEI)** adalah instrumen pengukuran untuk melihat seberapa inklusif pertumbuhan ekonomi di suatu wilayah.")
