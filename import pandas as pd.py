import pandas as pd

# ==========================================
# PASO 1: Leer el archivo CSV original
# ==========================================
print("Leyendo datos desde Datos.csv...")
df = pd.read_csv('que te pasa.csv')

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
output_filename = 'reporte_cobertura.csv'
reporte.to_csv(output_filename, index=False, sep='\t') # Tab-separated para que se vea igual que el ejemplo
# Tambien lo guardo como CSV normal separado por comas
reporte.to_csv('reporte_cobertura_comas.csv', index=False)

print(f"✅ Nuevo reporte exportado exitosamente como '{output_filename}' y 'reporte_cobertura_comas.csv'")

# Imprimir en consola para verificar
print("\n--- VISTA PREVIA DEL REPORTE ---")
print(reporte.to_string(index=False))
