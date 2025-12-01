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

**Opción 2: Editar directamente en el código**

Edita la celda de configuración y reemplaza `'2f4c488fb0071f271d8970d535d398bc'` con tu API key.

## 📖 Uso

1. Abre el notebook `Copia de API_Weather.ipynb`
2. Ejecuta las celdas en orden
3. Selecciona el país cambiando `PAIS_SELECCIONADO` en la celda de configuración
4. Los resultados se guardarán automáticamente:
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
- Usa variables de entorno para producción
- La API key actual en el código es solo para pruebas

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

