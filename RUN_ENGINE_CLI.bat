@echo off
set /p cliente="Ingrese el nombre del cliente/empresa (ej: Empresa_Demo): "
set /p fecha="Ingrese la fecha (ej: 2026-03): "

echo Activando entorno virtual...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b %errorlevel%
)

echo Ejecutando Motor de Metricas para %cliente% en %fecha%...
python calculo_metricas_video.py -e "%cliente%" -f "%fecha%"

echo.
echo Proceso finalizado. Presione cualquier tecla para cerrar.
pause
