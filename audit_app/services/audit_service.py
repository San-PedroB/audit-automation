"""Application service that orchestrates audit processing."""

from __future__ import annotations

import os

import pandas as pd

from audit_app.domain.metrics import build_audit_report
from audit_app.infrastructure.charts import build_chart_payloads
from audit_app.infrastructure.excel_exporter import export_audit_report


def build_work_dir(base_dir: str, empresa: str, fecha: str, sucursal: str | None) -> str:
    if sucursal:
        return os.path.join(base_dir, empresa, sucursal, fecha)
    return os.path.join(base_dir, empresa, fecha)


def load_audit_csv(input_file_path: str) -> tuple[pd.DataFrame | None, str | None]:
    if not os.path.exists(input_file_path):
        return None, f"ERROR: No se encontro el archivo en la ruta:\n   {input_file_path}"

    try:
        return pd.read_csv(input_file_path), None
    except Exception as exc:
        return None, f"ERROR al leer CSV: {exc}"


def process_audit_data(empresa, fecha, sucursal=None, input_filename="input.csv"):
    base_dir = "Auditorias_Clientes"
    work_dir = build_work_dir(base_dir, empresa, fecha, sucursal)
    input_file_path = os.path.join(work_dir, input_filename)

    df, error = load_audit_csv(input_file_path)
    if error:
        return None, error

    reporte, df_grafico, df_total = build_audit_report(df, fecha)
    chart_payloads = build_chart_payloads(df_grafico, df_total)
    output_xlsx = export_audit_report(empresa, fecha, work_dir, reporte, chart_payloads)

    return {
        "reporte": reporte,
        "df_grafico": df_grafico,
        "df_total": df_total,
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
    }, None
