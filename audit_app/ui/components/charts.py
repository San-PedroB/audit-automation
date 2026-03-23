"""Chart display helpers for Streamlit views."""

from __future__ import annotations

import streamlit as st

from audit_app.infrastructure.charts import make_dual_bar_chart

DEFAULT_CHART_WIDTH = 760
COMPACT_CHART_WIDTH = 460


def render_chart_image(image_data, caption: str | None = None, width: int = DEFAULT_CHART_WIDTH):
    if image_data is None:
        return
    st.image(image_data, caption=caption, width=width)


def render_dual_bar_support_chart(labels, base_values, result_values, title, width: int = DEFAULT_CHART_WIDTH):
    chart_bytes = make_dual_bar_chart(
        labels,
        base_values,
        result_values,
        title,
        "Total Eventos",
        "Eventos Correctos del Sistema",
    )
    render_chart_image(chart_bytes, width=width)
