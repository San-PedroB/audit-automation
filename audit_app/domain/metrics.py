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


def build_audit_report(df: pd.DataFrame, fecha: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_zones = df[df["Zona_name"].notna() & (df["Zona_name"] != "")].copy()
    has_camera = "Camara" in df_zones.columns
    group_columns = ["Camara", "Zona_name"] if has_camera else ["Zona_name"]

    report = (
        df_zones.groupby(group_columns)
        .apply(calculate_group_metrics, include_groups=False)
        .reset_index()
    )

    if has_camera:
        report.rename(columns={"Zona_name": "Zona", "Camara": CAMERA_COLUMN}, inplace=True)
    else:
        report.rename(columns={"Zona_name": "Zona"}, inplace=True)
        report[CAMERA_COLUMN] = ""

    normalized_date = fecha.replace("_", "-")
    report["Fecha"] = normalized_date
    report["Hora_inicio"] = ""
    report["Hora_termino"] = ""

    totals = calculate_group_metrics(df_zones)
    totals["Zona"] = "TOTAL"
    totals[CAMERA_COLUMN] = ""
    totals["Fecha"] = normalized_date
    totals["Hora_inicio"] = ""
    totals["Hora_termino"] = ""

    report = pd.concat([report, pd.DataFrame(totals).T], ignore_index=True)
    ordered_columns = [column for column in KPI_COLUMNS if column in report.columns]
    report = report[ordered_columns]

    chart_df = report[report["Zona"] != "TOTAL"].copy()
    total_df = report[report["Zona"] == "TOTAL"].copy()
    return report, chart_df, total_df
