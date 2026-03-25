"""Curated report-ready dashboard view."""

from __future__ import annotations

import streamlit as st

from audit_app.services.report_data import build_report_view_data
from audit_app.ui.components.charts import COMPACT_CHART_WIDTH, render_generic_dual_bar_support_chart
from audit_app.ui.components.tables import render_table_model


def _render_context_filters(base_view: dict, widget_suffix: str) -> dict:
    options = base_view["filter_options"]
    context = base_view["context"]

    st.markdown("##### Filtros")
    info_cols = st.columns(3)
    info_cols[0].selectbox(
        "Tienda",
        options["empresa"],
        index=0,
        disabled=True,
        key=f"report_empresa_{widget_suffix}",
    )
    info_cols[1].selectbox(
        "Sucursal",
        options["sucursal"],
        index=0,
        disabled=True,
        key=f"report_sucursal_{widget_suffix}",
    )
    info_cols[2].selectbox(
        "Modo de vista",
        options["modo"],
        index=0,
        disabled=True,
        key=f"report_modo_{widget_suffix}",
    )

    filter_cols = st.columns(5)
    return {
        "fecha": filter_cols[0].selectbox("Fecha", options["fecha"], key=f"report_fecha_{widget_suffix}"),
        "tramo": filter_cols[1].selectbox("Tramo / jornada", options["tramo"], key=f"report_tramo_{widget_suffix}"),
        "camara": filter_cols[2].selectbox("Camara", options["camara"], key=f"report_camara_{widget_suffix}"),
        "zona": filter_cols[3].selectbox("Zona", options["zona"], key=f"report_zona_{widget_suffix}"),
        "tipo_zona": filter_cols[4].selectbox("Tipo de zona", options["tipo_zona"], key=f"report_tipo_zona_{widget_suffix}"),
    }


def _render_validation_block(view_data: dict):
    st.markdown("##### Validaciones")
    if not view_data["validation_messages"]:
        st.success("Las validaciones principales cuadran para el filtro actual.")
        return

    for message in view_data["validation_messages"]:
        st.warning(message)


def _render_optional_table(title: str, caption: str, table_model: dict):
    st.markdown(f"##### {title}")
    st.caption(caption)
    if table_model["row_count"] == 0:
        st.info("No hay datos disponibles para este bloque con el filtro actual.")
        return
    render_table_model(table_model)


def render_report_data_tab(results: dict):
    st.markdown("#### Data Informe")
    st.caption(
        "Vista curada para redactar el informe final: solo KPIs, tablas y comparativos listos para copiar."
    )

    widget_suffix = str(results.get("active_sensor", "Todos")).replace(" ", "_")
    base_view = build_report_view_data(results)
    filters = _render_context_filters(base_view, widget_suffix)
    view_data = build_report_view_data(results, filters)

    st.caption(
        f"Filtro activo | Fecha: {filters['fecha']} | Tramo: {filters['tramo']} | Camara: {filters['camara']} | Zona: {filters['zona']} | Tipo: {filters['tipo_zona']} | Sensor: {view_data['context']['sensor']}"
    )

    if not view_data["has_data"]:
        st.warning("No hay datos para los filtros seleccionados dentro de Data Informe.")
        return

    _render_validation_block(view_data)

    _render_optional_table(
        "KPIs Generales del Informe",
        "Bloque central para resumen ejecutivo y lectura global del tramo filtrado.",
        view_data["kpis_table"],
    )

    _render_optional_table(
        "Lineas de Conteo",
        "Resumen curado para informe con precision principal, precision secundaria y subregistro.",
        view_data["lines_table"],
    )

    st.markdown("##### Error de linea de conteo")
    st.caption("Balance de flujo TDI por fecha y tramo para comparar entradas y salidas dentro del filtro activo.")
    if view_data["flow_balance"]["table"]["row_count"] == 0:
        st.info("No hay datos suficientes para construir el bloque de error de linea de conteo.")
    else:
        render_table_model(view_data["flow_balance"]["table"])
        if view_data["flow_balance"]["chart"] is not None:
            render_generic_dual_bar_support_chart(
                view_data["flow_balance"]["chart"]["labels"],
                view_data["flow_balance"]["chart"]["base_values"],
                view_data["flow_balance"]["chart"]["result_values"],
                view_data["flow_balance"]["chart"]["title"],
                view_data["flow_balance"]["chart"]["label_base"],
                view_data["flow_balance"]["chart"]["label_result"],
                width=COMPACT_CHART_WIDTH,
            )

    _render_optional_table(
        "Zonas de Permanencia",
        "Bloque listo para narrativa de permanencia y desempeno por zona.",
        view_data["dwell_table"],
    )

    _render_optional_table(
        "Resumen por Camara",
        "Sintesis por camara para alimentar narrativa ejecutiva.",
        view_data["camera_table"],
    )

    _render_optional_table(
        "Identity",
        "Separacion entre cobertura Identity e Identity Unknown para zonas aplicables.",
        view_data["identity_table"],
    )

    _render_optional_table(
        "Genero y Edad",
        "Cobertura y precision de atributos, con N/A cuando la cobertura es 0.",
        view_data["attributes_table"],
    )

    st.markdown("##### Consolidado multi-tramo")
    st.caption("Comparativo por fecha o tramo cuando el dataset activo contiene mas de un periodo.")
    if view_data["multi_period"]["table"]["row_count"] == 0:
        st.info("No hay datos para construir el consolidado multi-tramo.")
    elif not view_data["multi_period"]["available"]:
        st.info("El filtro actual contiene un solo periodo, por lo que no aplica comparativo multi-tramo.")
    else:
        render_table_model(view_data["multi_period"]["table"])
        if view_data["multi_period"]["chart"] is not None:
            render_generic_dual_bar_support_chart(
                view_data["multi_period"]["chart"]["labels"],
                view_data["multi_period"]["chart"]["base_values"],
                view_data["multi_period"]["chart"]["result_values"],
                view_data["multi_period"]["chart"]["title"],
                view_data["multi_period"]["chart"]["label_base"],
                view_data["multi_period"]["chart"]["label_result"],
                width=COMPACT_CHART_WIDTH,
            )
        _render_optional_table(
            "Comparativo por Camara",
            "Bloque consolidado por periodo y camara para reutilizar en informes multi-tramo.",
            view_data["multi_period"]["camera_table"],
        )
        _render_optional_table(
            "Comparativo por Zona",
            "Bloque consolidado por periodo, camara y zona para profundizar conclusiones cuando haga falta.",
            view_data["multi_period"]["zone_table"],
        )
