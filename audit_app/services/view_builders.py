"""Prepare dashboard view models outside the Streamlit UI layer."""

from __future__ import annotations

import pandas as pd

from audit_app.domain.kpi_schema import (
    BAD_EVENTS,
    BAD_EVENTS_PCT,
    CAMERA_COLUMN,
    CAMERA_SUMMARY_COLUMNS,
    COUNT_COLUMNS,
    EVENT_PRECISION_PCT,
    GLOBAL_SUMMARY_COLUMNS,
    TOTAL_SUMMARY_COLUMNS,
    UNKNOWN_COLUMNS,
)
from audit_app.services.audit_service import VIEW_MODE_SUCURSAL


def _format_camera_label(cam_value):
    if cam_value in ("", "nan", None):
        return "General"
    try:
        return f"Camara {int(cam_value)}"
    except (TypeError, ValueError):
        return f"Camara {cam_value}"


def _percent_formatter(value):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2%}"


def _count_formatter(value):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.0f}"


def build_display_table(dataframe: pd.DataFrame, columns: list[str] | None = None) -> dict:
    display_df = dataframe[columns].copy() if columns else dataframe.copy()
    formatters = {}

    for column in display_df.columns:
        if str(column).startswith("%"):
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = _percent_formatter
        elif column in COUNT_COLUMNS:
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = _count_formatter

    return {
        "dataframe": display_df,
        "formatters": formatters,
        "row_count": len(display_df),
    }


def build_global_view_data(results: dict) -> dict:
    df_global = results["df_grafico"][GLOBAL_SUMMARY_COLUMNS].copy()
    total_events = pd.to_numeric(df_global["Total Eventos"], errors="coerce").fillna(0).sum()
    correct_events = pd.to_numeric(df_global["Eventos Correctos del Sistema"], errors="coerce").fillna(0).sum()
    bad_events = pd.to_numeric(df_global[BAD_EVENTS], errors="coerce").fillna(0).sum()
    registered_events = results["df_total"]["Eventos Registrados por el Sistema"].iloc[0]

    totals_row = pd.DataFrame(
        [[
            "TOTAL",
            total_events,
            correct_events,
            (correct_events / total_events) if total_events > 0 else 0,
            (correct_events / registered_events) if registered_events > 0 else 0,
            bad_events,
            (bad_events / total_events) if total_events > 0 else 0,
        ]],
        columns=GLOBAL_SUMMARY_COLUMNS,
    )
    df_global = pd.concat([df_global, totals_row], ignore_index=True)

    zone_columns = [
        "Zona",
        "Total Eventos",
        "Eventos Correctos del Sistema",
        EVENT_PRECISION_PCT,
        "% Eventos Correctos sobre Registrados",
        BAD_EVENTS,
    ]
    zone_image_lookup = {image_data["label"]: image_data["buffer"] for image_data in results["zone_images"]}

    zones = []
    for index, zone_name in enumerate(results["df_grafico"]["Zona"].astype(str).tolist()):
        zone_row = results["df_grafico"][results["df_grafico"]["Zona"].astype(str) == zone_name].copy()
        zone_metrics_row = zone_row.iloc[0]
        available_zone_columns = [column for column in zone_columns if column in zone_row.columns]
        zones.append(
            {
                "name": zone_name,
                "expanded": index == 0,
                "metrics": [
                    ("Total Eventos", zone_metrics_row["Total Eventos"]),
                    ("Eventos Correctos del Sistema", zone_metrics_row["Eventos Correctos del Sistema"]),
                    (EVENT_PRECISION_PCT, zone_metrics_row[EVENT_PRECISION_PCT]),
                    (BAD_EVENTS, zone_metrics_row[BAD_EVENTS]),
                ],
                "table": build_display_table(zone_row, available_zone_columns),
                "chart": zone_image_lookup.get(zone_name),
            }
        )

    return {
        "metrics": [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            (EVENT_PRECISION_PCT, (correct_events / total_events) if total_events > 0 else 0),
            (BAD_EVENTS, bad_events),
        ],
        "summary_table": build_display_table(df_global),
        "totals_table": build_display_table(results["df_total"], TOTAL_SUMMARY_COLUMNS),
        "summary_chart": results["img_totales"],
        "zones": zones,
    }


def build_date_view_data(results: dict) -> dict | None:
    if results.get("view_mode") != VIEW_MODE_SUCURSAL:
        return None

    detail_df = results["reporte"].copy()
    detail_df = detail_df[detail_df["Zona"] != "TOTAL"].copy()
    detail_df = detail_df[detail_df["Fecha"].astype(str).str.strip() != ""].copy()
    if detail_df.empty:
        return {"available": False}

    overview = (
        detail_df.groupby("Fecha", dropna=False)
        .agg(
            {
                "Total Eventos": "sum",
                "Eventos Registrados por el Sistema": "sum",
                "Eventos Correctos del Sistema": "sum",
                BAD_EVENTS: "sum",
            }
        )
        .reset_index()
    )
    overview[EVENT_PRECISION_PCT] = overview.apply(
        lambda row: (row["Eventos Correctos del Sistema"] / row["Total Eventos"]) if row["Total Eventos"] > 0 else 0,
        axis=1,
    )
    overview["% Eventos Correctos sobre Registrados"] = overview.apply(
        lambda row: (
            row["Eventos Correctos del Sistema"] / row["Eventos Registrados por el Sistema"]
            if row["Eventos Registrados por el Sistema"] > 0
            else 0
        ),
        axis=1,
    )

    overview_columns = [
        "Fecha",
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        EVENT_PRECISION_PCT,
        BAD_EVENTS,
    ]
    date_detail_columns = [
        "Fecha",
        "Hora_inicio",
        "Hora_termino",
        CAMERA_COLUMN,
        "Zona",
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        EVENT_PRECISION_PCT,
        BAD_EVENTS,
    ]
    hourly_columns = [
        "Hora_inicio",
        "Hora_termino",
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        BAD_EVENTS,
    ]

    total_events = overview["Total Eventos"].sum()
    registered_events = overview["Eventos Registrados por el Sistema"].sum()
    correct_events = overview["Eventos Correctos del Sistema"].sum()

    dates = []
    for index, fecha in enumerate(sorted(detail_df["Fecha"].astype(str).unique().tolist())):
        date_rows = detail_df[detail_df["Fecha"].astype(str) == fecha].copy()
        date_total_events = pd.to_numeric(date_rows["Total Eventos"], errors="coerce").fillna(0).sum()
        date_registered_events = pd.to_numeric(
            date_rows["Eventos Registrados por el Sistema"],
            errors="coerce",
        ).fillna(0).sum()
        date_correct_events = pd.to_numeric(
            date_rows["Eventos Correctos del Sistema"],
            errors="coerce",
        ).fillna(0).sum()

        date_chart = (
            date_rows.groupby("Zona", dropna=False)[
                ["Total Eventos", "Eventos Correctos del Sistema"]
            ]
            .sum()
        )
        hourly_detail = (
            date_rows.groupby(["Hora_inicio", "Hora_termino"], dropna=False)
            .agg(
                {
                    "Total Eventos": "sum",
                    "Eventos Registrados por el Sistema": "sum",
                    "Eventos Correctos del Sistema": "sum",
                    BAD_EVENTS: "sum",
                }
            )
            .reset_index()
        )

        dates.append(
            {
                "label": fecha,
                "expanded": index == 0,
                "metrics": [
                    ("Total Eventos", date_total_events),
                    ("Eventos Registrados por el Sistema", date_registered_events),
                    ("Eventos Correctos del Sistema", date_correct_events),
                    (EVENT_PRECISION_PCT, (date_correct_events / date_total_events) if date_total_events > 0 else 0),
                ],
                "table": build_display_table(
                    date_rows,
                    [column for column in date_detail_columns if column in date_rows.columns],
                ),
                "chart": {
                    "labels": date_chart.index.astype(str).tolist(),
                    "base_values": pd.to_numeric(date_chart["Total Eventos"], errors="coerce").fillna(0).tolist(),
                    "result_values": pd.to_numeric(
                        date_chart["Eventos Correctos del Sistema"],
                        errors="coerce",
                    ).fillna(0).tolist(),
                    "title": f"Eventos Correctos del Sistema por Zona - {fecha}",
                },
                "hourly_table": build_display_table(hourly_detail, hourly_columns),
            }
        )

    return {
        "available": True,
        "metrics": [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            ("Eventos Correctos del Sistema", correct_events),
            (EVENT_PRECISION_PCT, (correct_events / total_events) if total_events > 0 else 0),
        ],
        "overview_table": build_display_table(overview, overview_columns),
        "overview_chart": {
            "labels": overview["Fecha"].astype(str).tolist(),
            "base_values": pd.to_numeric(overview["Total Eventos"], errors="coerce").fillna(0).tolist(),
            "result_values": pd.to_numeric(
                overview["Eventos Correctos del Sistema"],
                errors="coerce",
            ).fillna(0).tolist(),
            "title": "Eventos Correctos del Sistema por Fecha",
        },
        "dates": dates,
    }


def build_camera_view_data(results: dict) -> dict:
    camera_overview = (
        results["df_grafico"]
        .groupby(CAMERA_COLUMN, dropna=False)
        .agg(
            {
                "Total Eventos": "sum",
                "Eventos Registrados por el Sistema": "sum",
                "Eventos Correctos del Sistema": "sum",
                BAD_EVENTS: "sum",
            }
        )
        .reset_index()
    )
    camera_overview[CAMERA_COLUMN] = camera_overview[CAMERA_COLUMN].apply(_format_camera_label)
    camera_overview[EVENT_PRECISION_PCT] = camera_overview.apply(
        lambda row: (
            row["Eventos Correctos del Sistema"] / row["Total Eventos"]
            if row["Total Eventos"] > 0
            else 0
        ),
        axis=1,
    )

    camera_overview_columns = [
        CAMERA_COLUMN,
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        EVENT_PRECISION_PCT,
        BAD_EVENTS,
    ]
    summary_image_lookup = {
        image_data["label"]: image_data["buffer"] for image_data in results["cam_summary_images"]
    }
    correct_image_lookup = {
        image_data["label"]: image_data["buffer"] for image_data in results["cam_images"]
    }
    coverage_image_lookup = {
        image_data["label"]: image_data["buffer"] for image_data in results["cam_coverage_images"]
    }

    cameras = []
    for index, cam in enumerate(results["df_grafico"][CAMERA_COLUMN].unique()):
        cam_label = _format_camera_label(cam)
        camera_source_df = results["df_grafico"][results["df_grafico"][CAMERA_COLUMN] == cam].copy()
        total_events = camera_source_df["Total Eventos"].sum()
        registered_events = camera_source_df["Eventos Registrados por el Sistema"].sum()
        correct_events = camera_source_df["Eventos Correctos del Sistema"].sum()
        bad_events = camera_source_df[BAD_EVENTS].sum()
        identity_coverage = (
            pd.to_numeric(camera_source_df["Cobertura Identity"], errors="coerce").sum(min_count=1)
            if "Cobertura Identity" in camera_source_df.columns
            else None
        )
        identity_unknown = (
            pd.to_numeric(camera_source_df["Identity Unknown"], errors="coerce").sum(min_count=1)
            if "Identity Unknown" in camera_source_df.columns
            else None
        )
        identity_total = None
        if pd.notna(identity_coverage) or pd.notna(identity_unknown):
            identity_total = (identity_coverage or 0) + (identity_unknown or 0)

        totals_row = pd.DataFrame(
            [[
                "TOTAL CAMARA",
                cam,
                total_events,
                registered_events,
                correct_events,
                (correct_events / total_events) if total_events > 0 else 0,
                (correct_events / registered_events) if registered_events > 0 else 0,
                bad_events,
                (bad_events / total_events) if total_events > 0 else 0,
                ((identity_coverage or 0) / identity_total) if identity_total and identity_total > 0 else None,
            ]],
            columns=CAMERA_SUMMARY_COLUMNS,
        )
        camera_table = pd.concat([camera_source_df[CAMERA_SUMMARY_COLUMNS], totals_row], ignore_index=True)

        correct_columns = [
            "Zona",
            "Total Eventos",
            "Eventos Correctos del Sistema",
            EVENT_PRECISION_PCT,
            "% Eventos Correctos sobre Registrados",
        ]
        coverage_columns = [
            "Zona",
            "Total Eventos",
            "Eventos Registrados por el Sistema",
            "% Eventos Registrados por el Sistema",
            "Eventos NO Registrados (Manuales)",
        ]

        cameras.append(
            {
                "label": cam_label,
                "expanded": index == 0,
                "metrics": [
                    ("Total Eventos", total_events),
                    ("Eventos Registrados por el Sistema", registered_events),
                    ("Eventos Correctos del Sistema", correct_events),
                    (EVENT_PRECISION_PCT, (correct_events / total_events) if total_events > 0 else 0),
                ],
                "summary_table": build_display_table(camera_table),
                "summary_chart": summary_image_lookup.get(cam_label),
                "correct_chart": correct_image_lookup.get(cam_label),
                "coverage_chart": coverage_image_lookup.get(cam_label),
                "correct_table": build_display_table(
                    camera_source_df,
                    [column for column in correct_columns if column in camera_source_df.columns],
                ),
                "coverage_table": build_display_table(
                    camera_source_df,
                    [column for column in coverage_columns if column in camera_source_df.columns],
                ),
            }
        )

    total_registered = camera_overview["Eventos Registrados por el Sistema"].sum()
    total_correct = camera_overview["Eventos Correctos del Sistema"].sum()
    total_events = camera_overview["Total Eventos"].sum()

    return {
        "metrics": [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", total_registered),
            ("Eventos Correctos del Sistema", total_correct),
            (EVENT_PRECISION_PCT, (total_correct / total_events) if total_events > 0 else 0),
        ],
        "overview_table": build_display_table(camera_overview, camera_overview_columns),
        "overview_chart": {
            "labels": camera_overview[CAMERA_COLUMN].astype(str).tolist(),
            "base_values": pd.to_numeric(camera_overview["Total Eventos"], errors="coerce").fillna(0).tolist(),
            "result_values": pd.to_numeric(
                camera_overview["Eventos Correctos del Sistema"],
                errors="coerce",
            ).fillna(0).tolist(),
            "title": "Eventos Correctos del Sistema por Camara",
        },
        "cameras": cameras,
    }


def build_unknowns_view_data(results: dict) -> dict:
    source_df = results["df_grafico"].copy()
    applicable_df = source_df[source_df["% Identity Unknown"].notna()].copy()
    if applicable_df.empty:
        return {
            "metrics": [
                ("Eventos evaluables (Identity)", 0),
                ("Identity Unknown", 0),
                ("% Identity Unknown", None),
            ],
            "zones_with_unknown": 0,
            "summary_table": build_display_table(pd.DataFrame(columns=UNKNOWN_COLUMNS), UNKNOWN_COLUMNS),
            "summary_chart": None,
            "has_unknowns": False,
            "zones": [],
        }

    applicable_df["Eventos Registrados por el Sistema"] = (
        pd.to_numeric(applicable_df["Cobertura Identity"], errors="coerce").fillna(0)
        + pd.to_numeric(applicable_df["Identity Unknown"], errors="coerce").fillna(0)
    )
    df_unknown = applicable_df[UNKNOWN_COLUMNS].copy()
    registered_events = df_unknown["Eventos Registrados por el Sistema"].sum()
    unknown_events = pd.to_numeric(df_unknown["Identity Unknown"], errors="coerce").fillna(0).sum()
    unknown_rate = (unknown_events / registered_events) if registered_events > 0 else 0
    zones_with_unknown = int(
        (pd.to_numeric(df_unknown["Identity Unknown"], errors="coerce").fillna(0) > 0).sum()
    )

    totals_row = pd.DataFrame(
        [["TOTAL", registered_events, unknown_events, unknown_rate]],
        columns=UNKNOWN_COLUMNS,
    )
    df_unknown = pd.concat([df_unknown, totals_row], ignore_index=True)
    zone_lookup = {
        str(row["Zona"]): row
        for _, row in df_unknown[df_unknown["Zona"] != "TOTAL"].iterrows()
    }

    zones = []
    for img_obj in results["unknown_images"]:
        zone_name = img_obj["label"]
        zone_row = zone_lookup.get(zone_name)
        mini_table = None
        detail_caption = None

        if zone_row is not None:
            detail_caption = " | ".join(
                [
                    f"Eventos evaluables: {int(float(zone_row['Eventos Registrados por el Sistema']))}",
                    f"Identity Unknown: {int(float(zone_row['Identity Unknown']))}",
                    f"% Identity Unknown: {float(zone_row['% Identity Unknown']):.2%}",
                ]
            )
            mini_table = build_display_table(
                pd.DataFrame(
                    [[
                        zone_name,
                        zone_row["Eventos Registrados por el Sistema"],
                        zone_row["Identity Unknown"],
                        zone_row["% Identity Unknown"],
                    ]],
                    columns=UNKNOWN_COLUMNS,
                )
            )

        zones.append(
            {
                "label": zone_name,
                "caption": detail_caption,
                "chart": img_obj["buffer"],
                "table": mini_table,
            }
        )

    return {
        "metrics": [
            ("Eventos evaluables (Identity)", registered_events),
            ("Identity Unknown", unknown_events),
            ("% Identity Unknown", unknown_rate),
        ],
        "zones_with_unknown": zones_with_unknown,
        "summary_table": build_display_table(df_unknown, UNKNOWN_COLUMNS),
        "summary_chart": results.get("img_unknown_global"),
        "has_unknowns": bool(results["unknown_images"]),
        "zones": zones,
    }


def build_zone_view_data(results: dict) -> dict:
    zone_overview_columns = [
        "Zona",
        CAMERA_COLUMN,
        "Total Eventos",
        "Eventos Registrados por el Sistema",
        "Eventos Correctos del Sistema",
        BAD_EVENTS,
        EVENT_PRECISION_PCT,
        "% Eventos Correctos sobre Registrados",
    ]

    zones_data = []
    for img_data in results["zone_images"]:
        zone_name = img_data["label"]
        zone_row = results["df_grafico"][results["df_grafico"]["Zona"] == zone_name].copy()
        if zone_row.empty:
            continue
        cam = zone_row.iloc[0].get(CAMERA_COLUMN, "General")
        cam_label = _format_camera_label(cam)

        zone_metrics = zone_row.iloc[0]
        zones_data.append(
            {
                "camera_label": cam_label,
                "label": zone_name,
                "metrics": [
                    ("Total Eventos", zone_metrics["Total Eventos"]),
                    ("Eventos Registrados por el Sistema", zone_metrics["Eventos Registrados por el Sistema"]),
                    ("Eventos Correctos del Sistema", zone_metrics["Eventos Correctos del Sistema"]),
                    (EVENT_PRECISION_PCT, zone_metrics[EVENT_PRECISION_PCT]),
                ],
                "table": build_display_table(
                    zone_row,
                    [column for column in zone_overview_columns if column in zone_row.columns],
                ),
                "chart": img_data["buffer"],
                "raw_metrics": zone_metrics,
            }
        )

    cameras_dict = {}
    for zone_item in zones_data:
        cam_label = zone_item["camera_label"]
        cameras_dict.setdefault(cam_label, []).append(zone_item)

    cameras = []
    for index, (cam_label, cam_zones) in enumerate(cameras_dict.items()):
        summary_rows = []
        for zone_item in cam_zones:
            metrics = zone_item["raw_metrics"]
            total_eventos = metrics.get("Total Eventos", 0)
            correct_sistema = metrics.get("Eventos Correctos del Sistema", 0)
            no_reg = metrics.get("Eventos NO Registrados (Manuales)", 0)
            pct_precision = metrics.get(EVENT_PRECISION_PCT, 0)
            if pd.isna(pct_precision):
                pct_precision = 0

            try:
                x_val = int(round(float(correct_sistema)))
                y_val = int(round(float(total_eventos)))
                pct_val = float(pct_precision)
                precision_str = f"{x_val} de {y_val} ({pct_val:.2%})"
            except Exception:
                precision_str = "0 de 0 (0.00%)"

            summary_rows.append(
                {
                    "Zona": zone_item["label"],
                    "Total eventos": int(round(float(total_eventos))) if pd.notna(total_eventos) else 0,
                    "Precisión de eventos": precision_str,
                    "Eventos no registrados por el sistema": int(round(float(no_reg))) if pd.notna(no_reg) else 0,
                }
            )

        summary_df = pd.DataFrame(summary_rows)

        cameras.append(
            {
                "camera_label": cam_label,
                "expanded": index == 0,
                "summary_table": build_display_table(summary_df),
                "zones": cam_zones,
            }
        )

    total_events = results["df_grafico"]["Total Eventos"].sum()
    registered_events = results["df_grafico"]["Eventos Registrados por el Sistema"].sum()
    correct_events = results["df_grafico"]["Eventos Correctos del Sistema"].sum()

    return {
        "metrics": [
            ("Total Eventos", total_events),
            ("Eventos Registrados por el Sistema", registered_events),
            ("Eventos Correctos del Sistema", correct_events),
            (EVENT_PRECISION_PCT, (correct_events / total_events) if total_events > 0 else 0),
        ],
        "overview_table": build_display_table(
            results["df_grafico"],
            [column for column in zone_overview_columns if column in results["df_grafico"].columns],
        ),
        "overview_chart": results["img_global"],
        "cameras": cameras,
    }


def build_dashboard_view_models(results: dict) -> dict:
    return {
        "global": build_global_view_data(results),
        "dates": build_date_view_data(results),
        "camera": build_camera_view_data(results),
        "unknowns": build_unknowns_view_data(results),
        "zone": build_zone_view_data(results),
    }
