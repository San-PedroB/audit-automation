"""Core business logic for audit KPI calculation."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from audit_app.domain.kpi_schema import (
    AGE_PRECISION,
    AGE_PRECISION_PCT,
    CAMERA_COLUMN,
    GENDER_COVERAGE,
    GENDER_COVERAGE_PCT,
    GENDER_PRECISION,
    GENDER_PRECISION_PCT,
    KPI_COLUMNS,
)


def _empty_series(length: int, default_value=None) -> pd.Series:
    return pd.Series([default_value] * length)


def get_column(df: pd.DataFrame, candidate_names: Iterable[str], default_value=None) -> pd.Series:
    for name in candidate_names:
        if name in df.columns:
            return df[name]
    return _empty_series(len(df), default_value)


def calc_pct(part: float, total: float) -> float:
    return (part / total) if total > 0 else 0.0


def calculate_group_metrics(group: pd.DataFrame) -> pd.Series:
    identity = get_column(group, ["Identity_ID", "ID_Identidad"])
    event_audit = get_column(group, ["Event_Audit", "Auditoria_Evento"], "mal")
    gender_audit = get_column(group, ["Gender_Audit", "Auditoria_Genero"], "mal")
    age_audit = get_column(group, ["Age_Audit", "Auditoria_Edad"], "mal")
    gender = get_column(group, ["Gender", "Genero", "Sexo"], "unknown")
    age = get_column(group, ["Age", "Edad"], 0)

    total_events = len(group)
    not_registered = identity.isna().sum() + (identity.astype(str).str.strip() == "").sum()
    registered = total_events - not_registered

    correct_events = event_audit.astype(str).str.strip().str.lower().eq("bien").sum()
    correct_gender = gender_audit.astype(str).str.strip().str.lower().eq("bien").sum()
    correct_age = age_audit.astype(str).str.strip().str.lower().eq("bien").sum()

    known_gender = gender.notna() & (gender.astype(str).str.lower() != "unknown")
    gender_coverage = known_gender.sum()

    numeric_age = pd.to_numeric(age, errors="coerce")
    known_age = numeric_age.notna() & (numeric_age > 0)
    age_coverage = known_age.sum()

    identity_unknown = (identity.astype(str).str.lower() == "unknown").sum()
    identity_coverage = registered - identity_unknown
    registered_wrong = registered - correct_events

    return pd.Series(
        {
            "Total Eventos": total_events,
            "Eventos Registrados por el Sistema": registered,
            "% Eventos Registrados por el Sistema": calc_pct(registered, total_events),
            "Eventos NO Registrados (Manuales)": not_registered,
            "% Eventos NO Registrados (Manuales)": calc_pct(not_registered, total_events),
            "Eventos Correctos del Sistema": correct_events,
            "% Eventos Correctos sobre Registrados": calc_pct(correct_events, registered),
            "% Eventos Correctos sobre Total": calc_pct(correct_events, total_events),
            "Eventos Reg. Mal (Sist.)": registered_wrong,
            "% Eventos Reg. Mal sobre Registrados": calc_pct(registered_wrong, registered),
            "Cobertura Identity": identity_coverage,
            "% Cobertura Identity": calc_pct(identity_coverage, registered),
            "Identity Unknown": identity_unknown,
            "% Identity Unknown": calc_pct(identity_unknown, registered),
            GENDER_COVERAGE: gender_coverage,
            GENDER_COVERAGE_PCT: calc_pct(gender_coverage, registered),
            GENDER_PRECISION: correct_gender,
            GENDER_PRECISION_PCT: calc_pct(correct_gender, gender_coverage),
            "Cobertura Edad": age_coverage,
            "% Cobertura Edad": calc_pct(age_coverage, registered),
            AGE_PRECISION: correct_age,
            AGE_PRECISION_PCT: calc_pct(correct_age, age_coverage),
        }
    )


def ensure_audit_metadata(df: pd.DataFrame, default_fecha: str) -> pd.DataFrame:
    normalized_date = default_fecha.replace("_", "-") if default_fecha else ""
    metadata_df = df.copy()

    if "Fecha" not in metadata_df.columns:
        metadata_df["Fecha"] = normalized_date
    else:
        metadata_df["Fecha"] = metadata_df["Fecha"].fillna("").replace("", normalized_date)

    if "Hora_inicio" not in metadata_df.columns:
        metadata_df["Hora_inicio"] = ""
    else:
        metadata_df["Hora_inicio"] = metadata_df["Hora_inicio"].fillna("")

    if "Hora_termino" not in metadata_df.columns:
        metadata_df["Hora_termino"] = ""
    else:
        metadata_df["Hora_termino"] = metadata_df["Hora_termino"].fillna("")

    if "Tipo_sensor" not in metadata_df.columns:
        metadata_df["Tipo_sensor"] = ""
    else:
        metadata_df["Tipo_sensor"] = metadata_df["Tipo_sensor"].fillna("").astype(str).str.strip()

    return metadata_df


def build_grouped_report(df: pd.DataFrame, group_columns: list[str], has_camera: bool) -> pd.DataFrame:
    report = (
        df.groupby(group_columns)
        .apply(calculate_group_metrics, include_groups=False)
        .reset_index()
    )

    if has_camera:
        report.rename(columns={"Zona_name": "Zona", "Camara": CAMERA_COLUMN}, inplace=True)
    else:
        report.rename(columns={"Zona_name": "Zona"}, inplace=True)
        report[CAMERA_COLUMN] = ""

    if "Fecha" not in report.columns:
        report["Fecha"] = ""
    if "Hora_inicio" not in report.columns:
        report["Hora_inicio"] = ""
    if "Hora_termino" not in report.columns:
        report["Hora_termino"] = ""

    ordered_columns = [column for column in KPI_COLUMNS if column in report.columns]
    report = report[ordered_columns]
    return report


def build_audit_report(df: pd.DataFrame, default_fecha: str = "") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_zones = df[df["Zona_name"].notna() & (df["Zona_name"] != "")].copy()
    df_zones = ensure_audit_metadata(df_zones, default_fecha)

    has_camera = "Camara" in df_zones.columns
    detail_group_columns = ["Fecha", "Hora_inicio", "Hora_termino", "Tipo_sensor"]
    if has_camera:
        detail_group_columns.append("Camara")
    detail_group_columns.append("Zona_name")

    report = build_grouped_report(df_zones, detail_group_columns, has_camera)
    report.sort_values(
        by=["Fecha", "Hora_inicio", "Hora_termino", "Tipo_sensor", CAMERA_COLUMN, "Zona"],
        inplace=True,
        ignore_index=True,
    )

    chart_group_columns = ["Zona_name"]
    if has_camera:
        chart_group_columns.insert(0, "Camara")
    chart_df = build_grouped_report(df_zones, chart_group_columns, has_camera)
    chart_df.sort_values(by=[CAMERA_COLUMN, "Zona"], inplace=True, ignore_index=True)

    totals = calculate_group_metrics(df_zones)
    totals["Zona"] = "TOTAL"
    totals[CAMERA_COLUMN] = ""
    totals["Fecha"] = ""
    totals["Hora_inicio"] = ""
    totals["Hora_termino"] = ""
    totals["Tipo_sensor"] = ""

    totals_df = pd.DataFrame(totals).T
    ordered_columns = [column for column in KPI_COLUMNS if column in totals_df.columns]
    totals_df = totals_df[ordered_columns]

    report = pd.concat([report, totals_df], ignore_index=True)
    return report, chart_df, totals_df
