import streamlit as st
import os
import requests
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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
# FUNCIÓN PARA OBTENER PRONÓSTICO
# ============================================
def obtener_pronostico(ciudad, api_key, max_reintentos=3):
    """Obtiene pronóstico meteorológico de 5 días para una ciudad"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": ciudad,
        "appid": api_key,
        "units": "metric",
        "lang": "es",
        "cnt": 40  # 40 períodos = 5 días (cada 3 horas)
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
# FUNCIÓN PARA OBTENER PRONÓSTICOS POR HORAS ESPECÍFICAS
# ============================================
def obtener_pronosticos_por_horas(forecast_data, horas=[6, 12, 18, 24, 36, 48]):
    """Obtiene pronósticos para horas específicas (6, 12, 18, 24, 36, 48 horas)"""
    
    if not forecast_data or 'list' not in forecast_data:
        return {}
    
    ahora = datetime.now()
    pronosticos = {}
    
    for horas_futuro in horas:
        fecha_objetivo = ahora + timedelta(hours=horas_futuro)
        # Buscar el pronóstico más cercano a la hora objetivo
        pronostico_cercano = None
        diferencia_minima = float('inf')
        
        for item in forecast_data['list']:
            fecha_item = datetime.strptime(item['dt_txt'], '%Y-%m-%d %H:%M:%S')
            diferencia = abs((fecha_item - fecha_objetivo).total_seconds())
            
            if diferencia < diferencia_minima:
                diferencia_minima = diferencia
                pronostico_cercano = item
        
        if pronostico_cercano:
            pronosticos[f"{horas_futuro}h"] = {
                'fecha': pronostico_cercano['dt_txt'],
                'temperatura': pronostico_cercano['main']['temp'],
                'descripcion': pronostico_cercano['weather'][0]['description'],
                'icono': pronostico_cercano['weather'][0]['icon'],
                'humedad': pronostico_cercano['main']['humidity'],
                'viento': pronostico_cercano['wind']['speed'] * 3.6,
                'probabilidad_lluvia': pronostico_cercano.get('pop', 0) * 100,
                'lluvia_3h': pronostico_cercano.get('rain', {}).get('3h', 0),
                'nieve_3h': pronostico_cercano.get('snow', {}).get('3h', 0),
                'main': pronostico_cercano['weather'][0]['main'].lower(),
                'description': pronostico_cercano['weather'][0]['description'].lower()
            }
    
    return pronosticos

# ============================================
# FUNCIÓN PARA ANALIZAR EVENTOS METEOROLÓGICOS
# ============================================
def analizar_eventos_meteorologicos(forecast_data):
    """Analiza el pronóstico para detectar lluvia, tormenta, granizo y nieve"""
    eventos = {
        'lluvia': False,
        'tormenta': False,
        'granizo': False,
        'nieve': False,
        'probabilidad_lluvia_max': 0,
        'probabilidad_nieve_max': 0,
        'intensidad_lluvia_max': 0,
        'horas_lluvia': [],
        'horas_tormenta': [],
        'horas_nieve': []
    }
    
    if not forecast_data or 'list' not in forecast_data:
        return eventos
    
    for item in forecast_data['list']:
        # Verificar condiciones meteorológicas
        weather_main = item.get('weather', [{}])[0].get('main', '').lower()
        weather_desc = item.get('weather', [{}])[0].get('description', '').lower()
        
        # Detectar lluvia
        if 'rain' in weather_main or 'lluvia' in weather_desc or 'drizzle' in weather_main:
            eventos['lluvia'] = True
            eventos['horas_lluvia'].append(item.get('dt_txt', ''))
            # Obtener intensidad de lluvia si está disponible
            if 'rain' in item and '3h' in item['rain']:
                eventos['intensidad_lluvia_max'] = max(eventos['intensidad_lluvia_max'], item['rain']['3h'])
        
        # Detectar tormenta
        if 'thunderstorm' in weather_main or 'tormenta' in weather_desc:
            eventos['tormenta'] = True
            eventos['horas_tormenta'].append(item.get('dt_txt', ''))
        
        # Detectar granizo (generalmente viene con tormenta)
        if 'hail' in weather_desc or 'granizo' in weather_desc:
            eventos['granizo'] = True
        
        # Detectar nieve
        if 'snow' in weather_main or 'nieve' in weather_desc:
            eventos['nieve'] = True
            eventos['horas_nieve'].append(item.get('dt_txt', ''))
        
        # Probabilidades de precipitación
        if 'pop' in item:  # Probability of Precipitation
            pop = item['pop'] * 100
            if 'rain' in weather_main or 'lluvia' in weather_desc:
                eventos['probabilidad_lluvia_max'] = max(eventos['probabilidad_lluvia_max'], pop)
            if 'snow' in weather_main or 'nieve' in weather_desc:
                eventos['probabilidad_nieve_max'] = max(eventos['probabilidad_nieve_max'], pop)
    
    return eventos

# ============================================
# BÚSQUEDA DE CIUDAD ESPECÍFICA
# ============================================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Búsqueda Personalizada")

ciudad_personalizada = st.sidebar.text_input(
    "Buscar ciudad específica",
    placeholder="Ej: Madrid, ES o New York, US",
    help="Ingresa el nombre de la ciudad y código de país (ej: 'Madrid, ES' o 'New York, US')"
)

buscar_ciudad = st.sidebar.button("🔍 Buscar Ciudad", use_container_width=True)

ciudad_personalizada_data = None
ciudad_personalizada_forecast = None
ciudad_personalizada_pronosticos = {}

if buscar_ciudad and ciudad_personalizada:
    with st.sidebar:
        with st.spinner(f"Buscando {ciudad_personalizada}..."):
            # Obtener datos actuales
            data, error = obtener_clima(ciudad_personalizada, API_KEY)
            if data:
                ciudad_personalizada_data = data
                st.success(f"✅ {data['name']} encontrada")
                
                # Obtener pronóstico
                forecast, forecast_error = obtener_pronostico(ciudad_personalizada, API_KEY)
                if forecast:
                    ciudad_personalizada_forecast = forecast
                    ciudad_personalizada_pronosticos = obtener_pronosticos_por_horas(forecast, horas=[6, 12, 18, 24, 36, 48])
                else:
                    if forecast_error:
                        st.warning(f"⚠️ Pronóstico no disponible: {forecast_error}")
                        st.info("💡 Nota: Algunas API keys gratuitas pueden tener límites en el acceso a pronósticos. Los datos actuales están disponibles.")
            else:
                st.error(f"❌ Error: {error}")

# ============================================
# OBTENER DATOS DE TODAS LAS CIUDADES
# ============================================
st.sidebar.markdown("---")
obtener_datos = st.sidebar.button("🔍 Obtener Datos Meteorológicos", type="primary", use_container_width=True)

# Limpiar datos si se cambió el país
if 'pais_anterior' in st.session_state and st.session_state.pais_anterior != pais_seleccionado:
    if 'weather_data' in st.session_state:
        del st.session_state.weather_data
    if 'errores' in st.session_state:
        del st.session_state.errores

st.session_state.pais_anterior = pais_seleccionado

if obtener_datos or 'weather_data' not in st.session_state:
    
    with st.spinner(f"🌍 Obteniendo datos meteorológicos y pronósticos de {pais_seleccionado}..."):
        weather_data = []
        forecast_data_list = []
        errores = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ciudad in enumerate(ciudades):
            status_text.text(f"Consultando: {ciudad}...")
            
            # Obtener datos actuales
            data, error = obtener_clima(ciudad, API_KEY)
            if data:
                weather_data.append(data)
                
                # Obtener pronóstico
                forecast, forecast_error = obtener_pronostico(ciudad, API_KEY)
                if forecast:
                    forecast_data_list.append(forecast)
                else:
                    forecast_data_list.append(None)
                    # Guardar el error si es relevante para mostrar después
                    if forecast_error and forecast_error not in ["Ciudad no encontrada", "API Key inválida"]:
                        # Solo mostrar advertencia si es un problema de pronóstico específico
                        pass
            else:
                errores.append((ciudad, error))
                forecast_data_list.append(None)
            
            progress_bar.progress((i + 1) / len(ciudades))
        
        progress_bar.empty()
        status_text.empty()
        
        if errores:
            st.warning(f"⚠️ {len(errores)} ciudades no pudieron ser procesadas")
            for ciudad, error in errores:
                st.error(f"❌ {ciudad}: {error}")
        
        if weather_data:
            st.session_state.weather_data = weather_data
            st.session_state.forecast_data = forecast_data_list
            st.session_state.errores = errores
            
            # Verificar cuántos pronósticos se obtuvieron
            pronosticos_obtenidos = sum(1 for f in forecast_data_list if f is not None)
            ciudades_sin_pronostico = len(weather_data) - pronosticos_obtenidos
            
            if pronosticos_obtenidos > 0:
                st.success(f"✅ {len(weather_data)} ciudades procesadas correctamente")
                if ciudades_sin_pronostico > 0:
                    st.warning(f"⚠️ {ciudades_sin_pronostico} ciudades sin pronóstico disponible. Se mostrarán solo datos actuales.")
                    st.info("💡 **Nota sobre pronósticos:**\n"
                           "- Las API keys gratuitas pueden tener límites en el acceso a pronósticos\n"
                           "- Si excedes el límite (429), espera unos minutos\n"
                           "- Algunas ciudades remotas pueden no tener datos de pronóstico\n"
                           "- Los datos actuales siempre estarán disponibles")
            else:
                st.success(f"✅ {len(weather_data)} ciudades procesadas correctamente")
                st.warning("⚠️ **Pronósticos no disponibles**")
                st.info("💡 **Posibles razones:**\n"
                       "- API Key gratuita con límites alcanzados\n"
                       "- Límite de solicitudes excedido (espera unos minutos)\n"
                       "- La API key puede no tener acceso al endpoint de pronóstico\n"
                       "- Problemas temporales de conexión\n\n"
                       "**Los datos actuales están disponibles, pero los pronósticos no se pueden mostrar.**")
        else:
            st.error("❌ No se pudieron obtener datos de ninguna ciudad")
            st.stop()

# Verificar si hay datos en session_state
if 'weather_data' not in st.session_state or not st.session_state.weather_data:
    st.info("👈 Usa el botón en el sidebar para obtener los datos meteorológicos")
    st.stop()

weather_data = st.session_state.weather_data
forecast_data_list = st.session_state.get('forecast_data', [])

# Obtener pronósticos por horas específicas para cada ciudad
pronosticos_por_horas = []
for i, forecast_data in enumerate(forecast_data_list):
    if forecast_data:
        pronosticos = obtener_pronosticos_por_horas(forecast_data, horas=[6, 12, 18, 24, 36, 48])
        pronosticos_por_horas.append(pronosticos)
    else:
        pronosticos_por_horas.append({})

# ============================================
# CREAR DATAFRAME CON DATOS COMPLETOS
# ============================================
columnas = [
    'Ciudad', 'Latitud', 'Longitud', 'Descripción del clima',
    'Temperatura (°C)', 'Sensación térmica (°C)', 'Temperatura mínima (°C)',
    'Temperatura máxima (°C)', 'Humedad (%)', 'Presión (hPa)',
    'Viento (km/h)', 'Dirección del viento (°)', 'Visibilidad (km)',
    'Ícono del clima', 'País',
    'Pronóstico Lluvia', 'Pronóstico Tormenta', 'Pronóstico Granizo', 'Pronóstico Nieve',
    'Prob. Lluvia (%)', 'Prob. Nieve (%)', 'Intensidad Lluvia (mm)'
]

datos = []
eventos_por_ciudad = []

for i, data in enumerate(weather_data):
    direccion_viento = data.get('wind', {}).get('deg', 'N/A')
    visibilidad = data.get('visibility', 0) / 1000 if data.get('visibility') else 'N/A'
    
    # Analizar pronóstico si está disponible
    eventos = {
        'lluvia': False,
        'tormenta': False,
        'granizo': False,
        'nieve': False,
        'probabilidad_lluvia_max': 0,
        'probabilidad_nieve_max': 0,
        'intensidad_lluvia_max': 0
    }
    
    if i < len(forecast_data_list) and forecast_data_list[i]:
        eventos = analizar_eventos_meteorologicos(forecast_data_list[i])
    
    eventos_por_ciudad.append(eventos)
    
    # Determinar texto de pronóstico
    pronosticos = []
    if eventos['lluvia']:
        pronosticos.append('🌧️ Lluvia')
    if eventos['tormenta']:
        pronosticos.append('⛈️ Tormenta')
    if eventos['granizo']:
        pronosticos.append('🧊 Granizo')
    if eventos['nieve']:
        pronosticos.append('❄️ Nieve')
    
    pronostico_texto = ', '.join(pronosticos) if pronosticos else 'Sin eventos'
    
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
        data['sys']['country'],
        'Sí' if eventos['lluvia'] else 'No',
        'Sí' if eventos['tormenta'] else 'No',
        'Sí' if eventos['granizo'] else 'No',
        'Sí' if eventos['nieve'] else 'No',
        f"{eventos['probabilidad_lluvia_max']:.0f}%" if eventos['probabilidad_lluvia_max'] > 0 else 'N/A',
        f"{eventos['probabilidad_nieve_max']:.0f}%" if eventos['probabilidad_nieve_max'] > 0 else 'N/A',
        f"{eventos['intensidad_lluvia_max']:.2f}" if eventos['intensidad_lluvia_max'] > 0 else 'N/A'
    ])

df = pd.DataFrame(datos, columns=columnas)

# ============================================
# MAPA INTERACTIVO (PRIMERO)
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
    eventos = eventos_por_ciudad[idx]
    
    # Determinar color según temperatura
    if temp < 10:
        color = 'blue'
    elif temp < 20:
        color = 'green'
    elif temp < 30:
        color = 'orange'
    else:
        color = 'red'
    
    # Determinar icono según eventos meteorológicos
    if eventos['granizo']:
        icon = 'exclamation-triangle'
        color = 'red'
    elif eventos['tormenta']:
        icon = 'bolt'
        color = 'purple'
    elif eventos['nieve']:
        icon = 'snowflake'
        color = 'lightblue'
    elif eventos['lluvia']:
        icon = 'tint'
        color = 'blue'
    else:
        icon = 'cloud'
    
    # Construir texto de pronóstico para el popup
    pronosticos_popup = []
    if eventos['lluvia']:
        pronosticos_popup.append(f"🌧️ Lluvia ({eventos['probabilidad_lluvia_max']:.0f}%)")
    if eventos['tormenta']:
        pronosticos_popup.append("⛈️ Tormenta")
    if eventos['granizo']:
        pronosticos_popup.append("🧊 Granizo")
    if eventos['nieve']:
        pronosticos_popup.append(f"❄️ Nieve ({eventos['probabilidad_nieve_max']:.0f}%)")
    
    pronostico_texto = '<br>'.join(pronosticos_popup) if pronosticos_popup else 'Sin eventos pronosticados'
    
    popup_html = f"""
    <div style="font-family: Arial; width: 280px;">
        <h3 style="margin: 5px 0; color: #2c3e50;">{row['Ciudad']}</h3>
        <hr style="margin: 5px 0;">
        <p style="margin: 3px 0;"><b>🌡️ Temperatura:</b> {row['Temperatura (°C)']:.1f}°C</p>
        <p style="margin: 3px 0;"><b>🌤️ Estado:</b> {row['Descripción del clima']}</p>
        <p style="margin: 3px 0;"><b>💧 Humedad:</b> {row['Humedad (%)']}%</p>
        <p style="margin: 3px 0;"><b>💨 Viento:</b> {row['Viento (km/h)']:.1f} km/h</p>
        <p style="margin: 3px 0;"><b>📊 Presión:</b> {row['Presión (hPa)']} hPa</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 3px 0;"><b>📅 Pronóstico (5 días):</b></p>
        <p style="margin: 3px 0; color: {'#d32f2f' if eventos['tormenta'] or eventos['granizo'] else '#1976d2'};">
            {pronostico_texto}
        </p>
    </div>
    """
    
    # Tooltip con información de pronóstico
    tooltip_text = f"{row['Ciudad']}: {row['Temperatura (°C)']:.1f}°C"
    if eventos['lluvia'] or eventos['tormenta'] or eventos['granizo'] or eventos['nieve']:
        tooltip_text += " ⚠️"
    
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=color, icon=icon, prefix='fa'),
        tooltip=tooltip_text
    ).add_to(marker_cluster)

# Mostrar mapa en Streamlit
import tempfile
import os

with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
    m.save(tmp_file.name)
    with open(tmp_file.name, 'r', encoding='utf-8') as f:
        map_html = f.read()
    os.unlink(tmp_file.name)

st.components.v1.html(map_html, height=600, scrolling=True)

# ============================================
# ALERTAS DE PRONÓSTICO (SEGUNDO)
# ============================================
st.header("⚠️ Alertas de Pronóstico (Próximos 5 días)")

ciudades_con_eventos = []
for i, eventos in enumerate(eventos_por_ciudad):
    if eventos['lluvia'] or eventos['tormenta'] or eventos['granizo'] or eventos['nieve']:
        ciudades_con_eventos.append((df.iloc[i]['Ciudad'], eventos))

if ciudades_con_eventos:
    for ciudad, eventos in ciudades_con_eventos:
        with st.expander(f"🌍 {ciudad}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if eventos['lluvia']:
                    st.warning(f"🌧️ **Lluvia pronosticada**")
                    if eventos['probabilidad_lluvia_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos['probabilidad_lluvia_max']:.0f}%")
                    if eventos['intensidad_lluvia_max'] > 0:
                        st.write(f"   Intensidad máxima: {eventos['intensidad_lluvia_max']:.2f} mm")
                    if eventos['horas_lluvia']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_lluvia'][:3])}...")
                
                if eventos['tormenta']:
                    st.error(f"⛈️ **Tormenta pronosticada**")
                    if eventos['horas_tormenta']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_tormenta'][:3])}...")
            
            with col2:
                if eventos['granizo']:
                    st.error(f"🧊 **Granizo pronosticado**")
                    st.write("   ⚠️ Precaución: riesgo de granizo")
                
                if eventos['nieve']:
                    st.info(f"❄️ **Nieve pronosticada**")
                    if eventos['probabilidad_nieve_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos['probabilidad_nieve_max']:.0f}%")
                    if eventos['horas_nieve']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_nieve'][:3])}...")
else:
    st.success("✅ No se pronostican eventos meteorológicos significativos en las próximas ciudades")

# ============================================
# CONDICIONES ACTUALES (TERCERO)
# ============================================
st.header("🌤️ Condiciones Actuales")

# Resumen Estadístico
st.subheader("📊 Resumen Estadístico")

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
# CIUDAD PERSONALIZADA (si se buscó)
# ============================================
if ciudad_personalizada_data:
    st.header(f"📍 Ciudad Personalizada: {ciudad_personalizada_data['name']}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌡️ Temperatura", f"{ciudad_personalizada_data['main']['temp']:.1f}°C")
    with col2:
        st.metric("🌤️ Estado", ciudad_personalizada_data['weather'][0]['description'].title())
    with col3:
        st.metric("💧 Humedad", f"{ciudad_personalizada_data['main']['humidity']}%")
    with col4:
        st.metric("💨 Viento", f"{ciudad_personalizada_data['wind']['speed'] * 3.6:.1f} km/h")
    
    # Pronósticos por horas para ciudad personalizada
    if ciudad_personalizada_pronosticos:
        st.subheader("⏰ Pronóstico por Horas")
        horas = ['6h', '12h', '18h', '24h', '36h', '48h']
        cols = st.columns(6)
        
        for i, hora in enumerate(horas):
            with cols[i]:
                if hora in ciudad_personalizada_pronosticos:
                    p = ciudad_personalizada_pronosticos[hora]
                    
                    # Determinar emoji según condiciones
                    emoji = "☀️"
                    color_bg = "#E8F5E9"
                    
                    if 'thunderstorm' in p['main'] or 'tormenta' in p['description']:
                        emoji = "⛈️"
                        color_bg = "#FFEBEE"
                    elif 'rain' in p['main'] or 'lluvia' in p['description'] or p['lluvia_3h'] > 0:
                        emoji = "🌧️"
                        color_bg = "#E3F2FD"
                    elif 'snow' in p['main'] or 'nieve' in p['description'] or p['nieve_3h'] > 0:
                        emoji = "❄️"
                        color_bg = "#E1F5FE"
                    elif 'hail' in p['description'] or 'granizo' in p['description']:
                        emoji = "🧊"
                        color_bg = "#FFF3E0"
                    elif 'cloud' in p['main']:
                        emoji = "☁️"
                        color_bg = "#F5F5F5"
                    
                    st.markdown(
                        f"""
                        <div style="background-color: {color_bg}; padding: 10px; border-radius: 8px; text-align: center;">
                            <h4 style="margin: 5px 0;">{hora}</h4>
                            <p style="font-size: 24px; margin: 5px 0;">{emoji}</p>
                            <p style="margin: 3px 0; font-weight: bold;">{p['temperatura']:.1f}°C</p>
                            <p style="margin: 3px 0; font-size: 0.85em;">{p['descripcion'].title()}</p>
                            <p style="margin: 3px 0; font-size: 0.8em;">💧 {p['humedad']}%</p>
                            <p style="margin: 3px 0; font-size: 0.8em;">💨 {p['viento']:.1f} km/h</p>
                            {f"<p style='margin: 3px 0; font-size: 0.8em; color: #1976d2;'>🌧️ {p['probabilidad_lluvia']:.0f}%</p>" if p['probabilidad_lluvia'] > 0 else ""}
                            {f"<p style='margin: 3px 0; font-size: 0.8em; color: #1976d2;'>💧 {p['lluvia_3h']:.1f}mm</p>" if p['lluvia_3h'] > 0 else ""}
                            {f"<p style='margin: 3px 0; font-size: 0.8em; color: #64B5F6;'>❄️ {p['nieve_3h']:.1f}mm</p>" if p['nieve_3h'] > 0 else ""}
                            <p style="margin: 5px 0; font-size: 0.75em; color: #666;">{p['fecha'][:16]}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    # Analizar eventos para ciudad personalizada
    if ciudad_personalizada_forecast:
        eventos_personalizada = analizar_eventos_meteorologicos(ciudad_personalizada_forecast)
        
        if eventos_personalizada['lluvia'] or eventos_personalizada['tormenta'] or eventos_personalizada['granizo'] or eventos_personalizada['nieve']:
            st.subheader("⚠️ Alertas de Pronóstico")
            alert_cols = st.columns(2)
            
            with alert_cols[0]:
                if eventos_personalizada['lluvia']:
                    st.warning(f"🌧️ **Lluvia pronosticada**")
                    if eventos_personalizada['probabilidad_lluvia_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos_personalizada['probabilidad_lluvia_max']:.0f}%")
                    if eventos_personalizada['intensidad_lluvia_max'] > 0:
                        st.write(f"   Intensidad máxima: {eventos_personalizada['intensidad_lluvia_max']:.2f} mm")
                
                if eventos_personalizada['tormenta']:
                    st.error(f"⛈️ **Tormenta pronosticada**")
            
            with alert_cols[1]:
                if eventos_personalizada['granizo']:
                    st.error(f"🧊 **Granizo pronosticado**")
                    st.write("   ⚠️ Precaución: riesgo de granizo")
                
                if eventos_personalizada['nieve']:
                    st.info(f"❄️ **Nieve pronosticada**")
                    if eventos_personalizada['probabilidad_nieve_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos_personalizada['probabilidad_nieve_max']:.0f}%")
    
    st.markdown("---")

# ============================================
# PRONÓSTICOS POR HORAS ESPECÍFICAS
# ============================================
st.header("⏰ Pronósticos por Horas (6, 12, 18, 24, 36, 48 horas)")

# Verificar si hay pronósticos disponibles
pronosticos_disponibles = any(pronosticos_por_horas) and any(p for p in pronosticos_por_horas if p)

if not pronosticos_disponibles:
    st.warning("⚠️ **Pronósticos no disponibles**")
    st.info("💡 Los pronósticos no están disponibles en este momento. Posibles razones:\n"
           "- API Key gratuita con límites alcanzados\n"
           "- Límite de solicitudes excedido\n"
           "- Problemas temporales de conexión\n\n"
           "Los datos actuales están disponibles arriba.")
else:
    for idx, row in df.iterrows():
        ciudad = row['Ciudad']
        pronosticos = pronosticos_por_horas[idx] if idx < len(pronosticos_por_horas) else {}
        
        if pronosticos:
        with st.expander(f"🌍 {ciudad}", expanded=False):
            horas = ['6h', '12h', '18h', '24h', '36h', '48h']
            cols = st.columns(6)
            
            for i, hora in enumerate(horas):
                with cols[i]:
                    if hora in pronosticos:
                        p = pronosticos[hora]
                        
                        # Determinar emoji según condiciones
                        emoji = "☀️"
                        color_bg = "#E8F5E9"  # Verde claro
                        
                        if 'thunderstorm' in p['main'] or 'tormenta' in p['description']:
                            emoji = "⛈️"
                            color_bg = "#FFEBEE"  # Rojo claro
                        elif 'rain' in p['main'] or 'lluvia' in p['description'] or p['lluvia_3h'] > 0:
                            emoji = "🌧️"
                            color_bg = "#E3F2FD"  # Azul claro
                        elif 'snow' in p['main'] or 'nieve' in p['description'] or p['nieve_3h'] > 0:
                            emoji = "❄️"
                            color_bg = "#E1F5FE"  # Azul muy claro
                        elif 'hail' in p['description'] or 'granizo' in p['description']:
                            emoji = "🧊"
                            color_bg = "#FFF3E0"  # Naranja claro
                        elif 'cloud' in p['main']:
                            emoji = "☁️"
                            color_bg = "#F5F5F5"  # Gris claro
                        
                        st.markdown(
                            f"""
                            <div style="background-color: {color_bg}; padding: 10px; border-radius: 8px; text-align: center;">
                                <h4 style="margin: 5px 0;">{hora}</h4>
                                <p style="font-size: 24px; margin: 5px 0;">{emoji}</p>
                                <p style="margin: 3px 0; font-weight: bold;">{p['temperatura']:.1f}°C</p>
                                <p style="margin: 3px 0; font-size: 0.85em;">{p['descripcion'].title()}</p>
                                <p style="margin: 3px 0; font-size: 0.8em;">💧 {p['humedad']}%</p>
                                <p style="margin: 3px 0; font-size: 0.8em;">💨 {p['viento']:.1f} km/h</p>
                                {f"<p style='margin: 3px 0; font-size: 0.8em; color: #1976d2;'>🌧️ {p['probabilidad_lluvia']:.0f}%</p>" if p['probabilidad_lluvia'] > 0 else ""}
                                {f"<p style='margin: 3px 0; font-size: 0.8em; color: #1976d2;'>💧 {p['lluvia_3h']:.1f}mm</p>" if p['lluvia_3h'] > 0 else ""}
                                {f"<p style='margin: 3px 0; font-size: 0.8em; color: #64B5F6;'>❄️ {p['nieve_3h']:.1f}mm</p>" if p['nieve_3h'] > 0 else ""}
                                <p style="margin: 5px 0; font-size: 0.75em; color: #666;">{p['fecha'][:16]}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("N/D")
        else:
            with st.expander(f"🌍 {ciudad}", expanded=False):
                st.warning("⚠️ No hay datos de pronóstico disponibles para esta ciudad")
                st.info("💡 Esto puede deberse a límites de la API o problemas temporales. Los datos actuales están disponibles arriba.")

# ============================================
# ALERTAS DE PRONÓSTICO
# ============================================
st.header("⚠️ Alertas de Pronóstico (Próximos 5 días)")

ciudades_con_eventos = []
for i, eventos in enumerate(eventos_por_ciudad):
    if eventos['lluvia'] or eventos['tormenta'] or eventos['granizo'] or eventos['nieve']:
        ciudades_con_eventos.append((df.iloc[i]['Ciudad'], eventos))

if ciudades_con_eventos:
    for ciudad, eventos in ciudades_con_eventos:
        with st.expander(f"🌍 {ciudad}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if eventos['lluvia']:
                    st.warning(f"🌧️ **Lluvia pronosticada**")
                    if eventos['probabilidad_lluvia_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos['probabilidad_lluvia_max']:.0f}%")
                    if eventos['intensidad_lluvia_max'] > 0:
                        st.write(f"   Intensidad máxima: {eventos['intensidad_lluvia_max']:.2f} mm")
                    if eventos['horas_lluvia']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_lluvia'][:3])}...")
                
                if eventos['tormenta']:
                    st.error(f"⛈️ **Tormenta pronosticada**")
                    if eventos['horas_tormenta']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_tormenta'][:3])}...")
            
            with col2:
                if eventos['granizo']:
                    st.error(f"🧊 **Granizo pronosticado**")
                    st.write("   ⚠️ Precaución: riesgo de granizo")
                
                if eventos['nieve']:
                    st.info(f"❄️ **Nieve pronosticada**")
                    if eventos['probabilidad_nieve_max'] > 0:
                        st.write(f"   Probabilidad máxima: {eventos['probabilidad_nieve_max']:.0f}%")
                    if eventos['horas_nieve']:
                        st.write(f"   Horarios: {', '.join(eventos['horas_nieve'][:3])}...")
else:
    st.success("✅ No se pronostican eventos meteorológicos significativos en las próximas ciudades")

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
    eventos = eventos_por_ciudad[idx]
    
    # Determinar color según temperatura
    if temp < 10:
        color = 'blue'
    elif temp < 20:
        color = 'green'
    elif temp < 30:
        color = 'orange'
    else:
        color = 'red'
    
    # Determinar icono según eventos meteorológicos
    if eventos['granizo']:
        icon = 'exclamation-triangle'
        color = 'red'
    elif eventos['tormenta']:
        icon = 'bolt'
        color = 'purple'
    elif eventos['nieve']:
        icon = 'snowflake'
        color = 'lightblue'
    elif eventos['lluvia']:
        icon = 'tint'
        color = 'blue'
    else:
        icon = 'cloud'
    
    # Construir texto de pronóstico para el popup
    pronosticos_popup = []
    if eventos['lluvia']:
        pronosticos_popup.append(f"🌧️ Lluvia ({eventos['probabilidad_lluvia_max']:.0f}%)")
    if eventos['tormenta']:
        pronosticos_popup.append("⛈️ Tormenta")
    if eventos['granizo']:
        pronosticos_popup.append("🧊 Granizo")
    if eventos['nieve']:
        pronosticos_popup.append(f"❄️ Nieve ({eventos['probabilidad_nieve_max']:.0f}%)")
    
    pronostico_texto = '<br>'.join(pronosticos_popup) if pronosticos_popup else 'Sin eventos pronosticados'
    
    popup_html = f"""
    <div style="font-family: Arial; width: 280px;">
        <h3 style="margin: 5px 0; color: #2c3e50;">{row['Ciudad']}</h3>
        <hr style="margin: 5px 0;">
        <p style="margin: 3px 0;"><b>🌡️ Temperatura:</b> {row['Temperatura (°C)']:.1f}°C</p>
        <p style="margin: 3px 0;"><b>🌤️ Estado:</b> {row['Descripción del clima']}</p>
        <p style="margin: 3px 0;"><b>💧 Humedad:</b> {row['Humedad (%)']}%</p>
        <p style="margin: 3px 0;"><b>💨 Viento:</b> {row['Viento (km/h)']:.1f} km/h</p>
        <p style="margin: 3px 0;"><b>📊 Presión:</b> {row['Presión (hPa)']} hPa</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 3px 0;"><b>📅 Pronóstico (5 días):</b></p>
        <p style="margin: 3px 0; color: {'#d32f2f' if eventos['tormenta'] or eventos['granizo'] else '#1976d2'};">
            {pronostico_texto}
        </p>
    </div>
    """
    
    # Tooltip con información de pronóstico
    tooltip_text = f"{row['Ciudad']}: {row['Temperatura (°C)']:.1f}°C"
    if eventos['lluvia'] or eventos['tormenta'] or eventos['granizo'] or eventos['nieve']:
        tooltip_text += " ⚠️"
    
    folium.Marker(
        location=[row['Latitud'], row['Longitud']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=color, icon=icon, prefix='fa'),
        tooltip=tooltip_text
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

