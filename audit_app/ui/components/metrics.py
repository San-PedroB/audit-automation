"""Metric card helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def format_camera_label(cam_value):
    if cam_value in ("", "nan", None):
        return "General"
    try:
        return f"Camara {int(cam_value)}"
    except (TypeError, ValueError):
        return f"Camara {cam_value}"


def format_metric_value(column_name: str, value) -> str:
    if pd.isna(value):
        return "N/A"
    if column_name.startswith("%"):
        return f"{float(value):.2%}"
    return f"{int(float(value))}"


def render_metric_cards(metric_items: list[tuple[str, float]], columns_per_row: int = 4):
    for start_index in range(0, len(metric_items), columns_per_row):
        row_items = metric_items[start_index : start_index + columns_per_row]
        row_columns = st.columns(len(row_items))
        for container, (metric_name, metric_value) in zip(row_columns, row_items):
            with container:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-card-title">{metric_name}</div>
                        <div class="metric-card-value">{format_metric_value(metric_name, metric_value)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
