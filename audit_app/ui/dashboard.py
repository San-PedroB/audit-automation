"""Streamlit dashboard entrypoint and routing."""

from __future__ import annotations

import os

import streamlit as st

from audit_app.domain.metrics import build_audit_report
from audit_app.domain.kpi_schema import TOP_METRIC_COLUMNS
from audit_app.infrastructure.charts import build_chart_payloads
from audit_app.services.audit_service import (
    SENSOR_TYPE_COLUMN,
    VIEW_MODE_DATE,
    VIEW_MODE_INDIVIDUAL,
    VIEW_MODE_SUCURSAL,
    list_audit_dates,
    list_audit_files,
    process_audit_data,
)
from audit_app.services.view_builders import build_dashboard_view_models
from audit_app.ui.components.metrics import format_metric_value
from audit_app.ui.views.camera_view import render_camera_tab
from audit_app.ui.views.global_view import render_global_and_data_tab
from audit_app.ui.views.unknowns_view import render_unknowns_tab
from audit_app.ui.views.zone_view import render_zone_tab


def configure_page():
    st.set_page_config(
        page_title="Audit Automation Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(255,255,255,0.06);
        }
        .metric-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.012));
            border: 1px solid rgba(255,255,255,0.06);
            border-left: 4px solid #1B2A4A;
            border-radius: 14px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.18);
            min-height: 118px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            backdrop-filter: blur(8px);
        }
        .metric-card-title {
            color: rgba(255,255,255,0.92);
            font-size: 0.82rem;
            line-height: 1.25rem;
            font-weight: 600;
            white-space: normal;
            word-break: break-word;
            overflow-wrap: anywhere;
            margin-bottom: 10px;
        }
        .metric-card-value {
            color: #FFFFFF;
            font-size: 2rem;
            line-height: 1;
            font-weight: 700;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 0.35rem;
            margin-bottom: 0.65rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 2.35rem;
            border-radius: 999px;
            padding: 0.2rem 0.9rem;
            background: rgba(255,255,255,0.015);
            border: 1px solid transparent;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(27,42,74,0.22);
            border: 1px solid rgba(64,102,163,0.45);
        }
        [data-testid="stExpander"] {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            background: rgba(255,255,255,0.015);
            overflow: hidden;
            margin-bottom: 0.9rem;
        }
        [data-testid="stExpander"] details summary {
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            overflow: hidden;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
        }
        [data-testid="stMarkdownContainer"] hr {
            margin-top: 1.5rem;
            margin-bottom: 1.35rem;
            border-color: rgba(255,255,255,0.08);
        }
        [data-testid="stCaptionContainer"] {
            color: rgba(255,255,255,0.58);
        }
        [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
            margin-bottom: 0.15rem;
        }
        h1, h2, h3 {
            color: var(--text-color);
            font-family: 'Inter', sans-serif;
        }
        h4, h5 {
            color: rgba(255,255,255,0.96);
            letter-spacing: -0.01em;
        }
        .stButton>button {
            background-color: #1B2A4A;
            color: white;
            border: 1px solid rgba(84,119,176,0.45);
            border-radius: 10px;
            padding: 10px 24px;
            font-weight: bold;
        }
        .stDownloadButton>button {
            border-radius: 10px;
            border: 1px solid rgba(84,119,176,0.45);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(selected_empresa: str, selected_sucursal: str, selected_context: str):
    st.title("Auditoria de Video Analytics")
    subtitle_html = f"""
        <div style="margin-top: -15px; margin-bottom: 25px; margin-left: 2px;">
            <span style="color: #555; font-size: 1.2rem; font-weight: 400;">
                <b>{selected_empresa}</b> &nbsp;&nbsp;&bull;&nbsp;&nbsp;
                {selected_sucursal} &nbsp;&nbsp;&bull;&nbsp;&nbsp;
                {selected_context}
            </span>
        </div>
    """
    st.write(subtitle_html, unsafe_allow_html=True)
    st.markdown("---")


def render_top_metrics(df_total):
    if df_total.empty:
        return

    total_row = df_total.iloc[0]
    columns = st.columns(len(TOP_METRIC_COLUMNS))
    for column_container, metric_name in zip(columns, TOP_METRIC_COLUMNS):
        with column_container:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-card-title">{metric_name}</div>
                    <div class="metric-card-value">{format_metric_value(metric_name, total_row[metric_name])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def get_sensor_options(results: dict) -> list[str]:
    source_df = results.get("source_df")
    if source_df is None or SENSOR_TYPE_COLUMN not in source_df.columns:
        return ["Todos"]

    sensor_values = (
        source_df[SENSOR_TYPE_COLUMN]
        .fillna("No definido")
        .astype(str)
        .str.strip()
        .replace("", "No definido")
        .tolist()
    )
    distinct_values = sorted(set(sensor_values))
    preferred_order = ["Linea_conteo", "Zona_permanencia", "No definido"]
    ordered_values = [value for value in preferred_order if value in distinct_values]
    ordered_values.extend([value for value in distinct_values if value not in ordered_values])
    if len(ordered_values) <= 1:
        return ["Todos"]
    return ["Todos"] + ordered_values


def build_sensor_filtered_results(results: dict, sensor_value: str) -> dict | None:
    if sensor_value == "Todos":
        filtered_results = dict(results)
        filtered_results["active_sensor"] = sensor_value
        return filtered_results

    source_df = results.get("source_df")
    if source_df is None or SENSOR_TYPE_COLUMN not in source_df.columns:
        return None

    filtered_source = source_df[
        source_df[SENSOR_TYPE_COLUMN].fillna("No definido").astype(str).str.strip() == sensor_value
    ].copy()
    if filtered_source.empty:
        return None

    reporte, df_grafico, df_total = build_audit_report(filtered_source, "")
    chart_payloads = build_chart_payloads(df_grafico, df_total)

    filtered_results = dict(results)
    filtered_results.update(
        {
            "reporte": reporte,
            "df_grafico": df_grafico,
            "df_total": df_total,
            "source_df": filtered_source,
            "img_global": chart_payloads["img_global"],
            "img_totales": chart_payloads["img_totales"],
            "cam_images": chart_payloads["cam_images"],
            "cam_coverage_images": chart_payloads["cam_coverage_images"],
            "cam_summary_images": chart_payloads["cam_summary_images"],
            "zone_images": chart_payloads["zone_images"],
            "img_unknown_global": chart_payloads["img_unknown_global"],
            "img_unknown_global_bytes": chart_payloads["img_unknown_global_bytes"],
            "unknown_images": chart_payloads["unknown_images"],
            "active_sensor": sensor_value,
        }
    )
    return filtered_results


def render_dashboard_views(results: dict):
    view_models = build_dashboard_view_models(results)

    render_top_metrics(results["df_total"])
    st.caption(
        f"{results['view_label']} | {results['source_count']} auditoria(s) procesada(s) | Sensor: {results.get('active_sensor', 'Todos')}"
    )
    st.markdown("### Analisis Visual")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Analisis Global",
            "Detalle por Camara",
            "Analisis de Unknowns",
            "Detalle por Zona",
        ]
    )

    with tab1:
        render_global_and_data_tab(results["reporte"], view_models["global"], view_models["dates"])
    with tab2:
        render_camera_tab(view_models["camera"])
    with tab3:
        render_unknowns_tab(view_models["unknowns"])
    with tab4:
        render_zone_tab(view_models["zone"])


def render_results(results: dict):
    sensor_options = get_sensor_options(results)
    if len(sensor_options) <= 1:
        render_dashboard_views(results)
    else:
        sensor_tabs = st.tabs(sensor_options)
        for sensor_value, sensor_tab in zip(sensor_options, sensor_tabs):
            with sensor_tab:
                filtered_results = build_sensor_filtered_results(results, sensor_value)
                if filtered_results is None:
                    st.info(f"No hay datos para el sensor {sensor_value}.")
                    continue
                render_dashboard_views(filtered_results)

    with open(results["output_xlsx"], "rb") as file:
        st.download_button(
            label="Descargar Reporte Excel Maestro",
            data=file,
            file_name=os.path.basename(results["output_xlsx"]),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_sidebar(base_dir: str):
    st.sidebar.header("Configuracion de Auditoria")

    empresas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    selected_empresa = st.sidebar.selectbox("Seleccione Empresa", empresas)

    empresa_path = os.path.join(base_dir, selected_empresa)
    sucursales = [d for d in os.listdir(empresa_path) if os.path.isdir(os.path.join(empresa_path, d))]
    selected_sucursal = st.sidebar.selectbox("Seleccione Sucursal", sucursales)

    fechas = list_audit_dates(base_dir, selected_empresa, selected_sucursal)
    if not fechas:
        st.sidebar.warning("No hay fechas o auditorias para esta sucursal.")
        st.stop()

    view_mode = st.sidebar.selectbox(
        "Modo de vista",
        [VIEW_MODE_INDIVIDUAL, VIEW_MODE_DATE, VIEW_MODE_SUCURSAL],
    )

    selected_fecha = None
    selected_audit_filename = None
    selected_context = "Consolidado sucursal"
    uploaded_file = None
    audit_files = []

    if view_mode in (VIEW_MODE_INDIVIDUAL, VIEW_MODE_DATE):
        selected_fecha = st.sidebar.selectbox("Seleccione Fecha", fechas)
        audit_files = list_audit_files(base_dir, selected_empresa, selected_sucursal, selected_fecha)

    if view_mode == VIEW_MODE_INDIVIDUAL:
        if not audit_files:
            st.sidebar.warning("No hay auditorias individuales para la fecha seleccionada.")
            st.stop()

        audit_labels = {audit["label"]: audit for audit in audit_files}
        selected_audit_label = st.sidebar.selectbox("Seleccione Auditoria", list(audit_labels.keys()))
        selected_audit = audit_labels[selected_audit_label]
        selected_audit_filename = selected_audit["filename"]
        selected_context = f"{selected_audit['fecha']} | {selected_audit['label']}"
        uploaded_file = st.sidebar.file_uploader("Actualizar auditoria (opcional)", type=["csv"])
    elif view_mode == VIEW_MODE_DATE:
        if not audit_files:
            st.sidebar.warning("No hay auditorias para la fecha seleccionada.")
            st.stop()
        selected_context = f"{selected_fecha.replace('_', '-')} | Consolidado por fecha"
        st.sidebar.caption(f"Se consolidaran {len(audit_files)} auditoria(s) de esta fecha.")
    else:
        total_files = 0
        for fecha in fechas:
            total_files += len(list_audit_files(base_dir, selected_empresa, selected_sucursal, fecha))
        if total_files == 0:
            st.sidebar.warning("No hay auditorias disponibles para consolidar en la sucursal.")
            st.stop()
        st.sidebar.caption(f"Se consolidaran {total_files} auditoria(s) de la sucursal completa.")

    process_btn = st.sidebar.button("Procesar Auditoria")

    return {
        "empresa": selected_empresa,
        "sucursal": selected_sucursal,
        "fecha": selected_fecha,
        "view_mode": view_mode,
        "audit_filename": selected_audit_filename,
        "uploaded_file": uploaded_file,
        "process_btn": process_btn,
        "context_label": selected_context,
    }


def handle_file_upload(base_dir: str, empresa: str, sucursal: str, fecha: str | None, audit_filename: str | None, uploaded_file):
    if not uploaded_file or not fecha or not audit_filename:
        return

    input_path = os.path.join(base_dir, empresa, sucursal, fecha, audit_filename)
    with open(input_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    st.sidebar.success("Archivo actualizado correctamente")


def run_dashboard():
    configure_page()

    base_dir = "Auditorias_Clientes"
    if not os.path.exists(base_dir):
        st.error(f"No se encontro la carpeta base: {base_dir}")
        st.stop()

    sidebar_state = render_sidebar(base_dir)
    render_header(
        sidebar_state["empresa"],
        sidebar_state["sucursal"],
        sidebar_state["context_label"],
    )
    handle_file_upload(
        base_dir,
        sidebar_state["empresa"],
        sidebar_state["sucursal"],
        sidebar_state["fecha"],
        sidebar_state["audit_filename"],
        sidebar_state["uploaded_file"],
    )

    if not sidebar_state["process_btn"]:
        st.info("Seleccione la empresa, sucursal y modo de vista en la barra lateral para comenzar.")
        st.image(
            "https://images.unsplash.com/photo-1551288049-bbbda536339a?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True,
        )
        return

    with st.spinner("Procesando datos y generando graficos..."):
        results, error = process_audit_data(
            sidebar_state["empresa"],
            sidebar_state["fecha"],
            sucursal=sidebar_state["sucursal"],
            mode=sidebar_state["view_mode"],
            audit_filename=sidebar_state["audit_filename"],
        )
        if error:
            st.error(error)
            return
        render_results(results)
