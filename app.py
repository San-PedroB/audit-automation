import streamlit as st
import os
import pandas as pd
from calculo_metricas_video import process_audit_data

# Configuración de página con estética Premium
st.set_page_config(
    page_title="Audit Automation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS para el look "Informe Crystal" / Premium
st.markdown("""
    <style>
    .stMetric {
        background-color: var(--secondary-background-color) !important;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #1B2A4A;
        transition: transform 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
    }
    h1, h2, h3 {
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background-color: #1B2A4A;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Auditoría de Video Analytics")
st.markdown("---")

# --- SIDEBAR: Configuración ---
st.sidebar.header("Configuración de Auditoría")

base_dir = "Auditorias_Clientes"
if not os.path.exists(base_dir):
    st.error(f"No se encontró la carpeta base: {base_dir}")
    st.stop()

# Descubrir Empresas
empresas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
selected_empresa = st.sidebar.selectbox("Seleccione Empresa", empresas)

# Descubrir Sucursales para la empresa seleccionada
empresa_path = os.path.join(base_dir, selected_empresa)
sucursales = [d for d in os.listdir(empresa_path) if os.path.isdir(os.path.join(empresa_path, d))]
selected_sucursal = st.sidebar.selectbox("Seleccione Sucursal", sucursales)

# Descubrir Fechas para la sucursal seleccionada
sucursal_path = os.path.join(empresa_path, selected_sucursal)
fechas = [d for d in os.listdir(sucursal_path) if os.path.isdir(os.path.join(sucursal_path, d))]

if not fechas:
    st.sidebar.warning("No hay fechas/auditorías para esta sucursal.")
    st.stop()
    
selected_fecha = st.sidebar.selectbox("Seleccione Fecha", fechas)
work_dir = os.path.join(sucursal_path, selected_fecha)
st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Actualizar datos (opcional)", type=["csv"])

if uploaded_file and selected_fecha:
    # Guardar el archivo subido en el directorio correspondiente
    input_path = os.path.join(base_dir, selected_empresa, selected_sucursal, selected_fecha, "input.csv")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("✅ Archivo actualizado correctamente")
elif uploaded_file and not selected_fecha:
    st.sidebar.error("❌ Por favor, cree una carpeta de fecha antes de subir datos.")

# Botón de Procesamiento
process_btn = st.sidebar.button("Procesar Auditoría", disabled=(not selected_fecha))

# --- MAIN: Resultados ---
if process_btn and selected_fecha:
    with st.spinner("Procesando datos y generando gráficos..."):
        results, error = process_audit_data(selected_empresa, selected_fecha, sucursal=selected_sucursal)
        
        if error:
            st.error(error)
        else:
            # Layout con métricas clave
            col1, col2, col3, col4, col5 = st.columns(5)
            
            df_total = results['df_total']
            if not df_total.empty:
                t_row = df_total.iloc[0]
                col1.metric("Total Eventos", int(t_row['Total Eventos']))
                col2.metric("Eventos Correctos", f"{t_row['% Eventos Correctos del Sistema']:.2%}")
                col3.metric("Registrados", int(t_row['Eventos Registrados por el Sistema']))
                col4.metric("Reg. Incorrectos", int(t_row['Eventos Reg. Mal (Sist.)']))
                col5.metric("No Registrados", int(t_row['Eventos NO Registrados (Manuales)']))

            st.markdown("### 📈 Análisis Visual")
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Análisis Global", 
                "Detalle por Cámara", 
                "Análisis de Unknowns",
                "Detalle por Zona", 
                "Tabla de Datos"
            ])
            
            with tab1:
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    if results['img_global']:
                        st.image(results['img_global'], caption="Distribución por Zona", use_container_width=True)
                        # Tabla Resumen Global (Zonas)
                        st.markdown("**Resumen de Calidad por Zona**")
                        cols_global = ['Zona', 'Total Eventos', 'Eventos Correctos del Sistema', '% Eventos Correctos del Sistema', 'Eventos Reg. Mal (Sist.)', '% Eventos Reg. Mal (Sist.)']
                        df_g = results['df_grafico'][cols_global].copy()
                        # Calcular Total
                        t_ev = df_g['Total Eventos'].sum()
                        p_ev = df_g['Eventos Correctos del Sistema'].sum()
                        bad_ev = df_g['Eventos Reg. Mal (Sist.)'].sum()
                        acc = p_ev / t_ev if t_ev > 0 else 0
                        reg_ev = results['df_total']['Eventos Registrados por el Sistema'].iloc[0]
                        bad_pct = bad_ev / reg_ev if reg_ev > 0 else 0
                        total_g = pd.DataFrame([['TOTAL', t_ev, p_ev, acc, bad_ev, bad_pct]], columns=cols_global)
                        df_g = pd.concat([df_g, total_g], ignore_index=True)
                        st.dataframe(df_g.style.format({
                            'Total Eventos': '{:.0f}',
                            'Eventos Correctos del Sistema': '{:.0f}',
                            '% Eventos Correctos del Sistema': '{:.2%}',
                            'Eventos Reg. Mal (Sist.)': '{:.0f}',
                            '% Eventos Reg. Mal (Sist.)': '{:.2%}'
                        }), hide_index=True, use_container_width=True)
                with col_right:
                    if results['img_totales']:
                        st.image(results['img_totales'], caption="Resumen de Totales", use_container_width=True)
                        # Tabla Totales (Ya es un resumen, pero mostramos formateado)
                        st.markdown("**Métricas Globales Acumuladas**")
                        st.dataframe(results['df_total'][['Total Eventos', '% Eventos Correctos del Sistema', '% Eventos Reg. Mal (Sist.)', '% Eventos Registrados por el Sistema', '% Eventos NO Registrados (Manuales)']].style.format({
                            'Total Eventos': '{:.0f}',
                            '% Eventos Correctos del Sistema': '{:.2%}',
                            '% Eventos Reg. Mal (Sist.)': '{:.2%}',
                            '% Eventos Registrados por el Sistema': '{:.2%}',
                            '% Eventos NO Registrados (Manuales)': '{:.2%}'
                        }), hide_index=True, use_container_width=True)

            with tab2:
                st.markdown("#### Análisis de Rendimiento por Cámara")
                st.info("💡 Se muestra primero el Resumen Agregado de la cámara (todas las zonas sumadas) y luego el detalle comparativo por zona.")
                
                cameras = results['df_grafico']['Camara_pura'].unique()
                for i, cam in enumerate(cameras):
                    cam_label = f"Cámara {int(cam)}" if cam not in ('', 'nan', None) else "General"
                    st.markdown(f"### {cam_label}")
                    
                    # 1. Resumen Agregado
                    if i < len(results['cam_summary_images']):
                        st.image(results['cam_summary_images'][i]['buffer'], caption=f"{cam_label} - RESUMEN AGREGADO", width=900)
                    
                    # 2. Detalle lado a lado (Gráficos)
                    c1, c2 = st.columns(2)
                    with c1:
                        if i < len(results['cam_images']):
                            st.image(results['cam_images'][i]['buffer'], caption=f"{cam_label} - Precisión por Zona", use_container_width=True)
                    with c2:
                        if i < len(results['cam_coverage_images']):
                            st.image(results['cam_coverage_images'][i]['buffer'], caption=f"{cam_label} - Cobertura por Zona", use_container_width=True)
                    
                    # 3. Tabla de Datos de la Cámara
                    st.markdown(f"**Datos Detallados — {cam_label}**")
                    cam_df = results['df_grafico'][results['df_grafico']['Camara_pura'] == cam].copy()
                    cols_cam = ['Zona', 'Total Eventos', 'Eventos Correctos del Sistema', '% Eventos Correctos del Sistema', 'Eventos Reg. Mal (Sist.)', '% Eventos Reg. Mal (Sist.)', '% Cobertura Identity']
                    
                    # Calcular Fila Total de Cámara
                    t_c = cam_df['Total Eventos'].sum()
                    p_c = cam_df['Eventos Correctos del Sistema'].sum()
                    b_c = cam_df['Eventos Reg. Mal (Sist.)'].sum()
                    i_c = cam_df['Cobertura Identity'].sum() if 'Cobertura Identity' in cam_df.columns else 0
                    
                    acc_c = p_c / t_c if t_c > 0 else 0
                    # Nueva regla: Reg. Mal sobre Registrados
                    reg_cam = cam_df['Eventos Registrados por el Sistema'].sum()
                    bad_c = b_c / reg_cam if reg_cam > 0 else 0
                    # Cobertura Identity sobre Registrados
                    cob_i = i_c / reg_cam if reg_cam > 0 else 0
                    
                    total_cam = pd.DataFrame([['TOTAL CÁMARA', t_c, p_c, acc_c, b_c, bad_c, cob_i]], columns=cols_cam)
                    cam_df = pd.concat([cam_df[cols_cam], total_cam], ignore_index=True)
                    
                    st.dataframe(cam_df.style.format({
                        'Total Eventos': '{:.0f}',
                        'Eventos Correctos del Sistema': '{:.0f}',
                        '% Eventos Correctos del Sistema': '{:.2%}',
                        'Eventos Reg. Mal (Sist.)': '{:.0f}',
                        '% Eventos Reg. Mal (Sist.)': '{:.2%}',
                        '% Cobertura Identity': '{:.2%}'
                    }), hide_index=True, use_container_width=True)
                    st.markdown("---")

            with tab3:
                st.markdown("#### Registro de Identidades Desconocidas")
                if results.get('img_unknown_global'):
                    st.image(results['img_unknown_global'], caption="Impacto Global de Unknowns (Sindicados vs Unknown)", width=900)
                    st.markdown("---")
                    
                if results['unknown_images']:
                    # Tabla General de Unknowns primero
                    st.markdown("**Tabla General de Unknowns por Zona**")
                    cols_unk = ['Zona', 'Eventos Registrados por el Sistema', 'Identity Unknown', '% Identity Unknown']
                    df_u = results['df_grafico'][cols_unk].copy()
                    
                    # Calcular Total Unknowns
                    r_u = df_u['Eventos Registrados por el Sistema'].sum()
                    u_u = df_u['Identity Unknown'].sum()
                    p_u = u_u / r_u if r_u > 0 else 0
                    
                    total_u = pd.DataFrame([['TOTAL', r_u, u_u, p_u]], columns=cols_unk)
                    df_u = pd.concat([df_u, total_u], ignore_index=True)
                    
                    st.dataframe(df_u.style.format({
                        'Eventos Registrados por el Sistema': '{:.0f}',
                        'Identity Unknown': '{:.0f}',
                        '% Identity Unknown': '{:.2%}'
                    }), hide_index=True, use_container_width=True)
                    st.markdown("---")
                    
                    for img_u in results['unknown_images']:
                        st.image(img_u['buffer'], caption=f"Impacto Unknowns en {img_u['label']}", width=700)
                else:
                    st.success("🎉 No se detectaron Unknowns en los registros del sistema.")

            with tab4:
                st.markdown("#### Desglose por Zona")
                for i, img_data in enumerate(results['zone_images']):
                    st.image(img_data['buffer'], caption=img_data['label'], width=700)
                    # Mostrar fila de datos para esta zona
                    zona_row = results['df_grafico'][results['df_grafico']['Zona'] == img_data['label']]
                    # Formatear porcentajes y conteos dinámicamente
                    pct_cols = [c for c in zona_row.columns if str(c).startswith('%')]
                    count_cols = [
                        'Total Eventos', 'Eventos Registrados por el Sistema', 'Eventos NO Registrados (Manuales)', 
                        'Eventos Correctos del Sistema', 'Eventos Reg. Mal (Sist.)', 'Identity Unknown', 'Cobertura Género', 'Cobertura Edad', 'Cobertura Identity'
                    ]
                    
                    fmt_dict = {c: '{:.2%}' for c in pct_cols}
                    for c in count_cols:
                        if c in zona_row.columns:
                            fmt_dict[c] = '{:.0f}'
                            
                    st.dataframe(zona_row.style.format(fmt_dict), hide_index=True)
                    st.markdown("---")

            with tab5:
                # Formatear todos los porcentajes y conteos en el reporte maestro
                pct_cols_all = [c for c in results['reporte'].columns if str(c).startswith('%')]
                count_cols_all = [
                    'Total Eventos', 'Eventos Registrados por el Sistema', 'Eventos NO Registrados (Manuales)', 
                    'Eventos Correctos del Sistema', 'Precisión de Género', 'Precisión de Edad', 'Eventos Reg. Mal (Sist.)', 'Identity Unknown',
                    'Cobertura Género', 'Cobertura Edad', 'Cobertura Identity'
                ]
                
                fmt_dict_all = {c: '{:.2%}' for c in pct_cols_all}
                for c in count_cols_all:
                    if c in results['reporte'].columns:
                        fmt_dict_all[c] = '{:.0f}'
                        
                st.dataframe(results['reporte'].style.format(fmt_dict_all), use_container_width=True)

            # Botón de Descarga
            with open(results['output_xlsx'], "rb") as file:
                btn = st.download_button(
                    label="⬇️ Descargar Reporte Excel Maestro",
                    data=file,
                    file_name=os.path.basename(results['output_xlsx']),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    # Estado inicial
    st.info("Seleccione la empresa y fecha en la barra lateral para comenzar.")
    st.image("https://images.unsplash.com/photo-1551288049-bbbda536339a?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_container_width=True)
