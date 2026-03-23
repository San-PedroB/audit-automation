"""Zone dashboard view."""

from __future__ import annotations

import streamlit as st

from audit_app.ui.components.charts import COMPACT_CHART_WIDTH, DEFAULT_CHART_WIDTH, render_chart_image
from audit_app.ui.components.metrics import render_metric_cards
from audit_app.ui.components.tables import render_table_model


def render_zone_tab(view_data: dict):
    st.markdown("#### Desglose por Zona")
    st.caption(
        "Cada zona se agrupa por cámara, mostrando primero un resumen de sus zonas y luego el detalle individual."
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

    st.markdown("##### Detalle Agrupado por Cámara")
    st.caption("Estructura modular: resumen de la cámara seguido del detalle por zona.")

    for cam_item in view_data.get("cameras", []):
        st.markdown(f"**{cam_item['camera_label']}**")
        
        st.markdown("###### Resumen de Zonas")
        render_table_model(cam_item["summary_table"])
        
        for zone_item in cam_item["zones"]:
            with st.expander(zone_item["label"], expanded=False):
                render_metric_cards(zone_item["metrics"], columns_per_row=4)

                st.markdown("**Grafico de Apoyo**")
                render_chart_image(
                    zone_item["chart"],
                    caption=f"Eventos Correctos del Sistema - {zone_item['label']}",
                    width=DEFAULT_CHART_WIDTH,
                )

                with st.expander("Ver detalle KPI de la zona", expanded=False):
                    render_table_model(zone_item["table"])
        
        st.markdown("---")
