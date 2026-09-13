import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd

# -----------------------------------------------------------------------------
# 2. FUNGSI PEMUATAN DATA (DENGAN GEOPANDAS DISSOLVE)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # --- 1. BACA DATA EXCEL ---
    df_provinsi = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Provinsi")
    df_kabkota = pd.read_excel("Data_Dummy_IPEI.xlsx", sheet_name="Kab_Kota")

    # Bersihkan kode dan ubah ke numerik
    for df in [df_provinsi, df_kabkota]:
        df['kodedaerah'] = df['kodedaerah'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        kolom_indikator = ['ipei', 'pilar1', 'pilar2', 'pilar3', 'sp11', 'sp12', 'sp13', 'sp21', 'sp22', 'sp31', 'sp32', 'sp33']
        for col in kolom_indikator:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- 2. BACA JSON KABUPATEN & BERSIHKAN ---
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
                "id": kode_kab, # ID untuk pemetaan level Kabupaten
                "properties": {"kode_provinsi": kode_prov, "namadaerah": item.get('name', '')},  
                "geometry": actual_geom
            })

    # Ini adalah GeoJSON murni untuk Kabupaten (garis kecil-kecil)
    geojson_kabkota = {"type": "FeatureCollection", "features": fitur_kabkota}

    # --- 3. BIKIN PETA PROVINSI (MELEBUR BATAS KABUPATEN) ---
    # Ubah geojson kabupaten ke GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(geojson_kabkota)
    
    # KUNCI UTAMA: Leburkan poligon berdasarkan 'kode_provinsi'
    gdf_prov = gdf.dissolve(by='kode_provinsi').reset_index()
    
    # Ubah kembali GeoDataFrame hasil peleburan ke format JSON
    geojson_prov_str = gdf_prov.to_json()
    geojson_provinsi = json.loads(geojson_prov_str)

    # Sesuaikan 'id' pada geojson_provinsi agar Plotly bisa membacanya
    for feature in geojson_provinsi['features']:
        feature['id'] = feature['properties']['kode_provinsi']

    return df_provinsi, df_kabkota, geojson_provinsi, geojson_kabkota

# ---> PANGGIL FUNGSINYA DI SINI <---
df_provinsi, df_kabkota, geojson_provinsi, geojson_kabkota = load_data()
