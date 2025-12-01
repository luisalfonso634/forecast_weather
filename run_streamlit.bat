@echo off
REM Script para ejecutar Streamlit con la API Key configurada automáticamente

REM Configurar la API Key
set OPENWEATHER_API_KEY=2f4c488fb0071f271d8970d535d398bc

REM Verificar y ejecutar
echo ✅ API Key configurada
echo 🚀 Iniciando aplicación Streamlit...
echo.

streamlit run app.py

pause

