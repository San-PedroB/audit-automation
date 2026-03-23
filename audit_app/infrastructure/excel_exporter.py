"""Excel export infrastructure."""

from __future__ import annotations

import io
import os

import openpyxl
import pandas as pd
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from audit_app.domain.kpi_schema import COUNT_COLUMNS, KPI_COLUMNS


def export_audit_report(
    empresa: str,
    fecha: str,
    work_dir: str,
    reporte: pd.DataFrame,
    chart_payloads: dict,
    output_filename: str | None = None,
) -> str:
    central_template = os.path.join(os.getcwd(), "templates", "Template Tabla Maestra.xlsx")
    local_template = os.path.join(work_dir, "Template Tabla Maestra.xlsx")
    template_path = central_template if os.path.exists(central_template) else local_template
    if not output_filename:
        output_filename = os.path.join(work_dir, f"Reporte_Auditoria_Maestro_{empresa}.xlsx")

    if not os.path.exists(template_path):
        fallback_filename = os.path.join(work_dir, f"Reporte_Auditoria_{empresa}_{fecha}.xlsx")
        reporte.to_excel(fallback_filename, index=False)
        return fallback_filename

    workbook = openpyxl.load_workbook(template_path)
    worksheet = workbook.active
    column_mapping = {column_name: index + 1 for index, column_name in enumerate(KPI_COLUMNS)}

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    grey_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")

    for column_index in range(1, len(KPI_COLUMNS) + 1):
        cell = worksheet.cell(row=2, column=column_index)
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    for row_index, row in reporte.iterrows():
        excel_row = 3 + row_index
        is_total_row = str(row["Zona"]).upper() == "TOTAL"
        row_font = Font(name="Arial", size=11, bold=True) if is_total_row else Font(name="Arial", size=10)

        for column_name, column_index in column_mapping.items():
            if column_name not in reporte.columns:
                continue

            value = row[column_name]
            cell = worksheet.cell(row=excel_row, column=column_index)

            if isinstance(column_name, str) and column_name.startswith("%"):
                try:
                    cell.value = float(value) if value not in (None, "", "N/A") else 0
                except Exception:
                    cell.value = 0
                cell.number_format = "0.00%"
            elif column_name in COUNT_COLUMNS:
                try:
                    cell.value = int(float(value)) if value not in (None, "", "N/A") else 0
                except Exception:
                    cell.value = 0
                cell.number_format = "0"
            elif column_name == "Tipo_sensor":
                cell.value = str(value) if value is not None else ""
                cell.number_format = "General"
            else:
                cell.value = value if value is not None else ""
                cell.number_format = "General"

            cell.font = row_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border
            cell.fill = grey_fill

    ws_graphs = workbook.create_sheet("Graficos")
    ws_graphs.add_image(XLImage(io.BytesIO(chart_payloads["img_global_bytes"])), "B2")
    if chart_payloads["img_totales_bytes"]:
        ws_graphs.add_image(XLImage(io.BytesIO(chart_payloads["img_totales_bytes"])), "B30")

    ws_camera = workbook.create_sheet("Por Camara")
    cursor = 2
    for index, img_obj in enumerate(chart_payloads["cam_images"]):
        if index < len(chart_payloads["cam_summary_images"]):
            ws_camera.add_image(
                XLImage(io.BytesIO(chart_payloads["cam_summary_images"][index]["bytes"])),
                f"B{cursor}",
            )
            cursor += 25

        ws_camera.add_image(XLImage(io.BytesIO(img_obj["bytes"])), f"B{cursor}")
        if index < len(chart_payloads["cam_coverage_images"]):
            ws_camera.add_image(
                XLImage(io.BytesIO(chart_payloads["cam_coverage_images"][index]["bytes"])),
                f"L{cursor}",
            )
        cursor += 28

    ws_zone = workbook.create_sheet("Detalle por Zona")
    cursor = 2
    for img_obj in chart_payloads["zone_images"]:
        ws_zone.add_image(XLImage(io.BytesIO(img_obj["bytes"])), f"B{cursor}")
        cursor += 25

    ws_unknown = workbook.create_sheet("Analisis de Unknowns")
    ws_unknown.add_image(XLImage(io.BytesIO(chart_payloads["img_unknown_global_bytes"])), "B2")
    cursor = 28
    for img_obj in chart_payloads["unknown_images"]:
        ws_unknown.add_image(XLImage(io.BytesIO(img_obj["bytes"])), f"B{cursor}")
        cursor += 25

    workbook.save(output_filename)
    return output_filename
