"""Streamlit dashboard UI."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from audit_app.domain.kpi_schema import (
    CAMERA_COLUMN,
    CAMERA_SUMMARY_COLUMNS,
    COUNT_COLUMNS,
    DATA_TABLE_SECTIONS,
    GLOBAL_SUMMARY_COLUMNS,
    KPI_COLUMNS,
    TOP_METRIC_COLUMNS,
    TOTAL_SUMMARY_COLUMNS,
    UNKNOWN_COLUMNS,
)
from audit_app.services.audit_service import process_audit_data


def format_camera_label(cam_value):
    if cam_value in ("", "nan", None):
        return "General"
    try:
        return f"Camara {int(cam_value)}"
    except (TypeError, ValueError):
        return f"Camara {cam_value}"


def format_metric_value(column_name: str, value) -> str:
    if column_name.startswith("%"):
        return f"{float(value):.2%}"
    return f"{int(float(value))}"


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


def prepare_display_dataframe(dataframe: pd.DataFrame, columns: list[str] | None = None):
    display_df = dataframe[columns].copy() if columns else dataframe.copy()
    formatters = {}

    for column in display_df.columns:
        if str(column).startswith("%"):
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce").fillna(0.0)
            formatters[column] = "{:.2%}"
        elif column in COUNT_COLUMNS:
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce").fillna(0.0)
            formatters[column] = "{:.0f}"

    return display_df, formatters


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


def configure_page():
    st.set_page_config(
        page_title="Audit Automation Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .metric-card {
            background: rgba(255,255,255,0.01);
            border-left: 4px solid #1B2A4A;
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            min-height: 118px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .metric-card-title {
            color: rgba(255,255,255,0.92);
            font-size: 0.82rem;
            line-height: 1.25rem;
            font-weight: 600;
            white-space: normal;
            word-break: break-word;
            overflow-wrap: anywhere;
            margin-bottom: 10px;
        }
        .metric-card-value {
            color: #FFFFFF;
            font-size: 2rem;
            line-height: 1;
            font-weight: 700;
        }
        h1, h2, h3 {
            color: var(--text-color);
            font-family: 'Inter', sans-serif;
        }
        .stButton>button {
            background-color: #1B2A4A;
            color: white;
            border-radius: 5px;
            padding: 10px 24px;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(selected_empresa: str, selected_sucursal: str, selected_fecha: str):
    st.title("Auditoria de Video Analytics")
    subtitle_html = f"""
        <div style="margin-top: -15px; margin-bottom: 25px; margin-left: 2px;">
            <span style="color: #555; font-size: 1.2rem; font-weight: 400;">
                <b>{selected_empresa}</b> &nbsp;&nbsp;&bull;&nbsp;&nbsp;
                {selected_sucursal} &nbsp;&nbsp;&bull;&nbsp;&nbsp;
                {selected_fecha.replace('_', '-')}
            </span>
        </div>
    """
    st.write(subtitle_html, unsafe_allow_html=True)
    st.markdown("---")


def render_top_metrics(df_total: pd.DataFrame):
    if df_total.empty:
        return

    total_row = df_total.iloc[0]
    columns = st.columns(len(TOP_METRIC_COLUMNS))
    for column_container, metric_name in zip(columns, TOP_METRIC_COLUMNS):
        with column_container:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-card-title">{metric_name}</div>
                    <div class="metric-card-value">{format_metric_value(metric_name, total_row[metric_name])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_global_tab(results: dict):
    st.markdown("#### Resumen Global")
    st.caption(
        "Vista general del sitio con mini resumen, tabla principal por zona, grafico de apoyo y detalle desplegable."
    )

    df_global = results["df_grafico"][GLOBAL_SUMMARY_COLUMNS].copy()
    total_events = df_global["Total Eventos"].sum()
    correct_events = df_global["Eventos Correctos del Sistema"].sum()
    bad_events = df_global["Eventos Reg. Mal (Sist.)"].sum()
    registered_events = results["df_total"]["Eventos Registrados por el Sistema"].iloc[0]

    totals_row = pd.DataFrame(
        [[
            "TOTAL",
            total_events,
            correct_events,
            (correct_events / registered_events) if registered_events > 0 else 0,
            (correct_events / total_events) if total_events > 0 else 0,
            bad_events,
            (bad_events / registered_events) if registered_events > 0 else 0,
        ]],
        columns=GLOBAL_SUMMARY_COLUMNS,
    )
    df_global = pd.concat([df_global, totals_row], ignore_index=True)
    df_global, global_formatters = prepare_display_dataframe(df_global)

    render_metric_cards(
        [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            ("% Eventos Correctos sobre Registrados", (correct_events / registered_events) if registered_events > 0 else 0),
            ("Eventos Reg. Mal (Sist.)", bad_events),
        ],
        columns_per_row=4,
    )

    table_col, chart_col = st.columns([1.8, 1])

    with table_col:
        st.markdown("##### Tabla Principal por Zona")
        st.caption("Resumen global de los KPI principales por zona, incluyendo una fila total del sitio.")
        render_styled_dataframe(df_global.style.format(global_formatters), len(df_global))

    with chart_col:
        st.markdown("##### Grafico de Apoyo")
        if results["img_totales"]:
            st.image(
                results["img_totales"],
                caption="Resumen de KPIs de la Tabla Maestra",
                use_container_width=True,
            )

        totals_df, totals_formatters = prepare_display_dataframe(
            results["df_total"],
            TOTAL_SUMMARY_COLUMNS,
        )
        st.markdown("**Resumen Acumulado**")
        render_styled_dataframe(totals_df.style.format(totals_formatters), len(totals_df))

    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se presenta como un bloque desplegable con su tabla corta y su grafico de apoyo.")

    zone_columns = [
        "Zona",
        "Total Eventos",
        "Eventos Correctos del Sistema",
        "% Eventos Correctos sobre Registrados",
        "% Eventos Correctos sobre Total",
        "Eventos Reg. Mal (Sist.)",
    ]

    zone_image_lookup = {image_data["label"]: image_data for image_data in results["zone_images"]}
    for index, zone_name in enumerate(results["df_grafico"]["Zona"].astype(str).tolist()):
        zone_row = results["df_grafico"][results["df_grafico"]["Zona"].astype(str) == zone_name].copy()
        available_zone_columns = [column for column in zone_columns if column in zone_row.columns]
        zone_table, zone_formatters = prepare_display_dataframe(zone_row, available_zone_columns)
        zone_metrics_row = zone_row.iloc[0]

        with st.expander(zone_name, expanded=(index == 0)):
            render_metric_cards(
                [
                    ("Total Eventos", zone_metrics_row["Total Eventos"]),
                    ("Eventos Correctos del Sistema", zone_metrics_row["Eventos Correctos del Sistema"]),
                    ("% Eventos Correctos sobre Registrados", zone_metrics_row["% Eventos Correctos sobre Registrados"]),
                    ("Eventos Reg. Mal (Sist.)", zone_metrics_row["Eventos Reg. Mal (Sist.)"]),
                ],
                columns_per_row=4,
            )

            detail_table_col, detail_chart_col = st.columns([1.4, 1])
            with detail_table_col:
                st.markdown("**Tabla Principal**")
                render_styled_dataframe(zone_table.style.format(zone_formatters), len(zone_table))
            with detail_chart_col:
                st.markdown("**Grafico de Apoyo**")
                zone_image = zone_image_lookup.get(zone_name)
                if zone_image:
                    st.image(
                        zone_image["buffer"],
                        caption=f"Eventos Correctos del Sistema - {zone_name}",
                        use_container_width=True,
                    )


def render_camera_tab(results: dict):
    st.markdown("#### Analisis de Rendimiento por Camara")
    st.caption(
        "Cada vista sigue el mismo patron: mini resumen, tabla principal, grafico de apoyo y detalle en expanders."
    )

    camera_overview = (
        results["df_grafico"]
        .groupby(CAMERA_COLUMN, dropna=False)
        .agg(
            {
                "Total Eventos": "sum",
                "Eventos Registrados por el Sistema": "sum",
                "Eventos Correctos del Sistema": "sum",
                "Eventos Reg. Mal (Sist.)": "sum",
            }
        )
        .reset_index()
    )
    camera_overview[CAMERA_COLUMN] = camera_overview[CAMERA_COLUMN].apply(format_camera_label)
    camera_overview["% Eventos Correctos sobre Registrados"] = camera_overview.apply(
        lambda row: (
            row["Eventos Correctos del Sistema"] / row["Eventos Registrados por el Sistema"]
            if row["Eventos Registrados por el Sistema"] > 0
            else 0
        ),
        axis=1,
    )
    camera_overview_columns = [
        CAMERA_COLUMN,
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        "% Eventos Correctos sobre Registrados",
        "Eventos Reg. Mal (Sist.)",
    ]
    camera_overview, camera_overview_formatters = prepare_display_dataframe(
        camera_overview,
        camera_overview_columns,
    )

    total_events = camera_overview["Total Eventos"].sum()
    registered_events = camera_overview["Eventos Registrados por el Sistema"].sum()
    correct_events = camera_overview["Eventos Correctos del Sistema"].sum()
    render_metric_cards(
        [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            ("Eventos Correctos del Sistema", correct_events),
            ("% Eventos Correctos sobre Registrados", (correct_events / registered_events) if registered_events > 0 else 0),
        ],
        columns_per_row=4,
    )

    overview_table_col, overview_chart_col = st.columns([1.8, 1])
    with overview_table_col:
        st.markdown("##### Tabla Principal por Camara")
        st.caption("Resumen agregado por camara para identificar rapido donde profundizar.")
        render_styled_dataframe(
            camera_overview.style.format(camera_overview_formatters),
            len(camera_overview),
        )

    with overview_chart_col:
        st.markdown("##### Grafico de Apoyo")
        chart_data = camera_overview.set_index(CAMERA_COLUMN)[
            ["Total Eventos", "Eventos Correctos del Sistema"]
        ]
        st.bar_chart(chart_data, use_container_width=True)

    st.markdown("##### Detalle por Camara")
    st.caption("Cada camara se presenta como un bloque desplegable con su resumen y comparativos por zona.")

    for index, cam in enumerate(results["df_grafico"][CAMERA_COLUMN].unique()):
        cam_label = format_camera_label(cam)
        camera_source_df = results["df_grafico"][results["df_grafico"][CAMERA_COLUMN] == cam].copy()
        total_events = camera_source_df["Total Eventos"].sum()
        registered_events = camera_source_df["Eventos Registrados por el Sistema"].sum()
        correct_events = camera_source_df["Eventos Correctos del Sistema"].sum()
        bad_events = camera_source_df["Eventos Reg. Mal (Sist.)"].sum()
        identity_coverage = (
            camera_source_df["Cobertura Identity"].sum() if "Cobertura Identity" in camera_source_df.columns else 0
        )

        totals_row = pd.DataFrame(
            [[
                "TOTAL CAMARA",
                cam,
                total_events,
                registered_events,
                correct_events,
                (correct_events / registered_events) if registered_events > 0 else 0,
                (correct_events / total_events) if total_events > 0 else 0,
                bad_events,
                (bad_events / registered_events) if registered_events > 0 else 0,
                (identity_coverage / registered_events) if registered_events > 0 else 0,
            ]],
            columns=CAMERA_SUMMARY_COLUMNS,
        )
        camera_table = pd.concat([camera_source_df[CAMERA_SUMMARY_COLUMNS], totals_row], ignore_index=True)
        camera_table, camera_formatters = prepare_display_dataframe(camera_table)

        with st.expander(cam_label, expanded=(index == 0)):
            render_metric_cards(
                [
                    ("Total Eventos", total_events),
                    ("Eventos Registrados por el Sistema", registered_events),
                    ("Eventos Correctos del Sistema", correct_events),
                    ("% Eventos Correctos sobre Registrados", (correct_events / registered_events) if registered_events > 0 else 0),
                ],
                columns_per_row=4,
            )

            table_col, chart_col = st.columns([1.8, 1])

            with table_col:
                st.markdown("##### Tabla General por Zona")
                st.caption(
                    f"Resumen completo de {cam_label}, incluyendo la fila total de la camara."
                )
                render_styled_dataframe(camera_table.style.format(camera_formatters), len(camera_table))

            with chart_col:
                st.markdown("##### Resumen Grafico")
                if index < len(results["cam_summary_images"]):
                    st.image(
                        results["cam_summary_images"][index]["buffer"],
                        caption=f"{cam_label} - Resumen Agregado",
                        use_container_width=True,
                    )

            st.markdown("##### Detalle por Zona")
            detail_left, detail_right = st.columns(2)

            with detail_left:
                st.markdown("**Eventos Correctos del Sistema por Zona**")
                if index < len(results["cam_images"]):
                    st.image(
                        results["cam_images"][index]["buffer"],
                        caption=f"{cam_label} - Eventos Correctos del Sistema por Zona",
                        use_container_width=True,
                    )
                correct_columns = [
                    "Zona",
                    "Total Eventos",
                    "Eventos Correctos del Sistema",
                    "% Eventos Correctos sobre Registrados",
                    "% Eventos Correctos sobre Total",
                ]
                available_correct_columns = [
                    column for column in correct_columns if column in camera_source_df.columns
                ]
                correct_table, correct_formatters = prepare_display_dataframe(
                    camera_source_df,
                    available_correct_columns,
                )
                render_styled_dataframe(
                    correct_table.style.format(correct_formatters),
                    len(correct_table),
                )

            with detail_right:
                st.markdown("**Eventos Registrados por el Sistema por Zona**")
                if index < len(results["cam_coverage_images"]):
                    st.image(
                        results["cam_coverage_images"][index]["buffer"],
                        caption=f"{cam_label} - Eventos Registrados por el Sistema por Zona",
                        use_container_width=True,
                    )
                coverage_columns = [
                    "Zona",
                    "Total Eventos",
                    "Eventos Registrados por el Sistema",
                    "% Eventos Registrados por el Sistema",
                    "Eventos NO Registrados (Manuales)",
                ]
                available_coverage_columns = [
                    column for column in coverage_columns if column in camera_source_df.columns
                ]
                coverage_table, coverage_formatters = prepare_display_dataframe(
                    camera_source_df,
                    available_coverage_columns,
                )
                render_styled_dataframe(
                    coverage_table.style.format(coverage_formatters),
                    len(coverage_table),
                )


def render_unknowns_tab(results: dict):
    st.markdown("#### Registro de Identidades Desconocidas")
    st.caption(
        "Esta vista concentra el resumen de Identity Unknown, el comparativo global y el detalle por zona."
    )

    df_unknown = results["df_grafico"][UNKNOWN_COLUMNS].copy()
    registered_events = df_unknown["Eventos Registrados por el Sistema"].sum()
    unknown_events = df_unknown["Identity Unknown"].sum()
    unknown_rate = (unknown_events / registered_events) if registered_events > 0 else 0
    zones_with_unknown = int(
        (pd.to_numeric(df_unknown["Identity Unknown"], errors="coerce").fillna(0) > 0).sum()
    )

    totals_row = pd.DataFrame(
        [["TOTAL", registered_events, unknown_events, unknown_rate]],
        columns=UNKNOWN_COLUMNS,
    )
    df_unknown = pd.concat([df_unknown, totals_row], ignore_index=True)

    styled = df_unknown.style.format(
        {
            "Eventos Registrados por el Sistema": "{:.0f}",
            "Identity Unknown": "{:.0f}",
            "% Identity Unknown": "{:.2%}",
        }
    )

    summary_columns = st.columns(3)
    summary_metrics = [
        ("Eventos Registrados por el Sistema", registered_events),
        ("Identity Unknown", unknown_events),
        ("% Identity Unknown", unknown_rate),
    ]

    for container, (metric_name, metric_value) in zip(summary_columns, summary_metrics):
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

    table_col, chart_col = st.columns([1.8, 1])

    with table_col:
        st.markdown("##### Tabla General de Identity Unknown por Zona")
        st.caption(
            f"Se identificaron Unknowns en {zones_with_unknown} zona(s). "
            "La tabla principal ocupa el mayor espacio para facilitar la revision completa."
        )
        render_styled_dataframe(styled, len(df_unknown))

    with chart_col:
        st.markdown("##### Resumen Grafico")
        if not results["unknown_images"]:
            st.success("No se detectaron Unknowns en los registros del sistema.")
        if results.get("img_unknown_global"):
            st.image(
                results["img_unknown_global"],
                caption="Identity Unknown - Resumen Global",
                use_container_width=True,
            )
        else:
            st.info("No hay grafico global disponible para esta auditoria.")

    if not results["unknown_images"]:
        return

    st.markdown("---")
    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se presenta como bloque desplegable para revisar solo lo que necesitas.")

    zone_lookup = {
        str(row["Zona"]): row
        for _, row in df_unknown[df_unknown["Zona"] != "TOTAL"].iterrows()
    }
    zone_columns = st.columns(2)

    for index, img_obj in enumerate(results["unknown_images"]):
        zone_name = img_obj["label"]
        zone_row = zone_lookup.get(zone_name)
        detail_lines = []
        if zone_row is not None:
            detail_lines.append(
                f"Eventos Registrados por el Sistema: {int(float(zone_row['Eventos Registrados por el Sistema']))}"
            )
            detail_lines.append(f"Identity Unknown: {int(float(zone_row['Identity Unknown']))}")
            detail_lines.append(
                f"% Identity Unknown: {float(zone_row['% Identity Unknown']):.2%}"
            )

        with zone_columns[index % 2]:
            with st.expander(f"Identity Unknown - {zone_name}", expanded=False):
                if detail_lines:
                    st.caption(" | ".join(detail_lines))
                st.image(
                    img_obj["buffer"],
                    caption=f"Identity Unknown - {zone_name}",
                    use_container_width=True,
                )
                if zone_row is not None:
                    mini_table = pd.DataFrame(
                        [[
                            zone_name,
                            zone_row["Eventos Registrados por el Sistema"],
                            zone_row["Identity Unknown"],
                            zone_row["% Identity Unknown"],
                        ]],
                        columns=[
                            "Zona",
                            "Eventos Registrados por el Sistema",
                            "Identity Unknown",
                            "% Identity Unknown",
                        ],
                    )
                    mini_table["Eventos Registrados por el Sistema"] = pd.to_numeric(
                        mini_table["Eventos Registrados por el Sistema"], errors="coerce"
                    ).fillna(0.0)
                    mini_table["Identity Unknown"] = pd.to_numeric(
                        mini_table["Identity Unknown"], errors="coerce"
                    ).fillna(0.0)
                    mini_table["% Identity Unknown"] = pd.to_numeric(
                        mini_table["% Identity Unknown"], errors="coerce"
                    ).fillna(0.0)

                    st.markdown("**Resumen de la zona**")
                    styled_table = mini_table.style.format(
                        {
                            "Eventos Registrados por el Sistema": "{:.0f}",
                            "Identity Unknown": "{:.0f}",
                            "% Identity Unknown": "{:.2%}",
                        }
                    )
                    render_styled_dataframe(styled_table, len(mini_table))


def render_zone_tab(results: dict):
    st.markdown("#### Desglose por Zona")
    st.caption(
        "Cada vista sigue el mismo patron: mini resumen, tabla principal, grafico de apoyo y detalle en expanders."
    )

    zone_overview_columns = [
        "Zona",
        CAMERA_COLUMN,
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        "Eventos Reg. Mal (Sist.)",
        "% Eventos Correctos sobre Registrados",
        "% Eventos Correctos sobre Total",
    ]
    zone_overview, zone_overview_formatters = prepare_display_dataframe(
        results["df_grafico"],
        [column for column in zone_overview_columns if column in results["df_grafico"].columns],
    )

    total_events = results["df_grafico"]["Total Eventos"].sum()
    registered_events = results["df_grafico"]["Eventos Registrados por el Sistema"].sum()
    correct_events = results["df_grafico"]["Eventos Correctos del Sistema"].sum()
    render_metric_cards(
        [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            ("Eventos Correctos del Sistema", correct_events),
            ("% Eventos Correctos sobre Total", (correct_events / total_events) if total_events > 0 else 0),
        ],
        columns_per_row=4,
    )

    overview_table_col, overview_chart_col = st.columns([1.8, 1])
    with overview_table_col:
        st.markdown("##### Tabla Principal por Zona")
        st.caption("Resumen agregado por zona para revisar rapidamente el comportamiento del sitio.")
        render_styled_dataframe(
            zone_overview.style.format(zone_overview_formatters),
            len(zone_overview),
        )

    with overview_chart_col:
        st.markdown("##### Grafico de Apoyo")
        if results["img_global"]:
            st.image(
                results["img_global"],
                caption="Eventos Correctos del Sistema por Zona",
                use_container_width=True,
            )

    st.markdown("##### Detalle por Zona")
    st.caption("Cada zona se muestra en un bloque desplegable con su resumen, tabla principal y grafico de apoyo.")

    for index, img_data in enumerate(results["zone_images"]):
        zone_name = img_data["label"]
        zone_row = results["df_grafico"][results["df_grafico"]["Zona"] == zone_name].copy()
        zone_table, zone_formatters = prepare_display_dataframe(
            zone_row,
            [column for column in zone_overview_columns if column in zone_row.columns],
        )
        zone_metrics = zone_row.iloc[0]

        with st.expander(zone_name, expanded=(index == 0)):
            render_metric_cards(
                [
                    ("Total Eventos", zone_metrics["Total Eventos"]),
                    ("Eventos Registrados por el Sistema", zone_metrics["Eventos Registrados por el Sistema"]),
                    ("Eventos Correctos del Sistema", zone_metrics["Eventos Correctos del Sistema"]),
                    ("% Eventos Correctos sobre Total", zone_metrics["% Eventos Correctos sobre Total"]),
                ],
                columns_per_row=4,
            )

            detail_table_col, detail_chart_col = st.columns([1.4, 1])
            with detail_table_col:
                st.markdown("**Tabla Principal**")
                render_styled_dataframe(
                    zone_table.style.format(zone_formatters),
                    len(zone_table),
                )
            with detail_chart_col:
                st.markdown("**Grafico de Apoyo**")
                st.image(
                    img_data["buffer"],
                    caption=f"Eventos Correctos del Sistema - {zone_name}",
                    use_container_width=True,
                )


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
            complete_df[column] = pd.to_numeric(complete_df[column], errors="coerce").fillna(0.0)
            base_formatters[column] = "{:.2%}"
        elif column in COUNT_COLUMNS:
            complete_df[column] = pd.to_numeric(complete_df[column], errors="coerce").fillna(0.0)
            base_formatters[column] = "{:.0f}"

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


def render_data_tab(results: dict):
    final_df = results["reporte"].copy()
    blocks_tab, complete_tab = st.tabs(["Tabla Maestra en Bloques", "Tabla Maestra Completa"])

    with blocks_tab:
        st.caption("La tabla se presenta separada por secciones, siguiendo la estructura de la tabla maestra.")

        for section_name, section_columns in DATA_TABLE_SECTIONS.items():
            available_columns = [column for column in section_columns if column in final_df.columns]
            if not available_columns:
                continue

            section_df = final_df[available_columns].copy()
            formatters = {}
            for column in available_columns:
                if str(column).startswith("%"):
                    section_df[column] = pd.to_numeric(section_df[column], errors="coerce").fillna(0.0)
                    formatters[column] = "{:.2%}"
                elif column in COUNT_COLUMNS:
                    section_df[column] = pd.to_numeric(section_df[column], errors="coerce").fillna(0.0)
                    formatters[column] = "{:.0f}"

            render_data_section(section_name, section_df, formatters)

    with complete_tab:
        render_complete_master_table(final_df)


def render_global_and_data_tab(results: dict):
    summary_tab, blocks_tab, complete_tab = st.tabs(
        ["Resumen Global", "Tabla Maestra en Bloques", "Tabla Maestra Completa"]
    )

    with summary_tab:
        render_global_tab(results)

    final_df = results["reporte"].copy()

    with blocks_tab:
        st.caption("La tabla se presenta separada por secciones, siguiendo la estructura de la tabla maestra.")

        for section_name, section_columns in DATA_TABLE_SECTIONS.items():
            available_columns = [column for column in section_columns if column in final_df.columns]
            if not available_columns:
                continue

            section_df = final_df[available_columns].copy()
            formatters = {}
            for column in available_columns:
                if str(column).startswith("%"):
                    section_df[column] = pd.to_numeric(section_df[column], errors="coerce").fillna(0.0)
                    formatters[column] = "{:.2%}"
                elif column in COUNT_COLUMNS:
                    section_df[column] = pd.to_numeric(section_df[column], errors="coerce").fillna(0.0)
                    formatters[column] = "{:.0f}"

            render_data_section(section_name, section_df, formatters)

    with complete_tab:
        render_complete_master_table(final_df)


def render_results(results: dict):
    render_top_metrics(results["df_total"])
    st.markdown("### Analisis Visual")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Analisis Global",
            "Detalle por Camara",
            "Analisis de Unknowns",
            "Detalle por Zona",
        ]
    )

    with tab1:
        render_global_and_data_tab(results)
    with tab2:
        render_camera_tab(results)
    with tab3:
        render_unknowns_tab(results)
    with tab4:
        render_zone_tab(results)

    with open(results["output_xlsx"], "rb") as file:
        st.download_button(
            label="Descargar Reporte Excel Maestro",
            data=file,
            file_name=os.path.basename(results["output_xlsx"]),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_sidebar(base_dir: str):
    st.sidebar.header("Configuracion de Auditoria")

    empresas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    selected_empresa = st.sidebar.selectbox("Seleccione Empresa", empresas)

    empresa_path = os.path.join(base_dir, selected_empresa)
    sucursales = [d for d in os.listdir(empresa_path) if os.path.isdir(os.path.join(empresa_path, d))]
    selected_sucursal = st.sidebar.selectbox("Seleccione Sucursal", sucursales)

    sucursal_path = os.path.join(empresa_path, selected_sucursal)
    fechas = [d for d in os.listdir(sucursal_path) if os.path.isdir(os.path.join(sucursal_path, d))]
    if not fechas:
        st.sidebar.warning("No hay fechas o auditorias para esta sucursal.")
        st.stop()

    selected_fecha = st.sidebar.selectbox("Seleccione Fecha", fechas)
    uploaded_file = st.sidebar.file_uploader("Actualizar datos (opcional)", type=["csv"])
    process_btn = st.sidebar.button("Procesar Auditoria", disabled=(not selected_fecha))

    return selected_empresa, selected_sucursal, selected_fecha, uploaded_file, process_btn


def handle_file_upload(base_dir: str, empresa: str, sucursal: str, fecha: str, uploaded_file):
    if not uploaded_file or not fecha:
        return

    input_path = os.path.join(base_dir, empresa, sucursal, fecha, "input.csv")
    with open(input_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    st.sidebar.success("Archivo actualizado correctamente")


def run_dashboard():
    configure_page()

    base_dir = "Auditorias_Clientes"
    if not os.path.exists(base_dir):
        st.error(f"No se encontro la carpeta base: {base_dir}")
        st.stop()

    empresa, sucursal, fecha, uploaded_file, process_btn = render_sidebar(base_dir)
    render_header(empresa, sucursal, fecha)
    handle_file_upload(base_dir, empresa, sucursal, fecha, uploaded_file)

    if not process_btn or not fecha:
        st.info("Seleccione la empresa y fecha en la barra lateral para comenzar.")
        st.image(
            "https://images.unsplash.com/photo-1551288049-bbbda536339a?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            use_container_width=True,
        )
        return

    with st.spinner("Procesando datos y generando graficos..."):
        results, error = process_audit_data(empresa, fecha, sucursal=sucursal)
        if error:
            st.error(error)
            return
        render_results(results)
