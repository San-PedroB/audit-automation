"""Camera dashboard views."""

from __future__ import annotations

import streamlit as st

from audit_app.ui.components.charts import (
    COMPACT_CHART_WIDTH,
    DEFAULT_CHART_WIDTH,
    render_chart_image,
    render_dual_bar_support_chart,
)
from audit_app.ui.components.metrics import render_metric_cards
from audit_app.ui.components.tables import render_table_model


def render_camera_tab(view_data: dict):
    st.markdown("#### Analisis de Rendimiento por Camara")
    st.caption(
        "Cada vista sigue el mismo patron: mini resumen, tabla principal, grafico de apoyo y detalle en expanders."
    )

    render_metric_cards(view_data["metrics"], columns_per_row=4)

    overview_table_col, overview_chart_col = st.columns([1.8, 1])
    with overview_table_col:
        st.markdown("##### Tabla Principal por Camara")
        st.caption("Resumen agregado por camara para identificar rapido donde profundizar.")
        render_table_model(view_data["overview_table"])

    with overview_chart_col:
        st.markdown("##### Grafico de Apoyo")
        overview_chart = view_data["overview_chart"]
        render_dual_bar_support_chart(
            overview_chart["labels"],
            overview_chart["base_values"],
            overview_chart["result_values"],
            overview_chart["title"],
            width=COMPACT_CHART_WIDTH,
        )

    st.markdown("##### Detalle por Camara")
    st.caption("Cada camara se presenta como un bloque desplegable con su resumen y comparativos por zona.")

    for camera_item in view_data["cameras"]:
        with st.expander(camera_item["label"], expanded=camera_item["expanded"]):
            render_metric_cards(camera_item["metrics"], columns_per_row=4)

            st.markdown("##### Tabla General por Zona")
            st.caption(
                f"Resumen completo de {camera_item['label']}, incluyendo la fila total de la camara."
            )
            render_table_model(camera_item["summary_table"])

            detail_correct_tab, detail_registered_tab = st.tabs(
                ["Eventos Correctos del Sistema", "Eventos Registrados por el Sistema"]
            )

            with detail_correct_tab:
                if camera_item["correct_chart"]:
                    render_chart_image(
                        camera_item["correct_chart"],
                        caption=f"{camera_item['label']} - Eventos Correctos del Sistema por Zona",
                        width=DEFAULT_CHART_WIDTH,
                    )
                render_table_model(camera_item["correct_table"])

            with detail_registered_tab:
                if camera_item["coverage_chart"]:
                    render_chart_image(
                        camera_item["coverage_chart"],
                        caption=f"{camera_item['label']} - Eventos Registrados por el Sistema por Zona",
                        width=DEFAULT_CHART_WIDTH,
                    )
                render_table_model(camera_item["coverage_table"])
