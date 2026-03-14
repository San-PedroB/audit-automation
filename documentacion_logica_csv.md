# Documentación del Proyecto de Procesamiento de Eventos de Video Analytics

Este documento detalla todas las reglas de negocio, transformaciones de datos y cálculos implementados en el script de Python (`import pandas as pd.py`) diseñado para procesar el archivo CSV de datos (`que te pasa.csv`).

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

---

## 4. Archivos Producidos

El proceso ejecutará sus iteraciones y finalmente expelerá los siguientes reportes tabulares:

1.  **reporte_cobertura.csv**: Formateado utilizando separador `\t` (Tabulación). Facilita profundamente hacer *Copy* & *Paste* de su contenido en crudo a entornos como Excel o Google Sheets, alineando todo a la perfección.
2.  **reporte_cobertura_comas.csv**: Un respaldo del archivo anterior, pero utilizando separador de comas estándar `,`, por si el archivo tabulado entra en conflictos con procesadores de bases de datos.
