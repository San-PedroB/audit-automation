@echo off
setlocal

echo Verificando entorno virtual...
if not exist ".venv\Scripts\activate.bat" (
    echo No se encontro .venv. Intentando crearlo...

    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>&1
        if %errorlevel% equ 0 (
            python -m venv .venv
        ) else (
            echo [ERROR] No se encontro Python instalado en el sistema.
            echo Instala Python 3.11+ y vuelve a ejecutar este archivo.
            pause
            exit /b 1
        )
    )
)

echo Activando entorno virtual...
call ".venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b %errorlevel%
)

echo Verificando dependencias...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudieron instalar las dependencias.
        pause
        exit /b %errorlevel%
    )
)

echo Lanzando Dashboard de Streamlit...
python -m streamlit run app.py
pause
