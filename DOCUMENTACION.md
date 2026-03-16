# Documentación: Sistema de Automatización de Auditorías (Dashboard Crystal)

Este sistema permite procesar datos de auditoría de video, generar métricas de precisión y visualizaciones profesionales ("Crystal Pro"), y exportar informes detallados en formato Excel.

## 🚀 Cómo Ejecutar el Programa

1. **Entorno Virtual**: Asegúrate de tener el entorno virtual activado.
   ```powershell
   .\.venv\Scripts\activate
   ```
2. **Lanzar Dashboard**: Ejecuta el comando de Streamlit.
   ```powershell
   streamlit run app.py
   ```
3. **Uso**: 
   - Selecciona la **Empresa**, la **Sucursal** y la **Fecha** del reporte.
   - El sistema busca automáticamente el archivo `input.csv` en la ruta: `Auditorias_Clientes / [Empresa] / [Sucursal] / [Fecha] /`.
   - Presiona **"Procesar Auditoría"**.

---

## 📂 Estructura del Proyecto

- `app.py`: Interfaz de usuario (Streamlit). Maneja la visualización de pestañas y navegación multinivel.
- `calculo_metricas_video.py`: Motor de métricas. Contiene la lógica matemática, normalización de datos y generación de gráficos.
- `templates/`: Carpeta raíz con la plantilla `Template Tabla Maestra.xlsx` para asegurar consistencia estética.
- `Auditorias_Clientes/`: Carpeta raíz donde se almacenan los inputs y resultados organizados por Empresa > Sucursal > Fecha.

---

## 🧮 Reglas de Negocio y Fórmulas
Para asegurar la consistencia del "Informe Crystal", todas las métricas de porcentaje utilizan el **Total Auditado** como denominador universal (Base 100%).

| Métrica | Fórmula | Descripción |
| :--- | :--- | :--- |
| **% Precisión** | $Aciertos / Total Auditado$ | Eficacia general de la detección correcta. |
| **% Cobertura ID** | $Identificados / Total Auditado$ | Porcentaje de personas con ID asignada sobre el total real. |
| **% Cobertura Género** | $Género Detectado / Total Auditado$ | Atribución de género sobre la población total auditada. |
| **% Cobertura Edad** | $Edad Detectada / Total Auditado$ | Atribución de edad sobre la población total auditada. |
| **% Unknowns** | $Unknowns / Total Auditado$ | Impacto de las identidades no resueltas sobre el total auditado. |

> [!IMPORTANT]
> Un evento se considera **"Registrado por el Sistema"** si tiene un `Identity_ID` no nulo. La **"Cobertura de Identidad"** descuenta los valores `unknown` para reflejar la calidad real del reconocimiento facial/ID.

---

## 📊 Lógica de Gráficos "Crystal Pro"

1. **Base de Referencia (100%)**: La barra azul representa el **Total Auditado**. Es el techo de todas las comparativas.
2. **Cumplimiento**: La barra roja representa los **Eventos Correctos**.
3. **Estandarización**: Todos los gráficos mantienen el mismo eje Y (0-100%) para permitir comparaciones visuales inmediatas entre sucursales o cámaras.

---

## 🛠️ Requisitos Técnicos

- **Python 3.11+**
- **Librerías principales**: `pandas`, `streamlit`, `matplotlib`, `openpyxl`.
- **Formato Input**: CSV con columnas `Zona_name`, `Event_Audit`, `Gender_Audit`, `Age_Audit`, `Identity_ID`.

---
*Documentación generada automáticamente - Marzo 2026*
