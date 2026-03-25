"""Core business logic for audit KPI calculation."""

from __future__ import annotations

from typing import Iterable
import unicodedata

import pandas as pd

from audit_app.domain.kpi_schema import (
    AGE_PRECISION,
    AGE_PRECISION_PCT,
    BAD_EVENTS,
    BAD_EVENTS_PCT,
    CAMERA_COLUMN,
    EVENT_PRECISION_PCT,
    GENDER_COVERAGE,
    GENDER_COVERAGE_PCT,
    GENDER_PRECISION,
    GENDER_PRECISION_PCT,
    KPI_COLUMNS,
)

LINE_SENSOR = "linea_conteo"
DWELL_SENSOR = "zona_permanencia"
ENTRY_KEYWORDS = ("entrada",)
EXTERIOR_KEYWORDS = ("exterior",)
GPU_NO_REGISTER_KEYWORDS = ("gpu no registra",)
COUNTER_POSITIVE_KEYWORDS = (
    "conteo sube",
    "conteo cambia",
    "solo registra conteo",
    "contador cambia",
    "cambio de contador",
    "contador sube",
    "sube contador",
)
COUNTER_NEGATIVE_KEYWORDS = (
    "evento no registrado",
    "conteo no cambia",
    "conteo no sube",
    "no registra conteo",
    "contador no cambia",
    "sin cambio de contador",
    "contador no sube",
    "no sube contador",
)


def _empty_series(length: int, default_value=None, index=None) -> pd.Series:
    return pd.Series([default_value] * length, index=index)


def get_column(df: pd.DataFrame, candidate_names: Iterable[str], default_value=None) -> pd.Series:
    for name in candidate_names:
        if name in df.columns:
            return df[name]
    return _empty_series(len(df), default_value, index=df.index)


def calc_pct(part: float, total: float) -> float:
    return (part / total) if total > 0 else 0.0


def calc_optional_pct(part: float, total: float, applies: bool) -> float | None:
    if not applies:
        return None
    return calc_pct(part, total)


def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def normalize_text_series(series: pd.Series) -> pd.Series:
    return series.apply(normalize_text)


def contains_any_keyword(series: pd.Series, keywords: tuple[str, ...]) -> pd.Series:
    normalized = normalize_text_series(series)
    mask = pd.Series(False, index=series.index)
    for keyword in keywords:
        mask = mask | normalized.str.contains(keyword, regex=False)
    return mask


def build_combined_text_series(*series_list: pd.Series) -> pd.Series:
    combined = pd.Series("", index=series_list[0].index, dtype="object")
    for series in series_list:
        combined = combined.str.cat(series.fillna("").astype(str), sep=" | ", na_rep="")
    return combined.str.strip()


def calculate_group_metrics(group: pd.DataFrame) -> pd.Series:
    identity = get_column(group, ["Identity_ID", "ID_Identidad"])
    event_audit = get_column(group, ["Event_Audit", "Auditoria_Evento"], "mal")
    gender_audit = get_column(group, ["Gender_Audit", "Auditoria_Genero"], "mal")
    age_audit = get_column(group, ["Age_Audit", "Auditoria_Edad"], "mal")
    gender = get_column(group, ["Gender", "Genero", "Sexo"], "unknown")
    age = get_column(group, ["Age", "Edad"], 0)
    zone = get_column(group, ["Zona_name", "Zona", "Nombre_zona"], "")
    sensor_type = get_column(group, ["Tipo_sensor"], "")
    observation_a = get_column(group, ["Observation_A", "Observacion_A", "Observacion_A"], "")
    observation_b = get_column(group, ["Observation_B", "Observacion_B", "Observacion_B"], "")
    counter_signal = get_column(
        group,
        [
            "Counter_Change",
            "Cambio_Contador",
            "Cambio contador",
            "Cambio_contador",
            "Estado_Contador",
            "Estado contador",
            "Counter_Status",
        ],
        "",
    )

    event_audit_normalized = normalize_text_series(event_audit)
    gender_audit_normalized = normalize_text_series(gender_audit)
    age_audit_normalized = normalize_text_series(age_audit)
    sensor_type_normalized = normalize_text_series(sensor_type)
    observation_a_normalized = normalize_text_series(observation_a)
    counter_signal_text = build_combined_text_series(observation_b, counter_signal)

    line_count_mask = sensor_type_normalized.eq(LINE_SENSOR)
    dwell_mask = sensor_type_normalized.eq(DWELL_SENSOR)
    entry_line_mask = line_count_mask & contains_any_keyword(zone, ENTRY_KEYWORDS)
    exterior_line_mask = line_count_mask & contains_any_keyword(zone, EXTERIOR_KEYWORDS)
    attribute_coverage_mask = dwell_mask | entry_line_mask

    gpu_no_register_mask = observation_a_normalized.str.contains("gpu no registra", regex=False)
    exterior_counter_positive_mask = exterior_line_mask & contains_any_keyword(counter_signal_text, COUNTER_POSITIVE_KEYWORDS)
    exterior_counter_negative_mask = exterior_line_mask & contains_any_keyword(counter_signal_text, COUNTER_NEGATIVE_KEYWORDS)
    exterior_not_registered_mask = exterior_counter_negative_mask & gpu_no_register_mask
    legacy_not_registered_mask = line_count_mask & contains_any_keyword(counter_signal_text, ("evento no registrado",))
    explicit_not_registered_mask = exterior_not_registered_mask | legacy_not_registered_mask
    registered_mask = ~explicit_not_registered_mask

    total_events = len(group)
    not_registered = int(explicit_not_registered_mask.sum())
    registered = int(registered_mask.sum())

    line_has_counter_signal = exterior_counter_positive_mask | exterior_counter_negative_mask
    exterior_line_correct_mask = exterior_counter_positive_mask
    non_exterior_line_count_mask = line_count_mask & ~exterior_line_mask
    fallback_line_correct_mask = (
        non_exterior_line_count_mask
        & ~line_has_counter_signal
        & registered_mask
        & event_audit_normalized.eq("bien")
    )
    regular_correct_mask = (
        ~line_count_mask
        & registered_mask
        & event_audit_normalized.eq("bien")
    )
    non_exterior_counter_correct_mask = non_exterior_line_count_mask & contains_any_keyword(counter_signal_text, COUNTER_POSITIVE_KEYWORDS)
    correct_event_mask = (
        exterior_line_correct_mask
        | non_exterior_counter_correct_mask
        | fallback_line_correct_mask
        | regular_correct_mask
    )
    correct_events = int(correct_event_mask.sum())
    bad_events = total_events - correct_events

    attribute_applies = bool(attribute_coverage_mask.any() and not exterior_line_mask.all())
    applicable_registered_mask = registered_mask & attribute_coverage_mask
    applicable_registered = int(applicable_registered_mask.sum())

    correct_gender = int((gender_audit_normalized.eq("bien") & applicable_registered_mask).sum()) if attribute_applies else None
    correct_age = int((age_audit_normalized.eq("bien") & applicable_registered_mask).sum()) if attribute_applies else None

    registered_gender = gender[applicable_registered_mask]
    registered_identity = identity[applicable_registered_mask]
    registered_age = age[applicable_registered_mask]

    known_gender = registered_gender.notna() & (normalize_text_series(registered_gender) != "unknown")
    gender_coverage = int(known_gender.sum()) if attribute_applies else None

    numeric_age = pd.to_numeric(registered_age, errors="coerce")
    known_age = numeric_age.notna() & (numeric_age > 0)
    age_coverage = int(known_age.sum()) if attribute_applies else None

    identity_unknown = int(normalize_text_series(registered_identity).eq("unknown").sum()) if attribute_applies else None
    identity_coverage = (applicable_registered - identity_unknown) if attribute_applies else None

    return pd.Series(
        {
            "Total Eventos": total_events,
            "Eventos Registrados por el Sistema": registered,
            "% Eventos Registrados por el Sistema": calc_pct(registered, total_events),
            "Eventos NO Registrados (Manuales)": not_registered,
            "% Eventos NO Registrados (Manuales)": calc_pct(not_registered, total_events),
            "Eventos Correctos del Sistema": correct_events,
            EVENT_PRECISION_PCT: calc_pct(correct_events, total_events),
            "% Eventos Correctos sobre Registrados": calc_pct(correct_events, registered),
            BAD_EVENTS: bad_events,
            BAD_EVENTS_PCT: calc_pct(bad_events, total_events),
            "Cobertura Identity": identity_coverage,
            "% Cobertura Identity": calc_optional_pct(identity_coverage or 0, applicable_registered, attribute_applies),
            "Identity Unknown": identity_unknown,
            "% Identity Unknown": calc_optional_pct(identity_unknown or 0, applicable_registered, attribute_applies),
            GENDER_COVERAGE: gender_coverage,
            GENDER_COVERAGE_PCT: calc_optional_pct(gender_coverage or 0, applicable_registered, attribute_applies),
            GENDER_PRECISION: correct_gender,
            GENDER_PRECISION_PCT: calc_optional_pct(correct_gender or 0, gender_coverage or 0, attribute_applies),
            "Cobertura Edad": age_coverage,
            "% Cobertura Edad": calc_optional_pct(age_coverage or 0, applicable_registered, attribute_applies),
            AGE_PRECISION: correct_age,
            AGE_PRECISION_PCT: calc_optional_pct(correct_age or 0, age_coverage or 0, attribute_applies),
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
    report_rows = []
    for group_key, group_df in df.groupby(group_columns, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        row = calculate_group_metrics(group_df).to_dict()
        row.update(dict(zip(group_columns, group_key)))
        report_rows.append(row)

    report = pd.DataFrame(report_rows)

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
