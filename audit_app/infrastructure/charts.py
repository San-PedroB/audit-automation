"""Chart generation utilities."""

from __future__ import annotations

import io
import textwrap

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from audit_app.domain.kpi_schema import CAMERA_COLUMN

matplotlib.use("Agg")


def to_num(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.replace("%", "", regex=False)
    return pd.to_numeric(normalized, errors="coerce").fillna(0)


def make_dual_bar_chart(
    labels,
    base_values,
    result_values,
    title,
    label_base="Auditados",
    label_result="Correctos",
):
    bar_width = 0.30
    bar_gap = 0.05
    half = bar_width / 2 + bar_gap / 2
    count = len(labels)

    fig_w = max(8, min(18, 4.5 + count * 1.65))
    fig, ax = plt.subplots(figsize=(fig_w, 6.8))
    fig.patch.set_facecolor("white")

    base_heights = [100.0 for _ in range(count)]
    result_heights = [(r / b * 100) if b > 0 else 0 for r, b in zip(result_values, base_values)]
    x_values = range(count)

    rects1 = ax.bar(
        [i - half for i in x_values],
        base_heights,
        bar_width,
        label=label_base,
        color="#1B2A4A",
        zorder=3,
    )
    rects2 = ax.bar(
        [i + half for i in x_values],
        result_heights,
        bar_width,
        label=label_result,
        color="#C0392B",
        zorder=3,
    )

    ax.grid(axis="y", linestyle="-", color="#EEEEEE", alpha=0.8, zorder=0)

    def autolabel(rects, values):
        for rect, value in zip(rects, values):
            height = rect.get_height()
            ax.annotate(
                f"{int(value)}",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="#1B2A4A",
            )

    autolabel(rects1, base_values)
    autolabel(rects2, result_values)

    ax.set_ylim(0, 115)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_xticks(list(x_values))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9, fontweight="medium")
    ax.set_xlim(-0.7, count - 0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#BBBBBB")
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.set_title(title, pad=60, fontweight="bold", color="#1B2A4A", fontsize=16)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize=11)

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()


def make_summary_bar_chart(labels, values, title, colors):
    fig, ax = plt.subplots(figsize=(9.5, 6.8))
    fig.patch.set_facecolor("white")

    wrapped_labels = [textwrap.fill(label, width=18) for label in labels]
    x_values = range(len(labels))
    bars = ax.bar(x_values, values, color=colors, width=0.52, zorder=3)

    ax.grid(axis="y", linestyle="-", color="#EEEEEE", alpha=0.8, zorder=0)
    ax.set_xticks(list(x_values))
    ax.set_xticklabels(wrapped_labels, rotation=0, ha="center", fontsize=10, fontweight="medium")
    ax.tick_params(axis="y", labelsize=10, colors="#333333")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#BBBBBB")
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.set_title(title, pad=24, fontweight="bold", color="#1B2A4A", fontsize=16)

    max_value = max(values) if values else 0
    ax.set_ylim(0, max_value * 1.18 if max_value > 0 else 1)

    for bar, value in zip(bars, values):
        ax.annotate(
            f"{int(value)}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#1B2A4A",
        )

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()


def build_chart_payloads(df_grafico: pd.DataFrame, df_total: pd.DataFrame) -> dict:
    zone_labels = df_grafico["Zona"].astype(str).tolist()
    total_values = to_num(df_grafico["Total Eventos"]).tolist()
    correct_values = to_num(df_grafico["Eventos Correctos del Sistema"]).tolist()

    global_bytes = make_dual_bar_chart(
        zone_labels,
        total_values,
        correct_values,
        "Eventos Correctos del Sistema por Zona",
        "Total Eventos",
        "Eventos Correctos del Sistema",
    )
    img_global = io.BytesIO(global_bytes)

    img_totales = None
    img_totales_bytes = None
    if not df_total.empty:
        total_row = df_total.iloc[0]
        categories = [
            "Total Eventos",
            "Eventos Registrados por el Sistema",
            "Eventos Correctos del Sistema",
        ]
        values = [
            to_num(pd.Series([value])).iloc[0]
            for value in [
                total_row["Total Eventos"],
                total_row["Eventos Registrados por el Sistema"],
                total_row["Eventos Correctos del Sistema"],
            ]
        ]
        img_totales_bytes = make_summary_bar_chart(
            categories,
            values,
            "Resumen de KPIs de la Tabla Maestra",
            ["#1B2A4A", "#2C5282", "#C0392B"],
        )
        img_totales = io.BytesIO(img_totales_bytes)

    camera_images = []
    camera_coverage_images = []
    camera_summary_images = []
    for cam in df_grafico[CAMERA_COLUMN].unique():
        camera_df = df_grafico[df_grafico[CAMERA_COLUMN] == cam]
        if camera_df.empty:
            continue

        camera_label = f"Camara {int(cam)}" if cam not in ("", "nan", None) else "General"
        zones = camera_df["Zona"].tolist()
        total_camera = to_num(camera_df["Total Eventos"]).tolist()
        registered_camera = to_num(camera_df["Eventos Registrados por el Sistema"]).tolist()
        correct_camera = to_num(camera_df["Eventos Correctos del Sistema"]).tolist()

        summary_bytes = make_dual_bar_chart(
            ["TOTAL CAMARA"],
            [sum(total_camera)],
            [sum(correct_camera)],
            f"Eventos Correctos del Sistema - Resumen Agregado - {camera_label}",
            "Total Eventos",
            "Eventos Correctos del Sistema",
        )
        camera_summary_images.append(
            {"label": camera_label, "buffer": io.BytesIO(summary_bytes), "bytes": summary_bytes}
        )

        camera_bytes = make_dual_bar_chart(
            zones,
            total_camera,
            correct_camera,
            f"Eventos Correctos del Sistema por Zona - {camera_label}",
            "Total Eventos",
            "Eventos Correctos del Sistema",
        )
        camera_images.append(
            {"label": camera_label, "buffer": io.BytesIO(camera_bytes), "bytes": camera_bytes}
        )

        coverage_bytes = make_dual_bar_chart(
            zones,
            total_camera,
            registered_camera,
            f"Eventos Registrados por el Sistema por Zona - {camera_label}",
            "Total Eventos",
            "Eventos Registrados por el Sistema",
        )
        camera_coverage_images.append(
            {"label": camera_label, "buffer": io.BytesIO(coverage_bytes), "bytes": coverage_bytes}
        )

    zone_images = []
    for _, row in df_grafico.iterrows():
        zone_name = str(row["Zona"])
        total_zone = [to_num(pd.Series([row["Total Eventos"]])).iloc[0]]
        correct_zone = [to_num(pd.Series([row["Eventos Correctos del Sistema"]])).iloc[0]]
        zone_bytes = make_dual_bar_chart(
            [zone_name],
            total_zone,
            correct_zone,
            f"Eventos Correctos del Sistema - {zone_name}",
            "Total Eventos",
            "Eventos Correctos del Sistema",
        )
        zone_images.append({"label": zone_name, "buffer": io.BytesIO(zone_bytes), "bytes": zone_bytes})

    unknown_global_bytes = None
    img_unknown_global = None
    total_identity_coverage = pd.to_numeric(pd.Series([df_total.iloc[0]["Cobertura Identity"]]), errors="coerce").iloc[0]
    total_unknown = pd.to_numeric(pd.Series([df_total.iloc[0]["Identity Unknown"]]), errors="coerce").iloc[0]
    if pd.notna(total_identity_coverage) or pd.notna(total_unknown):
        total_registered_for_identity = (0 if pd.isna(total_identity_coverage) else total_identity_coverage) + (
            0 if pd.isna(total_unknown) else total_unknown
        )
        unknown_global_bytes = make_dual_bar_chart(
            ["TOTAL SITIO"],
            [total_registered_for_identity],
            [0 if pd.isna(total_unknown) else total_unknown],
            "Identity Unknown - Resumen Global",
            "Eventos evaluables",
            "Identity Unknown",
        )
        img_unknown_global = io.BytesIO(unknown_global_bytes)

    unknown_images = []
    for _, row in df_grafico.iterrows():
        if pd.isna(row["% Identity Unknown"]):
            continue
        zone_name = str(row["Zona"])
        registered_zone = [
            to_num(pd.Series([(row["Cobertura Identity"] if pd.notna(row["Cobertura Identity"]) else 0) + (row["Identity Unknown"] if pd.notna(row["Identity Unknown"]) else 0)])).iloc[0]
        ]
        unknown_zone = [to_num(pd.Series([row["Identity Unknown"] if pd.notna(row["Identity Unknown"]) else 0])).iloc[0]]
        if registered_zone[0] <= 0:
            continue
        unknown_bytes = make_dual_bar_chart(
            [zone_name],
            registered_zone,
            unknown_zone,
            f"Identity Unknown - {zone_name}",
            "Eventos evaluables",
            "Identity Unknown",
        )
        unknown_images.append(
            {"label": zone_name, "buffer": io.BytesIO(unknown_bytes), "bytes": unknown_bytes}
        )

    return {
        "img_global": img_global,
        "img_global_bytes": global_bytes,
        "img_totales": img_totales,
        "img_totales_bytes": img_totales_bytes,
        "cam_images": camera_images,
        "cam_coverage_images": camera_coverage_images,
        "cam_summary_images": camera_summary_images,
        "zone_images": zone_images,
        "img_unknown_global": img_unknown_global,
        "img_unknown_global_bytes": unknown_global_bytes,
        "unknown_images": unknown_images,
    }
