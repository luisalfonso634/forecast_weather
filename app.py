import streamlit as st
import os
import requests
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import urllib3
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la página
st.set_page_config(
    page_title="🌤️ Visualizador de Clima",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🌤️ Visualizador de Clima con OpenWeatherMap API")
st.markdown("---")

# ============================================
# CONFIGURACIÓN DE API KEY
# ============================================
st.sidebar.header("🔐 Configuración")

# Opción 1: Variable de entorno
api_key_env = os.getenv('OPENWEATHER_API_KEY')

# Opción 2: Input en sidebar
api_key_input = st.sidebar.text_input(
    "API Key de OpenWeatherMap",
    type="password",
    help="Ingresa tu API key o configúrala como variable de entorno OPENWEATHER_API_KEY",
    value=api_key_env if api_key_env else ""
)

# Determinar qué API key usar
API_KEY = api_key_input if api_key_input else api_key_env

if not API_KEY:
    st.error("⚠️ **ERROR: API Key no configurada**")
    st.info(
        "Por favor configura tu API Key de OpenWeatherMap:\n\n"
        "**Opción 1:** Ingresa tu API key en el sidebar (izquierda)\n\n"
        "**Opción 2:** Configura como variable de entorno:\n"
        "- Windows: `set OPENWEATHER_API_KEY=tu_api_key`\n"
        "- Linux/Mac: `export OPENWEATHER_API_KEY=tu_api_key`\n\n"
        "Obtén tu API key gratuita en: https://openweathermap.org/api"
    )
    st.stop()

# ============================================
# CONFIGURACIÓN DE CIUDADES
# ============================================
PAISES_CONFIG = {
    'Argentina': [
        "Buenos Aires, AR", "Cordoba, AR", "Rosario, AR", "Mendoza, AR",
        "San Miguel de Tucuman, AR", "La Plata, AR", "Mar del Plata, AR",
        "Salta, AR", "Santa Fe, AR", "San Luis, AR"
    ],
    'Venezuela': [
        "Caracas, VE", "Maracaibo, VE", "Valencia, VE", "Barquisimeto, VE"
    ],
    'Colombia': [
        "Bogota, CO", "Medellin, CO", "Cali, CO", "Barranquilla, CO"
    ],
    'Chile': [
        "Santiago, CL", "Valparaiso, CL", "Concepcion, CL", "La Serena, CL"
    ],
    'Peru': [
        "Lima, PE", "Arequipa, PE", "Trujillo, PE", "Cusco, PE"
    ]
}

st.sidebar.header("🌍 Selección de País")
pais_seleccionado = st.sidebar.selectbox(
    "Selecciona un país",
    options=list(PAISES_CONFIG.keys()),
    index=0
)

ciudades = PAISES_CONFIG.get(pais_seleccionado, PAISES_CONFIG['Argentina'])

st.sidebar.info(f"📊 Se consultarán {len(ciudades)} ciudades de {pais_seleccionado}")

# ============================================
# FUNCIÓN PARA OBTENER DATOS METEOROLÓGICOS
# ============================================
def obtener_clima(ciudad, api_key, max_reintentos=3):
    """Obtiene datos meteorológicos de una ciudad con manejo de errores"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": ciudad,
        "appid": api_key,
        "units": "metric",
        "lang": "es"
    }
    
    for intento in range(max_reintentos):
        try:
            try:
                response = requests.get(url, params=params, timeout=10)
            except requests.exceptions.SSLError:
                response = requests.get(url, params=params, timeout=10, verify=False)
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 401:
                return None, "API Key inválida"
            elif response.status_code == 404:
                return None, f"Ciudad '{ciudad}' no encontrada"
            elif response.status_code == 429:
                return None, "Límite de solicitudes excedido"
            else:
                if intento < max_reintentos - 1:
                    continue
                return None, f"Error {response.status_code}"
                
        except requests.exceptions.Timeout:
            if intento < max_reintentos - 1:
                continue
            return None, "Timeout en la solicitud"
        except requests.exceptions.RequestException as e:
            return None, f"Error de conexión: {str(e)}"
    
    return None, "Error después de múltiples intentos"

# ============================================
# OBTENER DATOS DE TODAS LAS CIUDADES
# ============================================
obtener_datos = st.sidebar.button("🔍 Obtener Datos Meteorológicos", type="primary", use_container_width=True)

# Limpiar datos si se cambió el país
if 'pais_anterior' in st.session_state and st.session_state.pais_anterior != pais_seleccionado:
    if 'weather_data' in st.session_state:
        del st.session_state.weather_data
    if 'errores' in st.session_state:
        del st.session_state.errores

st.session_state.pais_anterior = pais_seleccionado

if obtener_datos or 'weather_data' not in st.session_state:
    
    with st.spinner(f"🌍 Obteniendo datos meteorológicos de {pais_seleccionado}..."):
        weather_data = []
        errores = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ciudad in enumerate(ciudades):
            status_text.text(f"Consultando: {ciudad}...")
            data, error = obtener_clima(ciudad, API_KEY)
            if data:
                weather_data.append(data)
            else:
                errores.append((ciudad, error))
            progress_bar.progress((i + 1) / len(ciudades))
        
        progress_bar.empty()
        status_text.empty()
        
        if errores:
            st.warning(f"⚠️ {len(errores)} ciudades no pudieron ser procesadas")
            for ciudad, error in errores:
                st.error(f"❌ {ciudad}: {error}")
        
        if weather_data:
            st.session_state.weather_data = weather_data
            st.session_state.errores = errores
            st.success(f"✅ {len(weather_data)} ciudades procesadas correctamente")
        else:
            st.error("❌ No se pudieron obtener datos de ninguna ciudad")
            st.stop()

# Verificar si hay datos en session_state
if 'weather_data' not in st.session_state or not st.session_state.weather_data:
    st.info("👈 Usa el botón en el sidebar para obtener los datos meteorológicos")
    st.stop()

weather_data = st.session_state.weather_data

# ============================================
# CREAR DATAFRAME CON DATOS COMPLETOS
# ============================================
columnas = [
    'Ciudad', 'Latitud', 'Longitud', 'Descripción del clima',
    'Temperatura (°C)', 'Sensación térmica (°C)', 'Temperatura mínima (°C)',
    'Temperatura máxima (°C)', 'Humedad (%)', 'Presión (hPa)',
    'Viento (km/h)', 'Dirección del viento (°)', 'Visibilidad (km)',
    'Ícono del clima', 'País'
]

datos = []

for data in weather_data:
    direccion_viento = data.get('wind', {}).get('deg', 'N/A')
    visibilidad = data.get('visibility', 0) / 1000 if data.get('visibility') else 'N/A'
    
    datos.append([
        data['name'],
        data['coord']['lat'],
        data['coord']['lon'],
        data['weather'][0]['description'],
        data['main']['temp'],
        data['main'].get('feels_like', 'N/A'),
        data['main']['temp_min'],
        data['main']['temp_max'],
        data['main']['humidity'],
        data['main']['pressure'],
        data['wind']['speed'] * 3.6,
        direccion_viento,
        visibilidad,
        data['weather'][0]['icon'],
        data['sys']['country']
    ])

df = pd.DataFrame(datos, columns=columnas)

# ============================================
# MOSTRAR RESUMEN ESTADÍSTICO
# ============================================
st.header("📊 Resumen Estadístico")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🌡️ Temp. Promedio", f"{df['Temperatura (°C)'].mean():.1f}°C")
with col2:
    st.metric("❄️ Temp. Mínima", f"{df['Temperatura (°C)'].min():.1f}°C")
with col3:
    st.metric("🔥 Temp. Máxima", f"{df['Temperatura (°C)'].max():.1f}°C")
with col4:
    st.metric("💧 Humedad Prom.", f"{df['Humedad (%)'].mean():.1f}%")
with col5:
    st.metric("💨 Viento Prom.", f"{df['Viento (km/h)'].mean():.1f} km/h")

# ============================================
# TABLA DE DATOS
# ============================================
st.header("📋 Datos Completos")
st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================
# MAPA INTERACTIVO
# ============================================
st.header("🗺️ Mapa Interactivo")

lat_centro = df['Latitud'].mean()
lon_centro = df['Longitud'].mean()

m = folium.Map(
    location=[lat_centro, lon_centro],
    zoom_start=6,
    tiles='OpenStreetMap'
)

# Capa de calor
heat_data = [[row['Latitud'], row['Longitud'], row['Temperatura (°C)']] 
             for idx, row in df.iterrows()]
HeatMap(heat_data, radius=25, blur=15, max_zoom=1).add_to(m)

# Marcadores
marker_cluster = MarkerCluster().add_to(m)

for idx, row in df.iterrows():
    temp = row['Temperatura (°C)']
    if temp < 10:
        color = 'blue'
    elif temp < 20:
        color = 'green'
    elif temp < 30:
        color = 'orange'
    else:
        color = 'red'
    
    popup_html = f"""
    <div style="font-family: Arial; width: 250px;">
        <h3 style="margin: 5px 0; color: #2c3e50;">{row['Ciudad']}</h3>
        <hr style="margin: 5px 0;">
        <p style="margin: 3px 0;"><b>🌡️ Temperatura:</b> {row['Temperatura (°C)']:.1f}°C</p>
        <p style="margin: 3px 0;"><b>🌤️ Estado:</b> {row['Descripción del clima']}</p>
        <p style="margin: 3px 0;"><b>💧 Humedad:</b> {row['Humedad (%)']}%</p>
        <p style="margin: 3px 0;"><b>💨 Viento:</b> {row['Viento (km/h)']:.1f} km/h</p>
        <p style="margin: 3px 0;"><b>📊 Presión:</b> {row['Presión (hPa)']} hPa</p>
        <p style="margin: 3px 0;"><b>👁️ Visibilidad:</b> {row['Visibilidad (km)']} km</p>
    </div>
    """
    
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=color, icon='cloud', prefix='fa'),
        tooltip=f"{row['Ciudad']}: {row['Temperatura (°C)']:.1f}°C"
    ).add_to(marker_cluster)

# Mostrar mapa en Streamlit
# Guardar el mapa como HTML temporal y mostrarlo
import tempfile
import os

with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
    m.save(tmp_file.name)
    with open(tmp_file.name, 'r', encoding='utf-8') as f:
        map_html = f.read()
    os.unlink(tmp_file.name)

st.components.v1.html(map_html, height=600, scrolling=True)

# ============================================
# GRÁFICO DE ISOTERMAS
# ============================================
if len(df) >= 3:
    st.header("📈 Mapa de Isotermas")
    
    posiciones = np.array([(lat, lon) for lat, lon in zip(df['Latitud'], df['Longitud'])])
    temperaturas = df['Temperatura (°C)'].values
    
    lat_min, lat_max = df['Latitud'].min(), df['Latitud'].max()
    lon_min, lon_max = df['Longitud'].min(), df['Longitud'].max()
    
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    lat_min -= lat_range * 0.1
    lat_max += lat_range * 0.1
    lon_min -= lon_range * 0.1
    lon_max += lon_range * 0.1
    
    grid_x, grid_y = np.mgrid[lat_min:lat_max:100j, lon_min:lon_max:100j]
    grid_z = griddata(posiciones, temperaturas, (grid_x, grid_y), method='cubic')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    contour = ax.contourf(grid_x, grid_y, grid_z, levels=20, cmap='RdYlBu_r')
    plt.colorbar(contour, ax=ax, label='Temperatura (°C)')
    
    scatter = ax.scatter(df['Longitud'], df['Latitud'], 
                        c=df['Temperatura (°C)'], 
                        s=100, edgecolors='black', 
                        linewidth=2, cmap='RdYlBu_r', zorder=5)
    
    for idx, row in df.iterrows():
        ax.annotate(row['Ciudad'], 
                   (row['Longitud'], row['Latitud']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, fontweight='bold')
    
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    ax.set_title(f'Mapa de Isotermas - {pais_seleccionado}\n{datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    st.pyplot(fig)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Desarrollado con ❤️ usando Python, Streamlit, OpenWeatherMap API, Folium y Matplotlib</p>
        <p>Última actualización: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    unsafe_allow_html=True
)

