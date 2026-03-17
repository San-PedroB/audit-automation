# 📊 Audit Automation Dashboard — Crystal Pro

Este proyecto es una herramienta avanzada para automatizar el procesamiento de auditorías de video analytics. Transforma datos crudos de CSV en informes visuales de alta calidad ("Crystal Pro") y reportes maestros en Excel con formatos ejecutivos.

## 🚀 Guía de Inicio Rápido

Para instalar y correr este proyecto en un nuevo PC, sigue estos pasos:

### 1. Requisitos
- **Python 3.11+**
- **Git** (opcional, para clonar el repositorio)

### 2. Instalación
Clona el repositorio o descarga la carpeta, luego abre una terminal y ejecuta:

```powershell
# Crear entorno virtual
python -m venv .venv

# Activar entorno (PowerShell)
.\.venv\Scripts\activate

# Instalar librerías necesarias
pip install -r requirements.txt
```

### 3. Ejecución
Para lanzar el dashboard interactivo:
```powershell
streamlit run app.py
```

---

## 🏗️ Estructura de Navegación
El sistema está diseñado para manejar múltiples clientes y fechas:
`Auditorias_Clientes / [Empresa] / [Sucursal] / [Fecha] / input.csv`

## 🧮 Reglas de Negocio (Regla de Oro)
Todas las métricas de porcentaje se normalizan utilizando el **Total Auditado** como base 100%. Esto asegura que los KPIs de **Precisión** y **Cobertura** sean comparables y coherentes entre sí.

## 📂 Contenido del Repositorio
- `app.py`: Interfaz de usuario con Streamlit.
- `calculo_metricas_video.py`: Motor de métricas y generación de gráficos.
- `templates/`: Plantilla Excel para reportes premium.
- `requirements.txt`: Lista de dependencias de Python.

---
*Desarrollado para la optimización de procesos de auditoría - 2026*
