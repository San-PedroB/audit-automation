"""Unknown identities dashboard view."""

from __future__ import annotations

import streamlit as st

from audit_app.ui.components.charts import COMPACT_CHART_WIDTH, DEFAULT_CHART_WIDTH, render_chart_image
from audit_app.ui.components.metrics import render_metric_cards
from audit_app.ui.components.tables import render_table_model


def render_unknowns_tab(view_data: dict):
    st.markdown("#### Registro de Identidades Desconocidas")
    st.caption(
        "Esta vista concentra el resumen de Identity Unknown, el comparativo global y el detalle por zona."
    )

    render_metric_cards(view_data["metrics"], columns_per_row=3)

    table_col, chart_col = st.columns([1.8, 1])

    with table_col:
        st.markdown("##### Tabla General de Identity Unknown por Zona")
        st.caption(
            f"Se identificaron Unknowns en {view_data['zones_with_unknown']} zona(s). "
            "La tabla principal ocupa el mayor espacio para facilitar la revision completa."
        )
        render_table_model(view_data["summary_table"])

    with chart_col:
        st.markdown("##### Resumen Grafico")
        if not view_data["has_unknowns"]:
            st.success("No se detectaron Unknowns en los registros del sistema.")
        if view_data["summary_chart"]:
            render_chart_image(
                view_data["summary_chart"],
                caption="Identity Unknown - Resumen Global",
                width=COMPACT_CHART_WIDTH,
            )
        else:
            st.info("No hay grafico global disponible para esta auditoria.")

    if not view_data["has_unknowns"]:
        return

    st.markdown("---")
    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se presenta como bloque desplegable para revisar solo lo que necesitas.")

    zone_columns = st.columns(2)

    for index, zone_item in enumerate(view_data["zones"]):
        with zone_columns[index % 2]:
            with st.expander(f"Identity Unknown - {zone_item['label']}", expanded=False):
                if zone_item["caption"]:
                    st.caption(zone_item["caption"])
                render_chart_image(
                    zone_item["chart"],
                    caption=f"Identity Unknown - {zone_item['label']}",
                    width=DEFAULT_CHART_WIDTH,
                )
                if zone_item["table"] is not None:
                    st.markdown("**Resumen de la zona**")
                    render_table_model(zone_item["table"])
