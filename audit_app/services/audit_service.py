"""Application service that orchestrates audit processing."""

from __future__ import annotations

import os
import re
import unicodedata

import pandas as pd

from audit_app.domain.metrics import build_audit_report
from audit_app.infrastructure.charts import build_chart_payloads
from audit_app.infrastructure.excel_exporter import export_audit_report

VIEW_MODE_INDIVIDUAL = "Auditoria individual"
VIEW_MODE_DATE = "Consolidado por fecha"
VIEW_MODE_SUCURSAL = "Consolidado sucursal"
SENSOR_TYPE_COLUMN = "Tipo_sensor"
SENSOR_LINE = "Linea_conteo"
SENSOR_DWELL = "Zona_permanencia"
SENSOR_UNDEFINED = "No definido"


def build_sucursal_dir(base_dir: str, empresa: str, sucursal: str | None) -> str:
    if sucursal:
        return os.path.join(base_dir, empresa, sucursal)
    return os.path.join(base_dir, empresa)


def build_work_dir(base_dir: str, empresa: str, fecha: str, sucursal: str | None) -> str:
    if sucursal:
        return os.path.join(base_dir, empresa, sucursal, fecha)
    return os.path.join(base_dir, empresa, fecha)


def normalize_time_fragment(fragment: str) -> str:
    return fragment.replace(".", ":")


def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def infer_sensor_type_from_zone(zone_name) -> str:
    normalized_zone = normalize_text(zone_name)
    if not normalized_zone:
        return SENSOR_UNDEFINED

    line_patterns = [
        "entrada",
        "exterior",
        "trafico",
        "linea",
        "acceso",
        "salida",
    ]
    if any(pattern in normalized_zone for pattern in line_patterns):
        return SENSOR_LINE
    return SENSOR_DWELL


def populate_sensor_type_column(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized_df = dataframe.copy()
    zone_series = None
    for candidate in ["Zona_name", "Zona", "Nombre_zona"]:
        if candidate in normalized_df.columns:
            zone_series = normalized_df[candidate]
            break

    if SENSOR_TYPE_COLUMN not in normalized_df.columns:
        if zone_series is not None:
            normalized_df[SENSOR_TYPE_COLUMN] = zone_series.apply(infer_sensor_type_from_zone)
        else:
            normalized_df[SENSOR_TYPE_COLUMN] = SENSOR_UNDEFINED
        return normalized_df

    normalized_df[SENSOR_TYPE_COLUMN] = (
        normalized_df[SENSOR_TYPE_COLUMN]
        .fillna(SENSOR_UNDEFINED)
        .astype(str)
        .str.strip()
        .replace("", SENSOR_UNDEFINED)
    )

    if zone_series is not None:
        missing_mask = normalized_df[SENSOR_TYPE_COLUMN].eq(SENSOR_UNDEFINED)
        if missing_mask.any():
            normalized_df.loc[missing_mask, SENSOR_TYPE_COLUMN] = zone_series[missing_mask].apply(
                infer_sensor_type_from_zone
            )

    return normalized_df


def parse_time_window_from_filename(filename: str) -> tuple[str, str]:
    match = re.search(r"_(\d{2}[.:]\d{2})-(\d{2}[.:]\d{2})\.csv$", filename, re.IGNORECASE)
    if not match:
        return "", ""
    return normalize_time_fragment(match.group(1)), normalize_time_fragment(match.group(2))


def build_audit_label(filename: str) -> str:
    hour_start, hour_end = parse_time_window_from_filename(filename)
    if hour_start and hour_end:
        return f"{hour_start} - {hour_end}"
    return os.path.splitext(filename)[0]


def list_audit_dates(base_dir: str, empresa: str, sucursal: str | None) -> list[str]:
    sucursal_dir = build_sucursal_dir(base_dir, empresa, sucursal)
    if not os.path.exists(sucursal_dir):
        return []

    return sorted(
        [
            directory
            for directory in os.listdir(sucursal_dir)
            if os.path.isdir(os.path.join(sucursal_dir, directory))
        ]
    )


def list_audit_files(base_dir: str, empresa: str, sucursal: str | None, fecha: str) -> list[dict]:
    work_dir = build_work_dir(base_dir, empresa, fecha, sucursal)
    if not os.path.exists(work_dir):
        return []

    csv_files = sorted(
        [
            filename
            for filename in os.listdir(work_dir)
            if filename.lower().endswith(".csv")
        ]
    )

    audit_files = []
    for filename in csv_files:
        hour_start, hour_end = parse_time_window_from_filename(filename)
        audit_files.append(
            {
                "filename": filename,
                "path": os.path.join(work_dir, filename),
                "label": build_audit_label(filename),
                "fecha": fecha.replace("_", "-"),
                "hora_inicio": hour_start,
                "hora_termino": hour_end,
            }
        )

    return audit_files


def load_audit_csv(input_file_path: str) -> tuple[pd.DataFrame | None, str | None]:
    if not os.path.exists(input_file_path):
        return None, f"ERROR: No se encontro el archivo en la ruta:\n   {input_file_path}"

    try:
        dataframe = pd.read_csv(input_file_path)
        dataframe.columns = [str(column).strip() for column in dataframe.columns]
        unnamed_columns = [
            column
            for column in dataframe.columns
            if column == "" or column.lower().startswith("unnamed:")
        ]
        if unnamed_columns:
            dataframe = dataframe.drop(columns=unnamed_columns)

        dataframe = populate_sensor_type_column(dataframe)

        return dataframe, None
    except Exception as exc:
        return None, f"ERROR al leer CSV: {exc}"


def annotate_audit_frame(df: pd.DataFrame, fecha: str, hora_inicio: str, hora_termino: str) -> pd.DataFrame:
    annotated_df = df.copy()
    annotated_df["Fecha"] = fecha
    annotated_df["Hora_inicio"] = hora_inicio
    annotated_df["Hora_termino"] = hora_termino
    return annotated_df


def collect_sources_for_mode(
    base_dir: str,
    empresa: str,
    sucursal: str | None,
    mode: str,
    fecha: str | None = None,
    audit_filename: str | None = None,
    input_filename: str = "input.csv",
) -> tuple[list[dict], str, str | None]:
    sucursal_dir = build_sucursal_dir(base_dir, empresa, sucursal)

    if mode == VIEW_MODE_SUCURSAL:
        sources = []
        for current_date in list_audit_dates(base_dir, empresa, sucursal):
            sources.extend(list_audit_files(base_dir, empresa, sucursal, current_date))
        if not sources:
            return [], sucursal_dir, "No se encontraron auditorias para la sucursal seleccionada."
        return sources, sucursal_dir, None

    if not fecha:
        return [], sucursal_dir, "Debe seleccionar una fecha para continuar."

    work_dir = build_work_dir(base_dir, empresa, fecha, sucursal)
    date_sources = list_audit_files(base_dir, empresa, sucursal, fecha)

    if not date_sources and input_filename:
        fallback_path = os.path.join(work_dir, input_filename)
        if os.path.exists(fallback_path):
            date_sources = [
                {
                    "filename": input_filename,
                    "path": fallback_path,
                    "label": build_audit_label(input_filename),
                    "fecha": fecha.replace("_", "-"),
                    "hora_inicio": "",
                    "hora_termino": "",
                }
            ]

    if not date_sources:
        return [], work_dir, "No se encontraron archivos CSV para la fecha seleccionada."

    if mode == VIEW_MODE_DATE:
        return date_sources, work_dir, None

    selected_source = None
    if audit_filename:
        selected_source = next(
            (source for source in date_sources if source["filename"] == audit_filename),
            None,
        )
    elif len(date_sources) == 1:
        selected_source = date_sources[0]

    if not selected_source:
        return [], work_dir, "Debe seleccionar una auditoria individual para continuar."

    return [selected_source], work_dir, None


def build_output_filename(
    empresa: str,
    sucursal: str | None,
    mode: str,
    work_dir: str,
    fecha: str | None,
    sources: list[dict],
) -> str:
    safe_sucursal = (sucursal or "").replace(" ", "_")

    if mode == VIEW_MODE_INDIVIDUAL and len(sources) == 1:
        audit_label = sources[0]["label"].replace(":", ".").replace(" ", "_")
        date_label = (fecha or "").replace(" ", "_")
        filename = f"Reporte_Auditoria_Maestro_{empresa}_{safe_sucursal}_{date_label}_{audit_label}.xlsx"
        return os.path.join(work_dir, filename)

    if mode == VIEW_MODE_DATE:
        date_label = (fecha or "").replace(" ", "_")
        filename = f"Reporte_Auditoria_Maestro_{empresa}_{safe_sucursal}_{date_label}.xlsx"
        return os.path.join(work_dir, filename)

    filename = f"Reporte_Auditoria_Maestro_{empresa}_{safe_sucursal}_Consolidado.xlsx"
    return os.path.join(work_dir, filename)


def build_view_label(mode: str, fecha: str | None, sources: list[dict]) -> str:
    if mode == VIEW_MODE_SUCURSAL:
        return "Consolidado sucursal"
    if mode == VIEW_MODE_DATE:
        return f"{fecha} | Consolidado por fecha"
    if len(sources) == 1:
        source = sources[0]
        if source["hora_inicio"] and source["hora_termino"]:
            return f"{source['fecha']} | {source['hora_inicio']} - {source['hora_termino']}"
        return source["fecha"]
    return fecha or ""


def process_audit_data(
    empresa,
    fecha=None,
    sucursal=None,
    input_filename="input.csv",
    mode: str = VIEW_MODE_INDIVIDUAL,
    audit_filename: str | None = None,
):
    base_dir = "Auditorias_Clientes"
    if not audit_filename and mode == VIEW_MODE_INDIVIDUAL and input_filename != "input.csv":
        audit_filename = input_filename
    sources, work_dir, error = collect_sources_for_mode(
        base_dir,
        empresa,
        sucursal,
        mode=mode,
        fecha=fecha,
        audit_filename=audit_filename,
        input_filename=input_filename,
    )
    if error:
        return None, error

    frames = []
    for source in sources:
        df, load_error = load_audit_csv(source["path"])
        if load_error:
            return None, load_error
        frames.append(
            annotate_audit_frame(
                df,
                source["fecha"],
                source["hora_inicio"],
                source["hora_termino"],
            )
        )

    consolidated_df = pd.concat(frames, ignore_index=True)
    reporte, df_grafico, df_total = build_audit_report(consolidated_df, fecha or "")
    chart_payloads = build_chart_payloads(df_grafico, df_total)
    output_xlsx = export_audit_report(
        empresa,
        fecha or "",
        work_dir,
        reporte,
        chart_payloads,
        df_grafico=df_grafico,
        df_total=df_total,
        output_filename=build_output_filename(empresa, sucursal, mode, work_dir, fecha, sources),
    )

    return {
        "reporte": reporte,
        "df_grafico": df_grafico,
        "df_total": df_total,
        "source_df": consolidated_df,
        "img_global": chart_payloads["img_global"],
        "img_totales": chart_payloads["img_totales"],
        "cam_images": chart_payloads["cam_images"],
        "cam_coverage_images": chart_payloads["cam_coverage_images"],
        "cam_summary_images": chart_payloads["cam_summary_images"],
        "zone_images": chart_payloads["zone_images"],
        "img_unknown_global": chart_payloads["img_unknown_global"],
        "img_unknown_global_bytes": chart_payloads["img_unknown_global_bytes"],
        "unknown_images": chart_payloads["unknown_images"],
        "output_xlsx": output_xlsx,
        "work_dir": work_dir,
        "view_mode": mode,
        "view_label": build_view_label(mode, fecha, sources),
        "source_count": len(sources),
        "selected_sources": sources,
    }, None
