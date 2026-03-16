# Contexto para IA de PC Principal (Transferencia de Proyecto)

Copia y pega el siguiente texto completo en la nueva IA de tu PC principal para que se ponga al día con el proyecto en el que estábamos trabajando.

---
INICIO DEL PROMPT PARA COPIAR:
---
**¡Hola IA!** Te estoy pasando el contexto maestro de un proyecto de "Análisis de Datos de Video Analytics" escrito en Python (Pandas) en el que estaba trabajando en mi notebook. Ahora vamos a continuar desarrollando este proyecto aquí en el PC principal.

### 📝 Contexto del Proyecto
El objetivo del proyecto ha sido limpiar y sacar **métricas exactas de precisión y cobertura** desde un reporte CSV base para volcar un resumen agrupado por el campo "Zona". Ya hemos establecido las reglas matemáticas explícitas de este reporte (cómo clasificar a cada usuario, qué es cobertura y qué es precisión) porque la métrica a veces daba más del 100% en versiones iniciales. Hemos arreglado todo eso.

### 🗃️ Estructura de Directorios y Ejecución
Para organizar mejor los reportes de distintos clientes y fechas, hemos creado la estructura base `Auditorias_Clientes/{Nombre_Empresa}/{Fecha}/`
El script *requiere* que se ejecuten parámetros por consola indicándole en qué carpeta operar. Ejemplo de uso:
> `python calculo_metricas_video.py -e Nombre_Cliente -f 2026-03`
El script buscará por defecto un archivo llamado `input.csv` en esa ruta, y dejará los reportes ahí mismo.

Las columnas clave que usamos del archivo de origen (`input.csv`) son:
*   `Identity_ID`: Identificador de persona. Puede tener un UUID, venir vacío/nulo, o decir "unknown".
*   `Zona_name`: La zona física (ej. Atencion_Club, Fila_Club). No se usa si viene vacío.
*   `Action`: Acción del evento (ej. Enter, Exit).
*   `Gender` / `Age`: Género y Edad inferidos por el modelo. (Pueden ser "unknown" o vacíos).
*   `Event_Audit`, `Gender_Audit`, `Age_Audit`: Columnas que hace el revisor humano manualmente. Las filas evaluadas correctamente por el sistema tienen el texto "Bien" escrito en estas columnas.

### 🧠 Lógica de Negocio y Métricas
*   **Total de Eventos:** El recuento completo de filas para una zona.
*   **Eventos **NO** registrados (manuales):** Son explícitamente aquellos en los que `Identity_ID` está vacía o es Nula. (NOTA IMPORTANTE: La palabra "unknown" NO cuenta como no registrado, eso cuenta como sistema).
*   **Eventos registrados por el sistema:** `Total Eventos` - `Eventos Manuales`. (Este número es el divisor para los porcentajes de cobertura, género y edad).
*   **Precisión de Eventos / Edad / Género**: Busca la cadena literal "Bien" en las respectivas columnas de Auditoría. (El % de Precisión de Evento se divide contra `Total eventos`, los demás porcentajes se dividen contra `Eventos registrados por el sistema`).
*   **Identity unknown**: Se cuenta cuántos literales dicen "unknown" de la columna `Identity_ID`.
*   **Cobertura de Género / Edad**: Cuántos de esos campos NO son nulos y contienen datos viables (ej. edad mayor a 0, y el string de género no debe ser "unknown").

### 💻 Script Actual (calculo_metricas_video.py)
A continuación te presento el código exacto, funcional e implementado del script Python en su estado actual, el cual procesa el archivo leyendo el origen y exportando dos CSV (delimitado por coma y delimitado por tabulación). 

```python
import pandas as pd
import argparse
import os

# ==========================================
# Configuración Dinámica de Rutas (Argparse)
# ==========================================
parser = argparse.ArgumentParser(description='Procesa los datos de Video Analytics para un cliente y fecha específicos.')
parser.add_argument('-e', '--empresa', type=str, required=True, help='Nombre de la carpeta de la empresa (ej. Empresa_Demo)')
parser.add_argument('-f', '--fecha', type=str, required=True, help='Nombre de la carpeta de fecha (ej. 2026-03)')
parser.add_argument('-i', '--input', type=str, default='input.csv', help='Nombre del archivo CSV a leer (por defecto: input.csv)')
args = parser.parse_args()

# Construir rutas dinámicamente
base_dir = "Auditorias_Clientes"
work_dir = os.path.join(base_dir, args.empresa, args.fecha)
input_file_path = os.path.join(work_dir, args.input)

# Validar que el archivo y directorio existan
if not os.path.exists(input_file_path):
    print(f"❌ ERROR: No se encontró el archivo en la ruta:\n   {input_file_path}")
    print("Por favor verifica que la carpeta de la empresa y fecha estén bien escritas y el archivo exista.")
    exit(1)

# ==========================================
# PASO 1: Leer el archivo CSV original
# ==========================================
print(f"Leyendo datos desde:\n   {input_file_path}")
df = pd.read_csv(input_file_path)

# Filtrar solo registros que tengan un 'Zona_name' asignado
df_zones = df[df['Zona_name'].notna() & (df['Zona_name'] != '')].copy()

# ==========================================
# PASO 2: Procesar y calcular métricas
# ==========================================
print("Calculando métricas por zona...")

def calculate_metrics(group):
    # Total de eventos (registros en esa zona)
    total_eventos = len(group)
    
    # Eventos no registrados (manuales) = Aquellos donde Identity_ID es nulo o vacio ('unknown' es del sistema)
    eventos_no_registrados = group['Identity_ID'].isna().sum() + \
                            (group['Identity_ID'].astype(str).str.strip() == '').sum()
    
    # Eventos registrados por el sistema
    eventos_registrados = total_eventos - eventos_no_registrados

    # Precisión de Eventos (columna Event_Audit == 'Bien')
    precicion_eventos = group['Event_Audit'].astype(str).str.strip().str.lower().eq('bien').sum()
    
    # Precisión de Género (columna Gender_Audit == 'Bien')
    precision_genero = group['Gender_Audit'].astype(str).str.strip().str.lower().eq('bien').sum()
    
    # Precisión de Edad (columna Age_Audit == 'Bien')
    precision_edad = group['Age_Audit'].astype(str).str.strip().str.lower().eq('bien').sum()
    
    # Cobertura de Género (diferente de 'unknown' o nulo)
    genero_conocido = group['Gender'].notna() & (group['Gender'] != 'unknown')
    cobertura_genero = genero_conocido.sum()
    
    # Cobertura de Edad (mayor a 0)
    edad_numerica = pd.to_numeric(group['Age'], errors='coerce')
    edad_conocida = edad_numerica.notna() & (edad_numerica > 0)
    cobertura_edad = edad_conocida.sum()
    
    # Identidad
    identity_unknown = (group['Identity_ID'] == 'unknown').sum()
    cobertura_identity = total_eventos - identity_unknown
    
    # Calcular porcentajes
    def calc_pct(part, total):
        return f"{(part / total * 100):.2f}%" if total > 0 else "0.00%"
        
    return pd.Series({
        'Eventos registrados por el sistema': eventos_registrados,
        'Eventos no registrados por el sistema': eventos_no_registrados,
        'Total eventos': total_eventos,
        'Precicion de Eventos': precicion_eventos,
        '% Presicion de Eventos': calc_pct(precicion_eventos, total_eventos), # viene del total
        'Precision de Genero': precision_genero,
        '% Precision de Genero': calc_pct(precision_genero, eventos_registrados), # viene del registrado
        'Precicion de Edad': precision_edad,
        '% Precicion de Edad': calc_pct(precision_edad, eventos_registrados), # viene del registrado
        'Identity unknown': identity_unknown,
        '% Identity unknown': calc_pct(identity_unknown, eventos_registrados), # viene del registrado
        'Cobertura Genero': cobertura_genero,
        '% Cobertura Genero': calc_pct(cobertura_genero, eventos_registrados), # viene del registrado
        'Cobertura de Edad': cobertura_edad,
        '% Cobertura de Edad': calc_pct(cobertura_edad, eventos_registrados), # viene del registrado
        'Cobertura de Identity': cobertura_identity,
        '% Cobertura de Identity': calc_pct(cobertura_identity, eventos_registrados) # viene del registrado
    })

# Agrupar por zona
reporte = df_zones.groupby('Zona_name').apply(calculate_metrics).reset_index()
reporte.rename(columns={'Zona_name': 'Zona'}, inplace=True)

# Calcular la fila de TOTALES agregando todo el dataframe que tiene zona
totales = calculate_metrics(df_zones)
totales['Zona'] = 'TOTAL'
# Convertir a DataFrame y transponer para poder concatenar
df_totales = pd.DataFrame(totales).T

# Concatenar los totales al reporte
reporte = pd.concat([reporte, df_totales], ignore_index=True)

# ==========================================
# PASO 3: Exportar el reporte procesado
# ==========================================
output_filename = os.path.join(work_dir, 'reporte_cobertura.csv')
reporte.to_csv(output_filename, index=False, sep='\t') # Tab-separated para que se vea igual que el ejemplo
# Tambien lo guardo como CSV normal separado por comas
output_comas = os.path.join(work_dir, 'reporte_cobertura_comas.csv')
reporte.to_csv(output_comas, index=False)

print(f"✅ Nuevo reporte exportado exitosamente en la carpeta del cliente:")
print(f"   -> {output_filename}")
print(f"   -> {output_comas}")
```

👉 **Mi siguiente pregunta e instrucción para continuar en este proyecto es:**
Para ejecutar este script, debes usar la línea de comandos y pasar los parámetros `-e` para la empresa y `-f` para la fecha. Por ejemplo: `python calculo_metricas_video.py -e Nombre_Cliente -f 2026-03`. El script ahora lee el `input.csv` y guarda los reportes de salida (`reporte_cobertura.csv` y `reporte_cobertura_comas.csv`) directamente en la carpeta dinámica `Auditorias_Clientes/{Nombre_Empresa}/{Fecha}/` que se especifica en los parámetros.

---
FIN DEL PROMPT.
---
