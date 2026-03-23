"""Global and date breakdown dashboard views."""

from __future__ import annotations

import streamlit as st

from audit_app.ui.components.charts import (
    COMPACT_CHART_WIDTH,
    DEFAULT_CHART_WIDTH,
    render_chart_image,
    render_dual_bar_support_chart,
)
from audit_app.ui.components.metrics import render_metric_cards
from audit_app.ui.components.tables import (
    render_complete_master_table,
    render_master_table_blocks,
    render_table_model,
)


def render_global_tab(view_data: dict):
    st.markdown("#### Resumen Global")
    st.caption(
        "Vista general del sitio con mini resumen, tabla principal por zona, grafico de apoyo y detalle desplegable."
    )

    render_metric_cards(view_data["metrics"], columns_per_row=4)

    table_col, chart_col = st.columns([1.8, 1])

    with table_col:
        st.markdown("##### Tabla Principal por Zona")
        st.caption("Resumen global de los KPI principales por zona, incluyendo una fila total del sitio.")
        render_table_model(view_data["summary_table"])

    with chart_col:
        st.markdown("##### Grafico de Apoyo")
        if view_data["summary_chart"]:
            render_chart_image(
                view_data["summary_chart"],
                caption="Resumen de KPIs de la Tabla Maestra",
                width=COMPACT_CHART_WIDTH,
            )

        with st.expander("Ver resumen acumulado", expanded=False):
            render_table_model(view_data["totals_table"])

    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se presenta como un bloque desplegable con su tabla corta y su grafico de apoyo.")

    for zone_item in view_data["zones"]:
        with st.expander(zone_item["name"], expanded=zone_item["expanded"]):
            render_metric_cards(zone_item["metrics"], columns_per_row=4)

            st.markdown("**Grafico de Apoyo**")
            if zone_item["chart"]:
                render_chart_image(
                    zone_item["chart"],
                    caption=f"Eventos Correctos del Sistema - {zone_item['name']}",
                    width=DEFAULT_CHART_WIDTH,
                )

            with st.expander("Ver detalle KPI de la zona", expanded=False):
                render_table_model(zone_item["table"])


def render_date_breakdown_tab(view_data: dict | None):
    st.caption("Cada fecha del consolidado se presenta de forma individual para comparar volumen y desempeno.")

    if not view_data or not view_data.get("available"):
        st.info("No hay fechas individuales disponibles para mostrar en este consolidado.")
        return

    render_metric_cards(view_data["metrics"], columns_per_row=4)

    table_col, chart_col = st.columns([1.8, 1])
    with table_col:
        st.markdown("##### Tabla Principal por Fecha")
        st.caption("Resumen agregado por fecha dentro del consolidado de sucursal.")
        render_table_model(view_data["overview_table"])

    with chart_col:
        st.markdown("##### Grafico de Apoyo")
        overview_chart = view_data["overview_chart"]
        render_dual_bar_support_chart(
            overview_chart["labels"],
            overview_chart["base_values"],
            overview_chart["result_values"],
            overview_chart["title"],
            width=COMPACT_CHART_WIDTH,
        )

    st.markdown("##### Detalle por Fecha")
    st.caption("Cada fecha se presenta como bloque desplegable con su tabla principal y el detalle por horario.")

    for date_item in view_data["dates"]:
        with st.expander(date_item["label"], expanded=date_item["expanded"]):
            render_metric_cards(date_item["metrics"], columns_per_row=4)

            detail_table_col, detail_chart_col = st.columns([1.6, 1])
            with detail_table_col:
                st.markdown("**Tabla Principal**")
                render_table_model(date_item["table"])

            with detail_chart_col:
                st.markdown("**Grafico de Apoyo**")
                date_chart = date_item["chart"]
                render_dual_bar_support_chart(
                    date_chart["labels"],
                    date_chart["base_values"],
                    date_chart["result_values"],
                    date_chart["title"],
                    width=COMPACT_CHART_WIDTH,
                )

            with st.expander("Ver detalle por horario", expanded=False):
                render_table_model(date_item["hourly_table"])


def render_global_and_data_tab(final_df, global_view_data: dict, date_view_data: dict | None = None):
    if date_view_data is not None:
        summary_tab, dates_tab, blocks_tab, complete_tab = st.tabs(
            ["Resumen Global", "Detalle por Fecha", "Tabla Maestra en Bloques", "Tabla Maestra Completa"]
        )
    else:
        summary_tab, blocks_tab, complete_tab = st.tabs(
            ["Resumen Global", "Tabla Maestra en Bloques", "Tabla Maestra Completa"]
        )
        dates_tab = None

    with summary_tab:
        render_global_tab(global_view_data)

    if dates_tab is not None:
        with dates_tab:
            render_date_breakdown_tab(date_view_data)

    with blocks_tab:
        render_master_table_blocks(final_df)

    with complete_tab:
        render_complete_master_table(final_df)
