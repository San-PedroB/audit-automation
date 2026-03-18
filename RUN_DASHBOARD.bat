@echo off
echo Activando entorno virtual...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual. Asegurate de que existe la carpeta .venv.
    pause
    exit /b %errorlevel%
)
echo Lanzando Dashboard de Streamlit...
streamlit run app.py
pause
