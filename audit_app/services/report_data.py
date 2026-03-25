"""Curated data models for the final audit report view."""

from __future__ import annotations

import pandas as pd

from audit_app.domain.kpi_schema import AGE_PRECISION, CAMERA_COLUMN, GENDER_COVERAGE, GENDER_PRECISION

DISPLAY_CAMERA_COLUMN = "Camara"
ZONE_TYPE_COLUMN = "Tipo de zona"
LINE_TYPE_COLUMN = "Tipo de linea"
TRAMO_COLUMN = "Tramo"
PERIODO_COLUMN = "Periodo"
MISREGISTERED_COLUMN = "Eventos mal registrados"
SUBREGISTER_PCT_COLUMN = "Subregistro"
IDENTITY_CONSIDERED_COLUMN = "Registrados considerados para Identity"
ATTRIBUTE_CONSIDERED_COLUMN = "Registrados considerados para atributos"
ATTRIBUTE_ZONE_TYPES = {"Linea de entrada", "Zona de permanencia"}


def _format_count(value):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.0f}"


def _format_percent(value):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2%}"


def _build_table_model(
    dataframe: pd.DataFrame,
    percent_columns: list[str] | None = None,
    count_columns: list[str] | None = None,
) -> dict:
    display_df = dataframe.copy()
    formatters = {}

    for column in percent_columns or []:
        if column in display_df.columns:
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = _format_percent

    for column in count_columns or []:
        if column in display_df.columns:
            display_df[column] = pd.to_numeric(display_df[column], errors="coerce")
            formatters[column] = _format_count

    return {"dataframe": display_df, "formatters": formatters, "row_count": len(display_df)}


def _build_plain_table_model(dataframe: pd.DataFrame) -> dict:
    return {"dataframe": dataframe.copy(), "formatters": {}, "row_count": len(dataframe)}


def _normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip().lower()


def _safe_sum(series: pd.Series) -> float:
    return pd.to_numeric(series, errors="coerce").fillna(0).sum()


def _safe_pct(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _format_camera_value(value) -> str:
    if value in ("", "nan", None) or pd.isna(value):
        return "General"
    try:
        return f"Camara {int(value)}"
    except (TypeError, ValueError):
        return f"Camara {value}"


def _build_tramo_label(fecha: str, hora_inicio: str, hora_termino: str) -> str:
    if hora_inicio and hora_termino:
        return f"{hora_inicio} - {hora_termino}"
    if hora_inicio:
        return hora_inicio
    return fecha or "Sin tramo"


def _build_periodo_label(fecha: str, tramo: str) -> str:
    if fecha and tramo and tramo != fecha:
        return f"{fecha} | {tramo}"
    return fecha or tramo or "Sin periodo"


def _classify_zone_type(sensor_type: str, zone_name: str) -> str:
    normalized_sensor = _normalize_text(sensor_type)
    normalized_zone = _normalize_text(zone_name)
    if normalized_sensor == "zona_permanencia":
        return "Zona de permanencia"
    if normalized_sensor == "linea_conteo" and "entrada" in normalized_zone:
        return "Linea de entrada"
    if normalized_sensor == "linea_conteo" and "exterior" in normalized_zone:
        return "Linea exterior"
    if normalized_sensor == "linea_conteo":
        return "Linea de conteo"
    return "Otro"


def _line_type_for_row(zone_type: str) -> str:
    if zone_type == "Linea exterior":
        return "Exterior"
    if zone_type == "Linea de entrada":
        return "Entrada"
    if zone_type == "Linea de conteo":
        return "Conteo"
    return ""


def _prepare_detail_dataframe(results: dict) -> pd.DataFrame:
    detail_df = results["reporte"].copy()
    detail_df = detail_df[detail_df["Zona"].astype(str).str.upper() != "TOTAL"].copy()
    if detail_df.empty:
        return detail_df

    detail_df[DISPLAY_CAMERA_COLUMN] = detail_df[CAMERA_COLUMN].apply(_format_camera_value)
    detail_df[TRAMO_COLUMN] = detail_df.apply(
        lambda row: _build_tramo_label(
            str(row.get("Fecha", "") or ""),
            str(row.get("Hora_inicio", "") or ""),
            str(row.get("Hora_termino", "") or ""),
        ),
        axis=1,
    )
    detail_df[PERIODO_COLUMN] = detail_df.apply(
        lambda row: _build_periodo_label(str(row.get("Fecha", "") or ""), str(row.get(TRAMO_COLUMN, "") or "")),
        axis=1,
    )
    detail_df[ZONE_TYPE_COLUMN] = detail_df.apply(
        lambda row: _classify_zone_type(row.get("Tipo_sensor", ""), row.get("Zona", "")),
        axis=1,
    )
    detail_df[LINE_TYPE_COLUMN] = detail_df[ZONE_TYPE_COLUMN].apply(_line_type_for_row)
    detail_df[MISREGISTERED_COLUMN] = (
        pd.to_numeric(detail_df["Eventos Registrados por el Sistema"], errors="coerce").fillna(0)
        - pd.to_numeric(detail_df["Eventos Correctos del Sistema"], errors="coerce").fillna(0)
    ).clip(lower=0)
    total_events = pd.to_numeric(detail_df["Total Eventos"], errors="coerce")
    not_registered = pd.to_numeric(detail_df["Eventos NO Registrados (Manuales)"], errors="coerce").fillna(0)
    detail_df[SUBREGISTER_PCT_COLUMN] = not_registered.div(total_events.where(total_events > 0))

    identity_coverage = pd.to_numeric(detail_df["Cobertura Identity"], errors="coerce")
    identity_unknown = pd.to_numeric(detail_df["Identity Unknown"], errors="coerce")
    attribute_applicable = detail_df[ZONE_TYPE_COLUMN].isin(ATTRIBUTE_ZONE_TYPES)
    identity_considered = identity_coverage.fillna(0) + identity_unknown.fillna(0)
    detail_df[IDENTITY_CONSIDERED_COLUMN] = identity_considered
    detail_df.loc[
        ~attribute_applicable | (identity_coverage.isna() & identity_unknown.isna()),
        IDENTITY_CONSIDERED_COLUMN,
    ] = pd.NA
    detail_df[ATTRIBUTE_CONSIDERED_COLUMN] = detail_df[IDENTITY_CONSIDERED_COLUMN]
    return detail_df


def _apply_filters(detail_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    filtered_df = detail_df.copy()
    if filtered_df.empty:
        return filtered_df

    if filters.get("fecha") and filters["fecha"] != "Todas":
        filtered_df = filtered_df[filtered_df["Fecha"].astype(str) == filters["fecha"]]
    if filters.get("tramo") and filters["tramo"] != "Todos":
        filtered_df = filtered_df[filtered_df[TRAMO_COLUMN].astype(str) == filters["tramo"]]
    if filters.get("camara") and filters["camara"] != "Todas":
        filtered_df = filtered_df[filtered_df[DISPLAY_CAMERA_COLUMN].astype(str) == filters["camara"]]
    if filters.get("zona") and filters["zona"] != "Todas":
        filtered_df = filtered_df[filtered_df["Zona"].astype(str) == filters["zona"]]
    if filters.get("tipo_zona") and filters["tipo_zona"] != "Todos":
        filtered_df = filtered_df[filtered_df[ZONE_TYPE_COLUMN].astype(str) == filters["tipo_zona"]]

    return filtered_df


def _build_filter_options(detail_df: pd.DataFrame, results: dict) -> dict:
    if detail_df.empty:
        return {
            "empresa": [results.get("empresa", "") or "N/D"],
            "sucursal": [results.get("sucursal", "") or "N/D"],
            "modo": [results.get("view_mode", "") or "N/D"],
            "fecha": ["Todas"],
            "tramo": ["Todos"],
            "camara": ["Todas"],
            "zona": ["Todas"],
            "tipo_zona": ["Todos"],
        }

    return {
        "empresa": [results.get("empresa", "") or "N/D"],
        "sucursal": [results.get("sucursal", "") or "N/D"],
        "modo": [results.get("view_mode", "") or "N/D"],
        "fecha": ["Todas"] + sorted(detail_df["Fecha"].astype(str).dropna().unique().tolist()),
        "tramo": ["Todos"] + sorted(detail_df[TRAMO_COLUMN].astype(str).dropna().unique().tolist()),
        "camara": ["Todas"] + sorted(detail_df[DISPLAY_CAMERA_COLUMN].astype(str).dropna().unique().tolist()),
        "zona": ["Todas"] + sorted(detail_df["Zona"].astype(str).dropna().unique().tolist()),
        "tipo_zona": ["Todos"] + sorted(detail_df[ZONE_TYPE_COLUMN].astype(str).dropna().unique().tolist()),
    }


def _build_brief_reading(precision_total: float | None, subregister_pct: float | None, zone_type: str | None = None) -> str:
    notes = []
    if precision_total is None:
        notes.append("Sin base suficiente.")
    elif precision_total >= 0.95:
        notes.append("Precision alta.")
    elif precision_total >= 0.85:
        notes.append("Precision estable.")
    else:
        notes.append("Precision baja.")

    if subregister_pct is not None and subregister_pct > 0.10:
        notes.append("Subregistro relevante.")
    elif subregister_pct is not None and subregister_pct > 0:
        notes.append("Subregistro acotado.")

    if zone_type == "Linea exterior":
        notes.append("Validado por contador.")
    elif zone_type == "Linea de entrada":
        notes.append("Incluye atributos.")
    elif zone_type == "Zona de permanencia":
        notes.append("Lectura de permanencia.")

    return " ".join(notes)


def _aggregate_scope(filtered_df: pd.DataFrame) -> dict:
    total_events = _safe_sum(filtered_df["Total Eventos"])
    registered = _safe_sum(filtered_df["Eventos Registrados por el Sistema"])
    not_registered = _safe_sum(filtered_df["Eventos NO Registrados (Manuales)"])
    correct = _safe_sum(filtered_df["Eventos Correctos del Sistema"])
    misregistered = max(registered - correct, 0)

    identity_df = filtered_df[filtered_df[IDENTITY_CONSIDERED_COLUMN].notna()].copy()
    identity_considered = _safe_sum(identity_df[IDENTITY_CONSIDERED_COLUMN])
    identity_coverage = _safe_sum(identity_df["Cobertura Identity"])
    identity_unknown = _safe_sum(identity_df["Identity Unknown"])

    attribute_df = filtered_df[filtered_df[ATTRIBUTE_CONSIDERED_COLUMN].notna()].copy()
    attribute_considered = _safe_sum(attribute_df[ATTRIBUTE_CONSIDERED_COLUMN])
    gender_coverage = _safe_sum(attribute_df[GENDER_COVERAGE])
    gender_precision = _safe_sum(attribute_df[GENDER_PRECISION])
    age_coverage = _safe_sum(attribute_df["Cobertura Edad"])
    age_precision = _safe_sum(attribute_df[AGE_PRECISION])

    return {
        "total_events": total_events,
        "registered": registered,
        "not_registered": not_registered,
        "correct": correct,
        "misregistered": misregistered,
        "precision_total": _safe_pct(correct, total_events),
        "precision_registered": _safe_pct(correct, registered),
        "subregister": _safe_pct(not_registered, total_events),
        "identity_considered": identity_considered,
        "identity_coverage": identity_coverage,
        "identity_unknown": identity_unknown,
        "identity_coverage_pct": _safe_pct(identity_coverage, identity_considered),
        "identity_unknown_pct": _safe_pct(identity_unknown, identity_considered),
        "attribute_considered": attribute_considered,
        "gender_coverage": gender_coverage,
        "gender_coverage_pct": _safe_pct(gender_coverage, attribute_considered),
        "gender_precision": gender_precision,
        "gender_precision_pct": _safe_pct(gender_precision, gender_coverage),
        "age_coverage": age_coverage,
        "age_coverage_pct": _safe_pct(age_coverage, attribute_considered),
        "age_precision": age_precision,
        "age_precision_pct": _safe_pct(age_precision, age_coverage),
    }


def _build_kpi_table(scope: dict) -> dict:
    rows = [
        ("Total eventos auditados", _format_count(scope["total_events"]), "Base principal del informe."),
        ("Eventos registrados por el sistema", _format_count(scope["registered"]), "Eventos detectados por el sistema."),
        ("Eventos no registrados por el sistema", _format_count(scope["not_registered"]), "Subregistro que baja la precision."),
        ("Eventos correctos del sistema", _format_count(scope["correct"]), "Eventos correctamente capturados."),
        ("Eventos mal registrados", _format_count(scope["misregistered"]), "Registrados pero incorrectos."),
        ("Precision sobre total auditado", _format_percent(scope["precision_total"]), "Metrica principal del informe."),
        ("Precision sobre registrados", _format_percent(scope["precision_registered"]), "Metrica complementaria."),
        ("Subregistro", _format_percent(scope["subregister"]), "No registrados sobre total auditado."),
        ("Cobertura Identity", f"{_format_count(scope['identity_coverage'])} ({_format_percent(scope['identity_coverage_pct'])})", "Identity con valor conocido."),
        ("Identity Unknown", f"{_format_count(scope['identity_unknown'])} ({_format_percent(scope['identity_unknown_pct'])})", "Identity registrado como unknown."),
        ("Cobertura Genero", f"{_format_count(scope['gender_coverage'])} ({_format_percent(scope['gender_coverage_pct'])})", "Solo entrada y permanencia."),
        ("Precision Genero", f"{_format_count(scope['gender_precision'])} ({_format_percent(scope['gender_precision_pct'])})", "N/A cuando la cobertura es 0."),
        ("Cobertura Edad", f"{_format_count(scope['age_coverage'])} ({_format_percent(scope['age_coverage_pct'])})", "Solo entrada y permanencia."),
        ("Precision Edad", f"{_format_count(scope['age_precision'])} ({_format_percent(scope['age_precision_pct'])})", "N/A cuando la cobertura es 0."),
    ]
    kpi_df = pd.DataFrame(rows, columns=["Indicador", "Resultado", "Lectura"])
    return _build_plain_table_model(kpi_df)


def _aggregate_zone_block(group_df: pd.DataFrame) -> pd.Series:
    total_events = _safe_sum(group_df["Total Eventos"])
    registered = _safe_sum(group_df["Eventos Registrados por el Sistema"])
    not_registered = _safe_sum(group_df["Eventos NO Registrados (Manuales)"])
    correct = _safe_sum(group_df["Eventos Correctos del Sistema"])
    misregistered = max(registered - correct, 0)
    precision_registered = _safe_pct(correct, registered)
    precision_total = _safe_pct(correct, total_events)
    subregister = _safe_pct(not_registered, total_events)
    zone_type = group_df[ZONE_TYPE_COLUMN].iloc[0] if ZONE_TYPE_COLUMN in group_df.columns else ""

    return pd.Series(
        {
            "Total eventos auditados": total_events,
            "Eventos registrados": registered,
            "Eventos no registrados": not_registered,
            "Eventos correctos": correct,
            MISREGISTERED_COLUMN: misregistered,
            "Precision sobre registrados": precision_registered,
            "Precision sobre total": precision_total,
            SUBREGISTER_PCT_COLUMN: subregister,
            "Lectura breve": _build_brief_reading(precision_total, subregister, zone_type),
        }
    )


def _group_zone_table(source_df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    rows = []
    for group_key, group_df in source_df.groupby(group_columns, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = _aggregate_zone_block(group_df).to_dict()
        row.update(dict(zip(group_columns, group_key)))
        rows.append(row)
    return pd.DataFrame(rows)


def _build_lines_table(filtered_df: pd.DataFrame) -> dict:
    lines_df = filtered_df[filtered_df[ZONE_TYPE_COLUMN].isin(["Linea exterior", "Linea de entrada", "Linea de conteo"])].copy()
    if lines_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    grouped = _group_zone_table(lines_df, [DISPLAY_CAMERA_COLUMN, "Zona", LINE_TYPE_COLUMN, ZONE_TYPE_COLUMN])
    grouped.rename(columns={LINE_TYPE_COLUMN: "Tipo de linea"}, inplace=True)
    grouped = grouped[
        [
            DISPLAY_CAMERA_COLUMN,
            "Zona",
            "Tipo de linea",
            "Total eventos auditados",
            "Eventos registrados",
            "Eventos no registrados",
            "Eventos correctos",
            MISREGISTERED_COLUMN,
            "Precision sobre registrados",
            "Precision sobre total",
            SUBREGISTER_PCT_COLUMN,
            "Lectura breve",
        ]
    ]
    return _build_table_model(
        grouped,
        percent_columns=["Precision sobre registrados", "Precision sobre total", SUBREGISTER_PCT_COLUMN],
        count_columns=["Total eventos auditados", "Eventos registrados", "Eventos no registrados", "Eventos correctos", MISREGISTERED_COLUMN],
    )


def _build_flow_balance(filtered_df: pd.DataFrame) -> dict:
    lines_df = filtered_df[filtered_df[ZONE_TYPE_COLUMN].isin(["Linea exterior", "Linea de entrada"])].copy()
    if lines_df.empty:
        return {"table": _build_plain_table_model(pd.DataFrame()), "chart": None, "available": False}

    rows = []
    for keys, period_df in lines_df.groupby(["Fecha", TRAMO_COLUMN], dropna=False):
        fecha, tramo = keys
        period_label = _build_periodo_label(str(fecha or ""), str(tramo or ""))
        entradas = _safe_sum(period_df.loc[period_df[ZONE_TYPE_COLUMN] == "Linea de entrada", "Total Eventos"])
        salidas = _safe_sum(period_df.loc[period_df[ZONE_TYPE_COLUMN] == "Linea exterior", "Total Eventos"])
        rows.append(
            {
                "Fecha": fecha,
                "Tramo / jornada": tramo,
                PERIODO_COLUMN: period_label,
                "Entradas": entradas,
                "Salidas": salidas,
                "Margen de error": _safe_pct(abs(entradas - salidas), entradas),
            }
        )

    flow_df = pd.DataFrame(rows).sort_values(by=["Fecha", "Tramo / jornada"]).reset_index(drop=True)
    chart = None
    if len(flow_df) > 1:
        chart = {
            "labels": flow_df[PERIODO_COLUMN].astype(str).tolist(),
            "base_values": pd.to_numeric(flow_df["Entradas"], errors="coerce").fillna(0).tolist(),
            "result_values": pd.to_numeric(flow_df["Salidas"], errors="coerce").fillna(0).tolist(),
            "title": "Balance de flujo por tramo",
            "label_base": "Entradas",
            "label_result": "Salidas",
        }

    return {
        "table": _build_table_model(
            flow_df[["Fecha", "Tramo / jornada", "Entradas", "Salidas", "Margen de error"]],
            percent_columns=["Margen de error"],
            count_columns=["Entradas", "Salidas"],
        ),
        "chart": chart,
        "available": True,
    }


def _build_dwell_table(filtered_df: pd.DataFrame) -> dict:
    dwell_df = filtered_df[filtered_df[ZONE_TYPE_COLUMN] == "Zona de permanencia"].copy()
    if dwell_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    grouped = _group_zone_table(dwell_df, [DISPLAY_CAMERA_COLUMN, "Zona"])
    grouped = grouped[
        [
            DISPLAY_CAMERA_COLUMN,
            "Zona",
            "Total eventos auditados",
            "Eventos registrados",
            "Eventos no registrados",
            "Eventos correctos",
            MISREGISTERED_COLUMN,
            "Precision sobre registrados",
            "Precision sobre total",
            SUBREGISTER_PCT_COLUMN,
            "Lectura breve",
        ]
    ]
    return _build_table_model(
        grouped,
        percent_columns=["Precision sobre registrados", "Precision sobre total", SUBREGISTER_PCT_COLUMN],
        count_columns=["Total eventos auditados", "Eventos registrados", "Eventos no registrados", "Eventos correctos", MISREGISTERED_COLUMN],
    )


def _build_camera_summary(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    rows = []
    for camera, camera_df in filtered_df.groupby(DISPLAY_CAMERA_COLUMN, dropna=False):
        total_events = _safe_sum(camera_df["Total Eventos"])
        registered = _safe_sum(camera_df["Eventos Registrados por el Sistema"])
        not_registered = _safe_sum(camera_df["Eventos NO Registrados (Manuales)"])
        correct = _safe_sum(camera_df["Eventos Correctos del Sistema"])
        rows.append(
            {
                DISPLAY_CAMERA_COLUMN: camera,
                "Total auditado": total_events,
                "Registrados": registered,
                "No registrados": not_registered,
                "Correctos": correct,
                MISREGISTERED_COLUMN: max(registered - correct, 0),
                "Precision sobre registrados": _safe_pct(correct, registered),
                "Precision sobre total": _safe_pct(correct, total_events),
                SUBREGISTER_PCT_COLUMN: _safe_pct(not_registered, total_events),
                "Zonas incluidas": ", ".join(sorted(camera_df["Zona"].astype(str).unique().tolist())),
            }
        )

    camera_df = pd.DataFrame(rows).sort_values(by=DISPLAY_CAMERA_COLUMN).reset_index(drop=True)
    return _build_table_model(
        camera_df,
        percent_columns=["Precision sobre registrados", "Precision sobre total", SUBREGISTER_PCT_COLUMN],
        count_columns=["Total auditado", "Registrados", "No registrados", "Correctos", MISREGISTERED_COLUMN],
    )


def _build_identity_table(filtered_df: pd.DataFrame) -> dict:
    identity_df = filtered_df[
        filtered_df[ZONE_TYPE_COLUMN].isin(ATTRIBUTE_ZONE_TYPES) & filtered_df[IDENTITY_CONSIDERED_COLUMN].notna()
    ].copy()
    if identity_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    rows = []
    for keys, group_df in identity_df.groupby([DISPLAY_CAMERA_COLUMN, "Zona"], dropna=False):
        camera, zone = keys
        considered = _safe_sum(group_df[IDENTITY_CONSIDERED_COLUMN])
        coverage = _safe_sum(group_df["Cobertura Identity"])
        unknown = _safe_sum(group_df["Identity Unknown"])
        rows.append(
            {
                DISPLAY_CAMERA_COLUMN: camera,
                "Zona": zone,
                IDENTITY_CONSIDERED_COLUMN: considered,
                "Cobertura Identity": coverage,
                "% Cobertura Identity": _safe_pct(coverage, considered),
                "Identity Unknown": unknown,
                "% Identity Unknown": _safe_pct(unknown, considered),
            }
        )

    table_df = pd.DataFrame(rows).sort_values(by=[DISPLAY_CAMERA_COLUMN, "Zona"]).reset_index(drop=True)
    return _build_table_model(
        table_df,
        percent_columns=["% Cobertura Identity", "% Identity Unknown"],
        count_columns=[IDENTITY_CONSIDERED_COLUMN, "Cobertura Identity", "Identity Unknown"],
    )


def _build_attribute_table(filtered_df: pd.DataFrame) -> dict:
    attribute_df = filtered_df[
        filtered_df[ZONE_TYPE_COLUMN].isin(ATTRIBUTE_ZONE_TYPES) & filtered_df[ATTRIBUTE_CONSIDERED_COLUMN].notna()
    ].copy()
    if attribute_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    rows = []
    for keys, group_df in attribute_df.groupby([DISPLAY_CAMERA_COLUMN, "Zona"], dropna=False):
        camera, zone = keys
        considered = _safe_sum(group_df[ATTRIBUTE_CONSIDERED_COLUMN])
        gender_coverage = _safe_sum(group_df[GENDER_COVERAGE])
        gender_precision = _safe_sum(group_df[GENDER_PRECISION])
        age_coverage = _safe_sum(group_df["Cobertura Edad"])
        age_precision = _safe_sum(group_df[AGE_PRECISION])
        rows.append(
            {
                DISPLAY_CAMERA_COLUMN: camera,
                "Zona": zone,
                ATTRIBUTE_CONSIDERED_COLUMN: considered,
                "Cobertura Genero": gender_coverage,
                "% Cobertura Genero": _safe_pct(gender_coverage, considered),
                "Precision Genero": gender_precision,
                "% Precision Genero": _safe_pct(gender_precision, gender_coverage),
                "Cobertura Edad": age_coverage,
                "% Cobertura Edad": _safe_pct(age_coverage, considered),
                "Precision Edad": age_precision,
                "% Precision Edad": _safe_pct(age_precision, age_coverage),
            }
        )

    table_df = pd.DataFrame(rows).sort_values(by=[DISPLAY_CAMERA_COLUMN, "Zona"]).reset_index(drop=True)
    return _build_table_model(
        table_df,
        percent_columns=["% Cobertura Genero", "% Precision Genero", "% Cobertura Edad", "% Precision Edad"],
        count_columns=[ATTRIBUTE_CONSIDERED_COLUMN, "Cobertura Genero", "Precision Genero", "Cobertura Edad", "Precision Edad"],
    )


def _build_multi_period_camera_table(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    rows = []
    for keys, group_df in filtered_df.groupby(["Fecha", TRAMO_COLUMN, DISPLAY_CAMERA_COLUMN], dropna=False):
        fecha, tramo, camera = keys
        total_events = _safe_sum(group_df["Total Eventos"])
        registered = _safe_sum(group_df["Eventos Registrados por el Sistema"])
        not_registered = _safe_sum(group_df["Eventos NO Registrados (Manuales)"])
        correct = _safe_sum(group_df["Eventos Correctos del Sistema"])
        rows.append(
            {
                "Fecha": fecha,
                "Tramo / jornada": tramo,
                DISPLAY_CAMERA_COLUMN: camera,
                "Total eventos auditados": total_events,
                "Eventos correctos": correct,
                "Precision sobre total": _safe_pct(correct, total_events),
                "Precision sobre registrados": _safe_pct(correct, registered),
                "Subregistro": _safe_pct(not_registered, total_events),
                "Zonas incluidas": ", ".join(sorted(group_df["Zona"].astype(str).unique().tolist())),
            }
        )

    table_df = pd.DataFrame(rows).sort_values(by=["Fecha", "Tramo / jornada", DISPLAY_CAMERA_COLUMN]).reset_index(drop=True)
    return _build_table_model(
        table_df,
        percent_columns=["Precision sobre total", "Precision sobre registrados", "Subregistro"],
        count_columns=["Total eventos auditados", "Eventos correctos"],
    )


def _build_multi_period_zone_table(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty:
        return _build_plain_table_model(pd.DataFrame())

    rows = []
    group_columns = ["Fecha", TRAMO_COLUMN, DISPLAY_CAMERA_COLUMN, "Zona", ZONE_TYPE_COLUMN]
    for keys, group_df in filtered_df.groupby(group_columns, dropna=False):
        fecha, tramo, camera, zone, zone_type = keys
        total_events = _safe_sum(group_df["Total Eventos"])
        registered = _safe_sum(group_df["Eventos Registrados por el Sistema"])
        not_registered = _safe_sum(group_df["Eventos NO Registrados (Manuales)"])
        correct = _safe_sum(group_df["Eventos Correctos del Sistema"])
        rows.append(
            {
                "Fecha": fecha,
                "Tramo / jornada": tramo,
                DISPLAY_CAMERA_COLUMN: camera,
                "Zona": zone,
                ZONE_TYPE_COLUMN: zone_type,
                "Total eventos auditados": total_events,
                "Eventos correctos": correct,
                "Precision sobre total": _safe_pct(correct, total_events),
                "Precision sobre registrados": _safe_pct(correct, registered),
                "Subregistro": _safe_pct(not_registered, total_events),
            }
        )

    table_df = pd.DataFrame(rows).sort_values(
        by=["Fecha", "Tramo / jornada", DISPLAY_CAMERA_COLUMN, "Zona"]
    ).reset_index(drop=True)
    return _build_table_model(
        table_df,
        percent_columns=["Precision sobre total", "Precision sobre registrados", "Subregistro"],
        count_columns=["Total eventos auditados", "Eventos correctos"],
    )


def _build_multi_period(filtered_df: pd.DataFrame) -> dict:
    if filtered_df.empty:
        empty_table = _build_plain_table_model(pd.DataFrame())
        return {
            "available": False,
            "table": empty_table,
            "chart": None,
            "camera_table": empty_table,
            "zone_table": empty_table,
        }

    rows = []
    for keys, period_df in filtered_df.groupby(["Fecha", TRAMO_COLUMN], dropna=False):
        fecha, tramo = keys
        period_label = _build_periodo_label(str(fecha or ""), str(tramo or ""))
        total_events = _safe_sum(period_df["Total Eventos"])
        registered = _safe_sum(period_df["Eventos Registrados por el Sistema"])
        not_registered = _safe_sum(period_df["Eventos NO Registrados (Manuales)"])
        correct = _safe_sum(period_df["Eventos Correctos del Sistema"])
        identity_scope_df = period_df[
            period_df[ZONE_TYPE_COLUMN].isin(ATTRIBUTE_ZONE_TYPES) & period_df[IDENTITY_CONSIDERED_COLUMN].notna()
        ]
        identity_unknown = (
            _safe_sum(identity_scope_df["Identity Unknown"]) if not identity_scope_df.empty else None
        )
        rows.append(
            {
                "Fecha": fecha,
                "Tramo / jornada": tramo,
                PERIODO_COLUMN: period_label,
                "Total eventos auditados": total_events,
                "Eventos correctos": correct,
                "Precision sobre total": _safe_pct(correct, total_events),
                "Precision sobre registrados": _safe_pct(correct, registered),
                "Subregistro": _safe_pct(not_registered, total_events),
                "Identity Unknown": identity_unknown,
            }
        )

    period_df = pd.DataFrame(rows).sort_values(by=["Fecha", "Tramo / jornada"]).reset_index(drop=True)
    chart = None
    if len(period_df) > 1:
        chart = {
            "labels": period_df[PERIODO_COLUMN].astype(str).tolist(),
            "base_values": pd.to_numeric(period_df["Total eventos auditados"], errors="coerce").fillna(0).tolist(),
            "result_values": pd.to_numeric(period_df["Eventos correctos"], errors="coerce").fillna(0).tolist(),
            "title": "Precision consolidada por tramo",
            "label_base": "Auditados",
            "label_result": "Correctos",
        }

    available = len(period_df) > 1
    return {
        "available": available,
        "table": _build_table_model(
            period_df[
                [
                    "Fecha",
                    "Tramo / jornada",
                    "Total eventos auditados",
                    "Eventos correctos",
                    "Precision sobre total",
                    "Precision sobre registrados",
                    "Subregistro",
                    "Identity Unknown",
                ]
            ],
            percent_columns=["Precision sobre total", "Precision sobre registrados", "Subregistro"],
            count_columns=["Total eventos auditados", "Eventos correctos", "Identity Unknown"],
        ),
        "chart": chart,
        "camera_table": _build_multi_period_camera_table(filtered_df) if available else _build_plain_table_model(pd.DataFrame()),
        "zone_table": _build_multi_period_zone_table(filtered_df) if available else _build_plain_table_model(pd.DataFrame()),
    }


def _build_validation_messages(scope: dict) -> list[str]:
    messages = []
    tolerance = 1e-6

    if abs((scope["registered"] + scope["not_registered"]) - scope["total_events"]) > tolerance:
        messages.append("Registrados + no registrados no coincide con el total auditado.")
    if abs((scope["correct"] + scope["misregistered"]) - scope["registered"]) > tolerance:
        messages.append("Correctos + mal registrados no coincide con registrados.")
    if abs((scope["correct"] + scope["misregistered"] + scope["not_registered"]) - scope["total_events"]) > tolerance:
        messages.append("Correctos + mal registrados + no registrados no coincide con el total.")
    if scope["identity_considered"] > 0 and abs((scope["identity_coverage"] + scope["identity_unknown"]) - scope["identity_considered"]) > tolerance:
        messages.append("Cobertura Identity + Identity Unknown no coincide con los registrados considerados para Identity.")
    if scope["gender_precision"] - scope["gender_coverage"] > tolerance:
        messages.append("La precision de Genero supera su cobertura.")
    if scope["age_precision"] - scope["age_coverage"] > tolerance:
        messages.append("La precision de Edad supera su cobertura.")
    return messages


def build_report_view_data(results: dict, filters: dict | None = None) -> dict:
    detail_df = _prepare_detail_dataframe(results)
    filter_options = _build_filter_options(detail_df, results)
    active_filters = filters or {"fecha": "Todas", "tramo": "Todos", "camara": "Todas", "zona": "Todas", "tipo_zona": "Todos"}
    filtered_df = _apply_filters(detail_df, active_filters)
    scope = _aggregate_scope(filtered_df) if not filtered_df.empty else _aggregate_scope(pd.DataFrame(columns=detail_df.columns))

    return {
        "context": {
            "empresa": results.get("empresa", ""),
            "sucursal": results.get("sucursal", ""),
            "modo": results.get("view_mode", ""),
            "fecha_selected": results.get("fecha_selected", ""),
            "sensor": results.get("active_sensor", "Todos"),
        },
        "filter_options": filter_options,
        "active_filters": active_filters,
        "filtered_row_count": len(filtered_df),
        "has_data": not filtered_df.empty,
        "kpis_table": _build_kpi_table(scope),
        "lines_table": _build_lines_table(filtered_df),
        "flow_balance": _build_flow_balance(filtered_df),
        "dwell_table": _build_dwell_table(filtered_df),
        "camera_table": _build_camera_summary(filtered_df),
        "identity_table": _build_identity_table(filtered_df),
        "attributes_table": _build_attribute_table(filtered_df),
        "multi_period": _build_multi_period(filtered_df),
        "validation_messages": _build_validation_messages(scope),
    }
