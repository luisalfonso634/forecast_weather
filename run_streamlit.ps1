# Script para ejecutar Streamlit con la API Key configurada automáticamente
# Este script configura la API Key y ejecuta la aplicación

# Configurar la API Key
$env:OPENWEATHER_API_KEY = "2f4c488fb0071f271d8970d535d398bc"

# Verificar que se configuró
Write-Host "✅ API Key configurada" -ForegroundColor Green
Write-Host "🚀 Iniciando aplicación Streamlit..." -ForegroundColor Cyan
Write-Host ""

# Ejecutar Streamlit
streamlit run app.py

