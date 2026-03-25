"""Chart display helpers for Streamlit views."""

from __future__ import annotations

import streamlit as st

from audit_app.infrastructure.charts import make_dual_bar_chart

DEFAULT_CHART_WIDTH = 0.72
COMPACT_CHART_WIDTH = 0.5


def render_chart_image(image_data, caption: str | None = None, width: float = DEFAULT_CHART_WIDTH):
    if image_data is None:
        return
    width = min(max(width, 0.2), 1.0)
    side = max((1.0 - width) / 2, 0.05)
    left_col, center_col, right_col = st.columns([side, width, side])
    with center_col:
        st.image(image_data, caption=caption, use_container_width=True)


def render_dual_bar_support_chart(labels, base_values, result_values, title, width: float = DEFAULT_CHART_WIDTH):
    render_generic_dual_bar_support_chart(
        labels,
        base_values,
        result_values,
        title,
        "Total Eventos",
        "Eventos Correctos del Sistema",
        width=width,
    )


def render_generic_dual_bar_support_chart(
    labels,
    base_values,
    result_values,
    title,
    label_base,
    label_result,
    width: float = DEFAULT_CHART_WIDTH,
):
    chart_bytes = make_dual_bar_chart(
        labels,
        base_values,
        result_values,
        title,
        label_base,
        label_result,
    )
    render_chart_image(chart_bytes, width=width)
