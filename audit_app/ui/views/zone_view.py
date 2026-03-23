"""Zone dashboard view."""

from __future__ import annotations

import streamlit as st

from audit_app.ui.components.charts import COMPACT_CHART_WIDTH, DEFAULT_CHART_WIDTH, render_chart_image
from audit_app.ui.components.metrics import render_metric_cards
from audit_app.ui.components.tables import render_table_model


def render_zone_tab(view_data: dict):
    st.markdown("#### Desglose por Zona")
    st.caption(
        "Cada vista sigue el mismo patron: mini resumen, tabla principal, grafico de apoyo y detalle en expanders."
    )

    render_metric_cards(view_data["metrics"], columns_per_row=4)

    overview_table_col, overview_chart_col = st.columns([1.8, 1])
    with overview_table_col:
        st.markdown("##### Tabla Principal por Zona")
        st.caption("Resumen agregado por zona para revisar rapidamente el comportamiento del sitio.")
        render_table_model(view_data["overview_table"])

    with overview_chart_col:
        st.markdown("##### Grafico de Apoyo")
        if view_data["overview_chart"]:
            render_chart_image(
                view_data["overview_chart"],
                caption="Eventos Correctos del Sistema por Zona",
                width=COMPACT_CHART_WIDTH,
            )

    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se muestra en un bloque desplegable con su resumen, tabla principal y grafico de apoyo.")

    for zone_item in view_data["zones"]:
        with st.expander(zone_item["label"], expanded=zone_item["expanded"]):
            render_metric_cards(zone_item["metrics"], columns_per_row=4)

            st.markdown("**Grafico de Apoyo**")
            render_chart_image(
                zone_item["chart"],
                caption=f"Eventos Correctos del Sistema - {zone_item['label']}",
                width=DEFAULT_CHART_WIDTH,
            )

            with st.expander("Ver detalle KPI de la zona", expanded=False):
                render_table_model(zone_item["table"])
