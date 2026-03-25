"""Reusable table helpers for dashboard views."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from audit_app.domain.kpi_schema import COUNT_COLUMNS, DATA_TABLE_SECTIONS, KPI_COLUMNS


def get_dataframe_height(row_count: int, extra_header_rows: int = 0) -> int:
    header_height = 38
    row_height = 35
    padding = 12
    return header_height * (1 + extra_header_rows) + row_height * max(row_count, 1) + padding


def render_styled_dataframe(styled_df, row_count: int, hide_index: bool = True):
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=hide_index,
        height=get_dataframe_height(row_count),
    )


def render_table_model(table_model: dict, hide_index: bool = True):
    render_styled_dataframe(
        table_model["dataframe"].style.format(table_model["formatters"]),
        table_model["row_count"],
        hide_index=hide_index,
    )


def prepare_display_dataframe(dataframe: pd.DataFrame, columns: list[str] | None = None):
    display_df = dataframe[columns].copy() if columns else dataframe.copy()
    formatters = {}

    for column in display_df.columns:
        if str(column).startswith("%"):
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = lambda value: "N/A" if pd.isna(value) else f"{float(value):.2%}"
        elif column in COUNT_COLUMNS:
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = lambda value: "N/A" if pd.isna(value) else f"{float(value):.0f}"

    return display_df, formatters


def render_data_section(title: str, dataframe: pd.DataFrame, formatters: dict):
    with st.expander(title, expanded=True):
        styled = dataframe.style.format(formatters)
        render_styled_dataframe(styled, len(dataframe))


def build_section_lookup() -> dict:
    section_lookup = {}
    for section_name, columns in DATA_TABLE_SECTIONS.items():
        for column in columns:
            if column != "Zona":
                section_lookup[column] = section_name
    section_lookup["Zona"] = "Contexto"
    return section_lookup


def render_complete_master_table(final_df: pd.DataFrame):
    ordered_columns = [column for column in KPI_COLUMNS if column in final_df.columns]
    complete_df = final_df[ordered_columns].copy()
    base_formatters = {}

    for column in ordered_columns:
        if str(column).startswith("%"):
            complete_df[column] = pd.to_numeric(complete_df[column], errors="coerce")
            base_formatters[column] = lambda value: "N/A" if pd.isna(value) else f"{float(value):.2%}"
        elif column in COUNT_COLUMNS:
            complete_df[column] = pd.to_numeric(complete_df[column], errors="coerce")
            base_formatters[column] = lambda value: "N/A" if pd.isna(value) else f"{float(value):.0f}"

    section_lookup = build_section_lookup()
    multi_columns = [(section_lookup.get(column, "Otros"), column) for column in ordered_columns]
    complete_df.columns = pd.MultiIndex.from_tuples(multi_columns)
    multi_formatters = {
        (section_lookup.get(column, "Otros"), column): formatter
        for column, formatter in base_formatters.items()
    }

    st.markdown("#### Tabla Maestra Completa")
    st.caption("Vista completa de la tabla maestra con una fila de encabezado agrupada por secciones.")
    styled = complete_df.style.format(multi_formatters)
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=get_dataframe_height(len(complete_df), extra_header_rows=1),
    )


def render_master_table_blocks(final_df: pd.DataFrame):
    st.caption("La tabla se presenta separada por secciones, siguiendo la estructura de la tabla maestra.")

    for section_name, section_columns in DATA_TABLE_SECTIONS.items():
        available_columns = [column for column in section_columns if column in final_df.columns]
        if not available_columns:
            continue

        section_df, formatters = prepare_display_dataframe(final_df, available_columns)
        render_data_section(section_name, section_df, formatters)
