# 🌤️ Visualizador de Clima con OpenWeatherMap API

Un proyecto completo para visualizar datos meteorológicos de múltiples ciudades usando la API de OpenWeatherMap, con mapas interactivos y gráficos de isotermas.

## ✨ Características

- 🔐 **Seguridad**: API Key configurable mediante variable de entorno
- 🌍 **Versatilidad**: Soporte para múltiples países (Argentina, Venezuela, Colombia, Chile, Perú)
- 📊 **Métricas completas**: Temperatura, humedad, viento, presión, visibilidad y más
- 🗺️ **Visualizaciones avanzadas**: Mapas interactivos con capa de calor y marcadores agrupados
- 📈 **Gráficos de isotermas**: Visualización de distribución de temperatura
- ⚡ **Manejo robusto de errores**: Reintentos automáticos y validaciones
- 🎨 **Interfaz mejorada**: Popups informativos y colores según temperatura

## 🚀 Instalación

### Requisitos

```bash
pip install requests pandas folium numpy scipy matplotlib
```

### Configuración de API Key

**Opción 1: Variable de entorno (Recomendado para producción)**

Windows:
```cmd
set OPENWEATHER_API_KEY=tu_api_key_aqui
```

Linux/Mac:
```bash
export OPENWEATHER_API_KEY=tu_api_key_aqui
```

**⚠️ IMPORTANTE**: El código NO incluye una API key por defecto por razones de seguridad. Debes configurarla como variable de entorno.

**Obtén tu API key gratuita en**: https://openweathermap.org/api

## 📖 Uso

### Opción 1: Aplicación Streamlit (Recomendado) 🌐

La forma más fácil de usar el proyecto es mediante la aplicación web interactiva:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar API Key (Windows PowerShell)
$env:OPENWEATHER_API_KEY = "tu_api_key_aqui"

# Ejecutar la aplicación
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

**Características de la app:**
- ✅ Interfaz web interactiva y moderna
- ✅ Selección de país desde el sidebar
- ✅ Mapa interactivo con marcadores y capa de calor
- ✅ Gráficos de isotermas
- ✅ Tabla de datos completa
- ✅ Resumen estadístico en tiempo real

### Opción 2: Jupyter Notebook 📓

1. Abre el notebook `API_Weather_VERSION_2.ipynb`
2. Configura tu API Key como variable de entorno
3. Ejecuta las celdas en orden
4. Selecciona el país cambiando `PAIS_SELECCIONADO` en la celda de configuración
5. Los resultados se guardarán automáticamente:
   - Mapa HTML: `mapa_clima_[pais]_[fecha].html`
   - Gráfico PNG: `isotermas_[pais]_[fecha].png`

## 🌍 Países Disponibles

- Argentina (10 ciudades)
- Venezuela (4 ciudades)
- Colombia (4 ciudades)
- Chile (4 ciudades)
- Perú (4 ciudades)

Puedes agregar más países editando el diccionario `PAISES_CONFIG` en el notebook.

## 📊 Datos Incluidos

- Ciudad y ubicación (latitud/longitud)
- Descripción del clima
- Temperatura actual, mínima, máxima y sensación térmica
- Humedad relativa
- Presión atmosférica
- Velocidad y dirección del viento
- Visibilidad
- Ícono del clima

## 🗺️ Visualizaciones

### Mapa Interactivo
- Capa de calor de temperatura
- Marcadores agrupados por proximidad
- Colores según temperatura:
  - 🔵 Azul: < 10°C
  - 🟢 Verde: 10-20°C
  - 🟠 Naranja: 20-30°C
  - 🔴 Rojo: > 30°C

### Gráfico de Isotermas
- Interpolación cúbica de temperaturas
- Etiquetas de ciudades
- Mapa de colores (RdYlBu_r)

## ⚠️ Notas de Seguridad

- **NUNCA** subas tu API key a repositorios públicos
- **NUNCA** hardcodees tu API key en el código
- Usa **SIEMPRE** variables de entorno para la API key
- El código está configurado para requerir la API key como variable de entorno
- Si expusiste una API key, revócala inmediatamente en https://home.openweathermap.org/api_keys

## 🐛 Solución de Problemas

### Error de SSL
Si encuentras errores de certificado SSL (común en redes corporativas), el código maneja esto automáticamente.

### Límite de solicitudes
Si excedes el límite de la API (429), espera unos minutos antes de volver a intentar.

### Ciudad no encontrada
Verifica que el formato sea correcto: `"Ciudad, Código_País"` (ej: "Buenos Aires, AR")

## 📝 Licencia

Este proyecto es de código abierto y está disponible para uso educativo y personal.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Desarrollado con ❤️ usando Python, OpenWeatherMap API, Folium y Matplotlib**
