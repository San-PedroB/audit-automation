# Documentación del Proyecto de Procesamiento de Eventos de Video Analytics

Este documento detalla todas las reglas de negocio, transformaciones de datos y cálculos implementados en el script de Python (`calculo_metricas_video.py`) diseñado para procesar el archivo CSV de datos (`datos_auditoria_video.csv`).

## 1. Objetivo Principal
Analizar un conjunto de datos obtenidos de eventos de tráfico en diferentes zonas, separando los eventos registrados por el sistema frente a los manuales, y emitiendo un reporte tabular con los cálculos matemáticos requeridos sobre precisión de reconocimientos (Auditorías) y coberturas.

## 2. Definiciones Fundamentales

*   **Identificador de Evento (Identity_ID):** El campo clave que permite saber la naturaleza del registro.
    *   Si contiene la cadena `"unknown"` -> El sistema detectó a la persona, generó un evento, pero no sabe quién es. Es considerado un **Evento Registrado**.
    *   Si viene completamente *vacío (empty)* o es *nulo (NaN)* -> Fue un evento que el sistema se saltó o no pudo registrar del todo. Fue agregado por fuera (ej. manual). Es considerado un **Evento NO Registrado**.
*   **Zona (Zona_name):** El campo por el cual agrupamos (pivotamos) todas las filas.  Aquellas filas que no cuenten con una definición de 'Zona_name' válida (vacías o nulas) son directamente descartadas del procesamiento.
*   **Criterio de Precisión:** Anteriormente se basaba en la presencia de datos. Actualmente, la precisión se evalúa buscando la cadena `"Bien"` (insensible a mayúsculas/minúsculas) de forma estricta en las columnas de validación manual: `Event_Audit`, `Gender_Audit` y `Age_Audit`.

## 3. Glosario de Métricas Calculadas y su Lógica

Todas estas métricas se calculan individualmente *Por Zona*, y por último se procesan para el DataFrame *TOTAL* general.

### Totales y Divisiones Principales
1.  **Total eventos:** En la zona en evaluación, es la cuenta absoluta de todas las líneas que pertenezcan a esa zona.
2.  **Eventos no registrados por el sistema:** Líneas donde `Identity_ID` es *nulo* o un string vacío `""`.
3.  **Eventos registrados por el sistema:** La resta entre *Total eventos* y los *Eventos no registrados*. 

### Área de "Precisión" (Basado en la Auditoría) 
4.  **Precisión de Eventos:** Cantidad de registros donde la columna `Event_Audit` diga explícitamente "Bien".
    *   **% Precisión de Eventos:** (`Precisión de Eventos` ÷ `Total eventos`) * 100. **(NOTA: Esta es la ÚNICA métrica cuyo divisor es el 'Total Eventos')**.
5.  **Precisión de Genero:** Cantidad de registros donde `Gender_Audit` sea "Bien".
    *   **% Precisión de Genero:** (`Precisión de Genero` ÷ `Eventos registrados por el sistema`) * 100.
6.  **Precisión de Edad:** Cantidad de registros donde `Age_Audit` sea "Bien".
    *   **% Precisión de Edad:** (`Precisión de Edad` ÷ `Eventos registrados por el sistema`) * 100.

### Área de Identificaciones Desconocidas e Independientes
7.  **Identity unknown:** Cantidad de registros donde `Identity_ID` sea exactamente la string `"unknown"`.
    *   **% Identity unknown:** (`Identity unknown` ÷ `Eventos registrados por el sistema`) * 100.

### Área de "Cobertura" (Presencia de datos válidos, independientemente si pasó la Auditoría)
8.  **Cobertura de Género:** Total de filas donde el Género (`Gender`) NO sea nulo ni contenga el string `"unknown"`.
    *   **% Cobertura Genero:** (`Cobertura de Género` ÷ `Eventos registrados por el sistema`) * 100.
9.  **Cobertura de Edad:** Total de filas donde la Edad (`Age`) no sea nula y su valor numérico sea estrictamente mayor a 0 (>0).
    *   **% Cobertura de Edad:** (`Cobertura de Edad` ÷ `Eventos registrados por el sistema`) * 100.
10. **Cobertura de Identity**: La diferencia matemática al restarle al total absoluto de la zona (`Total eventos`) todos los campos que dijeron ser "unknown" en `Identity_ID`.
    *   **% Cobertura de Identity:** (`Cobertura de Identity` ÷ `Eventos registrados por el sistema`) * 100.

## 4. Estructura del Reporte Automatizado (Excel)

A diferencia de los archivos CSV planos, el reporte final se genera en un formato Excel enriquecido con gráficos y tablas formateadas.

### 4.1. Uso de Plantilla (Template)
El script busca un archivo llamado `Template Tabla Maestra.xlsx` en la carpeta de la auditoría.
- Si lo encuentra: Inyecta los datos calculados a partir de la fila 3, preservando los logos, colores de cabecera y celdas combinadas del usuario.
- Si no lo encuentra: Genera un archivo estándar con formato de tabla de Excel.

### 4.2. Visualizaciones (Estilo Informe Crystal)
Se generan tres tipos de visualizaciones dinámicas utilizando Matplotlib:
1.  **Gráfico Global de Zonas**: Comparativa de Total Eventos vs Precisión de Eventos para todas las zonas auditadas.
2.  **Gráfico de Totales**: Resumen consolidado del desempeño general (Registrados, No Registrados, Precisión).
3.  **Análisis por Cámara**: Agrupación inteligente donde cada cámara tiene su propia sección con:
    *   Un gráfico de barras con todas sus zonas.
    *   Una tabla detallada con métricas por zona y un **TOTAL por cámara**.

### 4.3. Estética Corporativa
El diseño emula el **Informe Crystal**:
- **Colores**: Navy (`#1B2A4A`) para volumen de eventos y Rojo (`#C0392B`) para precisión.
- **Formato**: Fondo blanco limpio, leyendas centradas en la parte superior y tablas con cabeceras azul marino y filas alternas.

## 5. Ejecución del Script

Para procesar una auditoría, se utiliza la línea de comandos (CLI):

```bash
python calculo_metricas_video.py -e "Nombre Empresa" -f "DD-MM"
```
- `-e`: Nombre de la carpeta del cliente (ej. Casino Talca).
- `-f`: Subcarpeta de la fecha (ej. 11-03).

## 6. Archivos Producidos

1.  **Reporte_Auditoria_Maestro.xlsx**: El producto final con 3 hojas: `TABLA MAESTRA`, `Gráficos` y `Por Cámara`.
2.  **reporte_cobertura.csv**: Versión técnica de respaldo con separador de tabulaciones.
3.  **reporte_cobertura_comas.csv**: Versión técnica de respaldo con separador de comas.
