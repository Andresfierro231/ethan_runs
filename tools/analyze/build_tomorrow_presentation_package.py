#!/usr/bin/env python3
"""Build a slide-ready package for the July 9 closure presentation.

This package is a communication layer over existing July 8 evidence. It does
not read native OpenFOAM case trees and does not create new closure evidence.
It expands the existing postprocessor chart story into slide titles, bullets,
figure calls, speaker notes, and a small set of support figures that were
identified as missing or useful for tomorrow's discussion.

The SVG writer uses only the Python standard library so the package can be
rebuilt on minimal cluster shells.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products"
    / "2026-07"
    / "2026-07-08"
    / "2026-07-08_tomorrow_presentation_package"
)

INPUTS = {
    "postprocessor_story": REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/presentation_story.md",
    "postprocessor_figures": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures",
    "minor_loss_two_tap": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv",
    "minor_loss_separation": REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_minor_loss_separation/minor_loss_separation.csv",
    "thermal_replay_path_summary": REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_cfd_informed_fixed_mdot_1d_runs/path_summary.csv",
    "thermal_replay_readme": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_cfd_informed_fixed_mdot_1d_runs/README.md",
    "t13_campaign_note": REPO_ROOT / "operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md",
    "mesh_uncertainty_board": REPO_ROOT / ".agent/BOARD.md",
}

BASE_FIGURES = {
    "pressure_decomposition": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/pressure_decomposition_by_span.svg",
    "heat_accounting": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/heat_source_sink_by_patch_group.svg",
    "heat_residuals": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/heat_enthalpy_residual_by_segment.svg",
    "friction_mdot": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/friction_form_mdot_error.svg",
    "friction_leg": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/friction_per_leg_pressure_drop.svg",
    "f5_ri": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/f5_ri_screen_coefficients.svg",
    "upcomer": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/upcomer_backflow_vs_re.svg",
    "gate_status": "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts/figures/corrected_salt_gate_status.svg",
}

T13_ROWS = [
    {"run_id": "S3 anchor", "q_heater_W": 297.5, "expected_Re": 90.0, "status": "admitted current anchor"},
    {"run_id": "T13-A1", "q_heater_W": 595.0, "expected_Re": 107.0, "status": "proposed"},
    {"run_id": "T13-A2", "q_heater_W": 1190.0, "expected_Re": 161.0, "status": "proposed"},
    {"run_id": "T13-A3", "q_heater_W": 2380.0, "expected_Re": 221.0, "status": "proposed onset target"},
    {"run_id": "T13-A4", "q_heater_W": 4760.0, "expected_Re": 305.0, "status": "proposed high-Re check"},
    {"run_id": "T13-A5", "q_heater_W": 9520.0, "expected_Re": 428.0, "status": "optional convergence risk"},
]

COLORS = {
    "blue": "#2563EB",
    "orange": "#D97706",
    "green": "#15803D",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "teal": "#0F766E",
    "gray": "#6B7280",
    "light_gray": "#E5E7EB",
    "dark": "#111827",
    "white": "#FFFFFF",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fnum(value: object, default: float = 0.0) -> float:
    text = "" if value is None else str(value).strip()
    if not text or text.lower() in {"nan", "na", "none"}:
        return default
    return float(text)


def safe(value: object) -> str:
    return html.escape(str(value), quote=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def fmt(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{value:.2f}".rstrip("0").rstrip(".")


def wrap(text: str, width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        proposed = " ".join(current + [word])
        if current and len(proposed) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def svg_start(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COLORS["white"]}"/>',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#111827}",
        ".title{font-size:22px;font-weight:700}",
        ".subtitle{font-size:12px;fill:#4B5563}",
        ".tick{font-size:11px;fill:#4B5563}",
        ".small{font-size:10px;fill:#4B5563}",
        ".label{font-size:12px;fill:#111827}",
        ".legend{font-size:11px;fill:#111827}",
        ".axis{stroke:#374151;stroke-width:1}",
        ".grid{stroke:#E5E7EB;stroke-width:1}",
        "</style>",
    ]


def svg_finish(parts: list[str], path: Path) -> None:
    parts.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def ticks(min_value: float, max_value: float, count: int = 5) -> list[float]:
    if math.isclose(min_value, max_value):
        pad = abs(max_value) or 1.0
        min_value -= pad
        max_value += pad
    raw = (max_value - min_value) / max(count - 1, 1)
    mag = 10 ** math.floor(math.log10(abs(raw)))
    norm = raw / mag
    if norm > 5:
        step = 10 * mag
    elif norm > 2:
        step = 5 * mag
    elif norm > 1:
        step = 2 * mag
    else:
        step = mag
    start = math.floor(min_value / step) * step
    end = math.ceil(max_value / step) * step
    result = []
    value = start
    for _ in range(80):
        if value > end + 0.5 * step:
            break
        result.append(0.0 if abs(value) < 1e-12 else value)
        value += step
    return result


def draw_note(parts: list[str], x: int, y: int, text: str, width_chars: int = 140) -> None:
    for idx, line in enumerate(wrap(text, width_chars)):
        parts.append(f'<text x="{x}" y="{y + idx * 14}" class="small">{safe(line)}</text>')


def draw_grouped_bar_chart(
    path: Path,
    title: str,
    subtitle: str,
    groups: Sequence[str],
    series: Sequence[str],
    values: Mapping[tuple[str, str], float],
    colors: Mapping[str, str],
    y_label: str,
    note: str,
    width: int = 1180,
    height: int = 680,
) -> None:
    left, right, top, bottom = 86, 36, 88, 145
    plot_w = width - left - right
    plot_h = height - top - bottom
    all_values = [values[(group, name)] for group in groups for name in series if (group, name) in values]
    min_tick = min(ticks(min(0.0, min(all_values)), max(0.0, max(all_values))))
    max_tick = max(ticks(min(0.0, min(all_values)), max(0.0, max(all_values))))
    y_ticks = ticks(min_tick, max_tick)
    min_tick, max_tick = min(y_ticks), max(y_ticks)

    def y_pos(value: float) -> float:
        return top + (max_tick - value) / (max_tick - min_tick) * plot_h

    parts = svg_start(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe(subtitle)}</text>')

    zero_y = y_pos(0.0)
    for tick in y_ticks:
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="tick">{safe(fmt(tick))}</text>')
    parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{width - right}" y2="{zero_y:.1f}" class="axis"/>')
    parts.append(f'<text x="24" y="{top + plot_h / 2:.1f}" class="label" transform="rotate(-90 24 {top + plot_h / 2:.1f})">{safe(y_label)}</text>')

    group_w = plot_w / max(len(groups), 1)
    bar_w = min(48.0, group_w / (len(series) + 1.4))
    for gi, group in enumerate(groups):
        center = left + group_w * (gi + 0.5)
        for si, name in enumerate(series):
            value = values.get((group, name), 0.0)
            x = center - (len(series) * bar_w) / 2 + si * bar_w
            y = min(y_pos(value), zero_y)
            h = abs(zero_y - y_pos(value))
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.82:.1f}" height="{h:.1f}" fill="{colors[name]}"/>'
            )
            label_y = y - 5 if value >= 0 else y + h + 13
            parts.append(f'<text x="{x + bar_w * 0.41:.1f}" y="{label_y:.1f}" text-anchor="middle" class="small">{safe(fmt(value))}</text>')
        for li, line in enumerate(wrap(group, 13)):
            parts.append(f'<text x="{center:.1f}" y="{top + plot_h + 28 + li * 13}" text-anchor="middle" class="tick">{safe(line)}</text>')

    legend_x = left
    legend_y = height - 72
    for si, name in enumerate(series):
        x = legend_x + si * 210
        parts.append(f'<rect x="{x}" y="{legend_y - 10}" width="12" height="12" fill="{colors[name]}"/>')
        parts.append(f'<text x="{x + 18}" y="{legend_y}" class="legend">{safe(name)}</text>')
    draw_note(parts, left, height - 38, note)
    svg_finish(parts, path)


def draw_line_chart(
    path: Path,
    title: str,
    subtitle: str,
    rows: Sequence[Mapping[str, object]],
    x_key: str,
    y_key: str,
    x_label: str,
    y_label: str,
    note: str,
    width: int = 1180,
    height: int = 680,
) -> None:
    left, right, top, bottom = 88, 44, 88, 130
    plot_w = width - left - right
    plot_h = height - top - bottom
    xs = [fnum(row[x_key]) for row in rows]
    ys = [fnum(row[y_key]) for row in rows]
    y_ticks = ticks(0.0, max(ys) * 1.08)
    y_min, y_max = min(y_ticks), max(y_ticks)
    x_min, x_max = min(xs), max(xs)

    def x_pos(value: float) -> float:
        if math.isclose(x_min, x_max):
            return left + plot_w / 2
        return left + (value - x_min) / (x_max - x_min) * plot_w

    def y_pos(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_h

    parts = svg_start(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe(subtitle)}</text>')

    for tick in y_ticks:
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="tick">{safe(fmt(tick))}</text>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{width - right}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<text x="{left + plot_w / 2:.1f}" y="{height - 60}" text-anchor="middle" class="label">{safe(x_label)}</text>')
    parts.append(f'<text x="24" y="{top + plot_h / 2:.1f}" class="label" transform="rotate(-90 24 {top + plot_h / 2:.1f})">{safe(y_label)}</text>')

    points = [(x_pos(x), y_pos(y)) for x, y in zip(xs, ys)]
    path_d = " ".join([("M" if idx == 0 else "L") + f"{x:.1f},{y:.1f}" for idx, (x, y) in enumerate(points)])
    parts.append(f'<path d="{path_d}" fill="none" stroke="{COLORS["blue"]}" stroke-width="3"/>')
    for threshold, color in [(200, COLORS["orange"]), (300, COLORS["red"])]:
        y = y_pos(threshold)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{color}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        parts.append(f'<text x="{width - right - 6}" y="{y - 5:.1f}" text-anchor="end" class="small">Re {threshold}</text>')
    for row, (x, y) in zip(rows, points):
        q = fnum(row[x_key])
        re = fnum(row[y_key])
        fill = COLORS["dark"] if str(row.get("run_id")) == "S3 anchor" else COLORS["blue"]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{fill}"/>')
        parts.append(f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" class="small">{safe(str(row["run_id"]))}</text>')
        parts.append(f'<text x="{x:.1f}" y="{top + plot_h + 23}" text-anchor="middle" class="tick">{safe(fmt(q))}</text>')
        parts.append(f'<text x="{x:.1f}" y="{y + 19:.1f}" text-anchor="middle" class="small">{safe(fmt(re))}</text>')
    draw_note(parts, left, height - 32, note)
    svg_finish(parts, path)


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def build_minor_loss_k_figure(output_dir: Path) -> tuple[str, list[dict[str, object]]]:
    rows = [row for row in read_csv(INPUTS["minor_loss_two_tap"]) if row["status"] == "computed_from_preserved_two_tap_feature_rows"]
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"K apparent": [], "K local": []})
    for row in rows:
        label = row["feature"].replace("corner_", "").replace("_", " ")
        grouped[label]["K apparent"].append(fnum(row["K_apparent"]))
        grouped[label]["K local"].append(fnum(row["K_local"]))
    groups = sorted(grouped)
    series = ["K apparent", "K local"]
    values = {(group, name): mean(grouped[group][name]) for group in groups for name in series}
    fig = output_dir / "figures" / "minor_loss_k_apparent_vs_local.svg"
    draw_grouped_bar_chart(
        fig,
        "Minor-loss K drops after adjacent straight-loss subtraction",
        "Salt 2/3/4 preserved corner rows; test-section complex still requires raw two-tap extraction",
        groups,
        series,
        values,
        {"K apparent": COLORS["orange"], "K local": COLORS["blue"]},
        "Mean K",
        "K_local remains an upper-bound estimate because preserved rows use an abs(dz) tap-length proxy, not full centerline tap-to-tap length.",
    )
    summary = [
        {"feature": group, "mean_K_apparent": values[(group, "K apparent")], "mean_K_local": values[(group, "K local")]}
        for group in groups
    ]
    return rel(fig), summary


def build_minor_loss_separation_figure(output_dir: Path) -> tuple[str, list[dict[str, object]]]:
    rows = [row for row in read_csv(INPUTS["minor_loss_separation"]) if row["valid"] == "True" and row["leg_class"] != "upcomer"]
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"phi original": [], "phi pipe only": [], "minor_fraction_pct": []})
    for row in rows:
        leg = row["leg_class"]
        grouped[leg]["phi original"].append(fnum(row["phi_original"]))
        grouped[leg]["phi pipe only"].append(fnum(row["phi_pipe_only"]))
        grouped[leg]["minor_fraction_pct"].append(fnum(row["minor_fraction_pct"]))
    groups = ["heater", "cooler", "downcomer"]
    series = ["phi original", "phi pipe only"]
    values = {(group, name): mean(grouped[group][name]) for group in groups for name in series}
    fig = output_dir / "figures" / "minor_loss_separation_phi.svg"
    draw_grouped_bar_chart(
        fig,
        "Corner losses do not explain the distributed friction excess",
        "Mean Salt 2/3/4 main-pipe spans; upcomer excluded because recirculation invalidates single-stream friction",
        groups,
        series,
        values,
        {"phi original": COLORS["purple"], "phi pipe only": COLORS["green"]},
        "phi relative to F3 Shah",
        "Corner attribution removes about 9-10% of main-pipe span pressure drop, but phi_pipe_only remains about 1.39-1.65.",
    )
    summary = [
        {
            "leg_class": group,
            "mean_phi_original": values[(group, "phi original")],
            "mean_phi_pipe_only": values[(group, "phi pipe only")],
            "mean_minor_fraction_pct": mean(grouped[group]["minor_fraction_pct"]),
        }
        for group in groups
    ]
    return rel(fig), summary


def build_thermal_replay_figure(output_dir: Path) -> tuple[str, list[dict[str, object]]]:
    rows = read_csv(INPUTS["thermal_replay_path_summary"])
    labels = {
        "P0_fixed_mdot_current_1d_contract": "Baseline current 1D",
        "P1_cfd_cooler_duty_only": "CFD cooler duty only",
        "P4_cfd_cooler_plus_heater_wallflux": "CFD cooler + heater flux",
    }
    selected = [row for row in rows if row["path_id"] in labels]
    groups = [labels[row["path_id"]] for row in selected]
    descriptions = {
        row["path_id"].split("_", 1)[0]: row["interpretation"]
        for row in rows
    }
    series = ["mean |Tmean error|", "mean |loop dT error|"]
    values = {}
    summary = []
    for row, group in zip(selected, groups):
        t_err = fnum(row["mean_abs_Tmean_error_K"])
        dt_err = fnum(row["mean_abs_loop_delta_T_error_K"])
        values[(group, series[0])] = t_err
        values[(group, series[1])] = dt_err
        summary.append(
            {
                "path": group,
                "path_id": row["path_id"],
                "mean_abs_Tmean_error_K": t_err,
                "mean_abs_loop_delta_T_error_K": dt_err,
                "thermal_gate_pass": row["thermal_gate_pass"],
                "interpretation": row["interpretation"],
            }
        )
    fig = output_dir / "figures" / "fixed_mdot_thermal_replay_error.svg"
    draw_grouped_bar_chart(
        fig,
        "Prescribing CFD cooler duty collapses the fixed-mdot temperature error",
        "Salt 2/3/4 mean errors at CFD mdot; pressure residual is diagnostic, not a gate",
        groups,
        series,
        values,
        {series[0]: COLORS["red"], series[1]: COLORS["teal"]},
        "Mean absolute error (K)",
        "Baseline is the current 1D thermal contract at CFD mdot. CFD cooler duty alone is the best three-case mean replay; adding CFD heater wall flux over-cools the loop.",
    )
    write_csv(
        output_dir / "tables" / "thermal_replay_path_labels.csv",
        [{"path": key, "interpretation": descriptions[key]} for key in sorted(descriptions)],
        ["path", "interpretation"],
    )
    return rel(fig), summary


def build_slide6_thermal_analysis_note(output_dir: Path) -> None:
    summary_rows = read_csv(INPUTS["thermal_replay_path_summary"])
    run_rows = read_csv(INPUTS["thermal_replay_path_summary"].with_name("fixed_mdot_pressure_replay_results.csv"))
    by_path = {row["path_id"]: row for row in summary_rows}
    selected_ids = [
        "P0_fixed_mdot_current_1d_contract",
        "P1_cfd_cooler_duty_only",
        "P4_cfd_cooler_plus_heater_wallflux",
    ]
    selected_results = [row for row in run_rows if row["path_id"] in selected_ids]

    def value(path_id: str, column: str) -> float:
        return fnum(by_path[path_id][column])

    def per_case_lines(path_id: str) -> list[str]:
        lines = []
        for row in selected_results:
            if row["path_id"] != path_id:
                continue
            lines.append(
                "- `{case}`: `Tmean_error_K = {terr:.2f}`, `loop_delta_T_error_K = {dterr:.2f}`, "
                "`qhx_total_W = {qhx:.2f}`, `qambient_total_W = {qamb:.2f}`, `source_total_W = {src:.2f}`".format(
                    case=row["case_id"],
                    terr=fnum(row["Tmean_error_K"]),
                    dterr=fnum(row["loop_delta_T_error_K"]),
                    qhx=fnum(row["qhx_total_W"]),
                    qamb=fnum(row["qambient_total_W"]),
                    src=fnum(row["source_total_W"]),
                )
            )
        return lines

    lines = [
        "# Slide 6 Thermal Replay Interpretation",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`",
        "Task: `AGENT-219` presentation package follow-up",
        "",
        "## What Baseline / Current 1D Means",
        "",
        "The slide-6 baseline is `P0_fixed_mdot_current_1d_contract`. It is not the fully predictive 1D solve and it is not a CFD-prescribed heat-ledger replay. It is a fixed-mdot thermal replay that holds the 1D mass flow equal to the admitted Salt CFD mass flow and then solves only the 1D thermal periodicity problem. The pressure residual is still reported, but it is diagnostic and is not used to change mdot.",
        "",
        "Within that fixed-mdot replay, `current 1D` means the existing Fluid salt thermal contract:",
        "",
        "- geometry and refined Fluid loop segmentation are unchanged;",
        "- mdot is imposed from CFD for Salt 2/3/4;",
        "- the heater/source side uses the current Fluid salt source contract: imposed heater duty plus the legacy `37 W` test-section input;",
        "- the cooler/HX side remains the predictive air-side HX model rather than a CFD-prescribed cooler heat rate;",
        "- internal ambient/passive-loss and radiation settings remain those used by the current Fluid salt scenario;",
        "- no CFD patchwise heat-loss map is injected;",
        "- no hydraulic pressure-root search is performed.",
        "",
        "So the baseline answers a narrow question: if the hydraulic state is forced to match CFD mdot, how wrong is the current 1D thermal boundary model by itself?",
        "",
        "## Focused Comparison",
        "",
        "| Replay path | What changes relative to baseline | Mean `|Tmean error|` | Mean `|loop delta-T error|` | Interpretation |",
        "| --- | --- | ---: | ---: | --- |",
        f"| Baseline current 1D (`P0`) | Nothing; current Fluid thermal contract at CFD mdot | {value(selected_ids[0], 'mean_abs_Tmean_error_K'):.2f} K | {value(selected_ids[0], 'mean_abs_loop_delta_T_error_K'):.2f} K | 1D loop mean is much too hot. |",
        f"| CFD cooler duty only (`P1`) | Replace predictive air-side HX duty with CFD cooler `wallHeatFlux` magnitude; keep current 1D sources | {value(selected_ids[1], 'mean_abs_Tmean_error_K'):.2f} K | {value(selected_ids[1], 'mean_abs_loop_delta_T_error_K'):.2f} K | Best three-case mean thermal-state replay. |",
        f"| CFD cooler + heater flux (`P4`) | Prescribe CFD cooler duty and CFD heater interface wall flux; omit legacy `37 W` test-section source | {value(selected_ids[2], 'mean_abs_Tmean_error_K'):.2f} K | {value(selected_ids[2], 'mean_abs_loop_delta_T_error_K'):.2f} K | Loop becomes too cold by roughly 39-41 K in each case. |",
        "",
        "## Why The Agreement Behaves This Way",
        "",
        "The baseline error is dominated by the absolute heat-removal level, not by the loop delta-T shape. In `P0`, the current 1D model removes only about `46-53 W` through the HX while also removing `256-318 W` through ambient/passive paths. The replay still closes thermal periodicity, but it lands at a loop-mean temperature about `62-65 K` above CFD. This is consistent with an external-boundary mismatch: the modeled temperature-dependent sink network finds a different absolute equilibrium temperature than the CFD case.",
        "",
        "Prescribing only the CFD cooler duty fixes the dominant absolute-temperature anchor. In `P1`, `qhx_total_W` becomes the CFD cooler magnitude, about `136 W`, `151 W`, and `169 W` for Salt 2/3/4. The current 1D sources are left alone, and the remaining ambient/passive loss falls to `166-205 W` because the loop equilibrates near a cooler mean temperature. That combination brings the loop mean to within `2.7-6.2 K` of CFD and keeps loop delta-T error below `0.2 K` on average. This is why the slide claim should be phrased as: the cooler/HX heat-removal model is the largest current thermal-state lever.",
        "",
        "Adding CFD heater wall flux in `P4` makes the result worse because it changes the source side at the same time as the cooler side. The CFD heater-interface wall flux used by this replay is lower than the current 1D source contract: the source total drops from `302.7/334.5/374.6 W` in `P0/P1` to `243.5/273.2/310.5 W` in `P4`. With the stronger CFD cooler duty still imposed, that lower source contract over-cools the 1D loop. The sign of the error flips: the model mean temperature is about `38.6-40.9 K` below CFD.",
        "",
        "Scientifically, this says the one-at-a-time cooler intervention is more diagnostic than the combined cooler+heater intervention. The cooler-only replay shows that the current predictive HX/cooler boundary is the main reason the current 1D thermal state sits too hot at CFD mdot. The combined replay shows that simply replacing multiple thermal terms with patchwise CFD values is not automatically more physical inside the current 1D semantics, because the source, passive-loss, and imposed-HX contracts are coupled through the periodic mean-temperature solve.",
        "",
        "## Per-Case Values",
        "",
        "### Baseline current 1D (`P0`)",
        "",
        *per_case_lines(selected_ids[0]),
        "",
        "### CFD cooler duty only (`P1`)",
        "",
        *per_case_lines(selected_ids[1]),
        "",
        "### CFD cooler + heater flux (`P4`)",
        "",
        *per_case_lines(selected_ids[2]),
        "",
        "## Presentation Wording",
        "",
        "Use this wording on the slide: `At fixed CFD mdot, the current 1D thermal contract is about 64 K too hot in loop mean temperature. Replacing only the predictive cooler/HX duty with the CFD cooler wallHeatFlux magnitude reduces the mean error to about 4.5 K. Replacing both cooler duty and heater wall flux over-corrects because the source contract changes at the same time, so this is a diagnostic replay, not a final predictive model.`",
        "",
        "## Claim Boundary",
        "",
        "This slide does not prove that prescribing CFD cooler duty is a predictive model. It proves that the cooler/HX boundary condition is the dominant lever in the fixed-mdot thermal-state mismatch. The next 1D model should predict that cooler removal from geometry, coolant conditions, and heat-transfer closure rather than importing it from CFD.",
    ]
    (output_dir / "slide6_thermal_replay_analysis.md").write_text("\n".join(lines) + "\n")


def build_t13_figure(output_dir: Path) -> tuple[str, list[dict[str, object]]]:
    fig = output_dir / "figures" / "t13_re_sweep_plan.svg"
    draw_line_chart(
        fig,
        "T13 proposal targets the missing Re range for onset and F6/F5 separation",
        "Q sweep from Salt 3 anchor; proposed rows are not yet CFD evidence",
        T13_ROWS,
        "q_heater_W",
        "expected_Re",
        "Heater Q (W)",
        "Estimated Re",
        "Use as a planning figure only: T13 depends on corrected-Salt gate/admission and does not replace mesh or time-window uncertainty.",
    )
    return rel(fig), [dict(row) for row in T13_ROWS]


def build_slide_outline(output_dir: Path, generated_figures: Mapping[str, str]) -> None:
    slide_path = output_dir / "slide_outline_with_speaker_notes.md"
    text = f"""# July 9 Presentation Outline With Speaker Notes

Generated: `{datetime.now(timezone.utc).isoformat(timespec="seconds")}`
Task: `AGENT-219`

## Presentation Thesis

The strongest defensible story is not a final closure coefficient. It is that
the CFD evidence has now been decomposed into pressure, heat, and regime terms
with explicit provenance, residuals, admission boundaries, and next actions for
turning the 1D model into a predictive surrogate.

## Slide 1 - Why the 1D model cannot be one tuned friction factor

**Use figure:** optional title slide, no required figure.

**Bullets**

- Goal: make the 1D model predictive against CFD, not merely tuned to mass flow.
- Today's evidence separates pressure, heat-path, and recirculation-regime terms.
- Claim boundary: this is a rigorous decomposition story, not a final coefficient story.

**Speaker notes**

Start by setting expectations. The project is now past the stage where one
global multiplier is the right scientific object. The data show several coupled
effects: buoyancy and pressure decomposition, thermal-boundary mismatch, and an
upcomer recirculation regime. The value of today's work is that these terms are
being separated so that future 1D closure terms have identifiable targets.

## Slide 2 - Evidence contract and admission boundary

**Use figure:** none required; use a compact table if the deck needs one.

**Bullets**

- Salt 2/3/4 Jin mainline rows are the current admitted evidence set.
- Corrected Salt rows are status-only until the gate requalifies them.
- All current QOIs still carry `coarse_no_gci`; mesh/GCI remains a publication gate.
- CFD setup audit: Salt CFD uses a 1.4 in layer and emissivity metadata, but no exported `qr` radiation field.

**Speaker notes**

This slide is the guardrail. The analysis is useful because every row is labeled
by its admission status. Salt 2/3/4 are the current mainline rows for closure
decomposition. Corrected Salt may become valuable, but right now it is not fit
evidence. That distinction keeps tomorrow's claims conservative and defensible.

## Slide 3 - Pressure decomposition: raw p_rgh is not friction

**Use figure:** `{BASE_FIGURES["pressure_decomposition"]}`

**Bullets**

- July 8 pressure ledger has 18 Salt 2/3/4 span rows.
- It separates endpoint `p_rgh`, dynamic head, total-pressure proxy, buoyancy,
  distributed loss, development/reset, minor-loss upper bound, recirculation
  flags, and residual.
- 12 rows are fit-eligible; 6 recirculation-invalid rows are excluded from
  single-stream friction fitting.

**Speaker notes**

The key point is that pressure loss is not being read directly from a raw static
or `p_rgh` slope. The ledger separates what is observed directly from what is
inferred as mechanical loss or residual. This is the pressure backbone for a
predictive 1D model.

## Slide 4 - Heat accounting: the boundary condition is first-order

**Use figure:** `{BASE_FIGURES["heat_accounting"]}`

**Bullets**

- Patchwise heat ledger reconciles imposed duties, wallHeatFlux, enthalpy
  changes, cooler sink, passive losses, and sign conventions.
- Cooler imposed duty and wallHeatFlux are closely aligned in CFD.
- Heater imposed duty is not identical to realized heater wallHeatFlux.
- Test section appears as a net sink in wall-flux accounting.

**Speaker notes**

The thermal boundary cannot be treated as a minor correction. The heat ledger
shows that the setup-level power and the realized fluid-side heat transfer are
not always the same object. This matters for 1D model comparison because the 1D
state can look wrong for thermal reasons even if the pressure closure is moving
in the right direction.

## Slide 5 - Segment enthalpy residuals expose where thermal closure is weak

**Use figure:** `{BASE_FIGURES["heat_residuals"]}`

**Bullets**

- Span endpoint temperatures now support segment-level heat residuals.
- Non-junction absolute heat residuals are about 36.7 W to 162.7 W.
- Upcomer residuals are diagnostic because recirculation violates ordinary
  single-stream assumptions.
- Cooler residuals remain caveated because current endpoints partially bracket
  the cooler.

**Speaker notes**

This is the bridge from a heat-source table to a closure target. The residuals
are not all fit targets yet, but they tell us where the thermal model is missing
physics or where the CFD reduction needs better bracketing.

## Slide 6 - Fixed-mdot thermal replay: cooler/HX path is the biggest lever

**Use figure:** `{generated_figures["thermal_replay"]}`

**Bullets**

- AGENT-211 ran fixed-mdot thermal replays at CFD mdot.
- Baseline mean temperature error is about 64 K.
- Prescribing CFD cooler duty alone drops mean temperature error to about 4.5 K.
- Prescribing both CFD cooler duty and CFD heater wall flux over-corrects the
  mean temperature by about 40 K because the source contract changes too.
- No replay path passes the strict thermal gate yet; this is diagnosis, not a
  final predictive thermal model.

**Speaker notes**

This slide answers the thermal-state mismatch question directly. The strongest
single issue is the cooler/HX heat-removal path. We can make the thermal state
much closer by prescribing the CFD cooler duty, but that is not yet predictive.
The current-1D baseline means the existing Fluid salt thermal contract at fixed
CFD mdot: current heater/source contract, predictive air-side HX, internal
ambient/passive-loss model, radiation setting retained, no CFD heat ledger
injected, and no pressure-root mdot solve. The cooler-plus-heater replay is a
useful warning: importing more CFD heat terms is not automatically better
inside the current source/loss semantics. The next model must predict cooler
removal from geometry and boundary conditions rather than importing it from CFD.
Use `slide6_thermal_replay_analysis.md` for the detailed scientific
interpretation and baseline definition.

## Slide 7 - Friction-form screen: F3 Shah is the current mdot baseline

**Use figure:** `{BASE_FIGURES["friction_mdot"]}`

**Optional support:** `{BASE_FIGURES["friction_leg"]}`

**Bullets**

- Fully developed F1 overpredicts mdot by about 9.7% to 18.0%.
- F3 Shah apparent narrows mdot error to about -0.9% to 3.7%.
- F4 leg-class over-stiffens the loop at about -24.7% to -23.2% mdot error.
- Mdot agreement alone is not enough; pressure distribution and thermal state
  must be scored separately.

**Speaker notes**

This is a useful result but not the final answer. F3 Shah apparent is the best
current mdot baseline, and that makes physical sense because the flow is not
fully developed. But a model that gets only total mass flow right can still get
the wrong pressure distribution or thermal state.

## Slide 8 - Minor losses: corrected K is smaller, but corners are not the full story

**Use figures:** `{generated_figures["minor_loss_k"]}` and `{generated_figures["minor_loss_separation"]}`

**Bullets**

- Two-tap reduction separates diagnostic `K_apparent` from corrected/local
  `K_local`.
- `K_local` is much lower after subtracting adjacent straight-loss contribution,
  but still an upper-bound estimate.
- Corner bends explain only about 8-12% of span-level pressure drop in the main
  pipe spans.
- Residual pipe-only phi remains about 1.34-1.90 after corner attribution.

**Speaker notes**

This slide is the pressure-breakdown nuance. We should not throw all residual
pressure into bend K values. The current evidence says corners matter, but they
do not explain the dominant excess above F3 Shah. That points toward secondary
flow, bend redevelopment, buoyancy-driven cross-section structure, or model-form
terms that remain distributed rather than purely local.

## Slide 9 - F5/Ri screen failed honestly; T13 is the path to separation

**Use figures:** `{BASE_FIGURES["f5_ri"]}` and `{generated_figures["t13"]}`

**Bullets**

- Current admitted dataset has only three Salt operating points.
- F5/Ri coefficients are zero/deactivated in the present screen.
- Re and Ri are too collinear in the current dataset to separate mechanisms.
- T13 proposes Q sweep from Salt 3 anchor to reach roughly Re 160, 220, 305, and
  possibly 428.

**Speaker notes**

This is a good negative result. The framework for Ri correction exists, but the
current data do not support a real fitted Ri law. T13 is valuable because it
pushes the loop across the missing Re range and may separate recirculation onset,
development effects, and buoyancy effects.

## Slide 10 - Upcomer: this is a recirculation-cell regime

**Use figure:** `{BASE_FIGURES["upcomer"]}`

**Bullets**

- All admitted Salt 2/3/4 upcomer points classify as recirculation-cell observed.
- Backflow fraction decreases with Re but remains nonzero at Salt 4.
- Upcomer rows should be validation/regime diagnostics, not ordinary pipe-friction fit rows.
- Need additional points near Re 150-250 to locate onset.

**Speaker notes**

This is where the 1D model needs a regime boundary. The upcomer cannot be
treated as an ordinary single-stream pipe span while the CFD shows a
recirculation cell. We either exclude it from ordinary friction fitting or build
a separate recirculation/regime term.

## Slide 11 - What is moving and what is still blocked

**Use figure:** `{BASE_FIGURES["gate_status"]}`

**Bullets**

- Converged Salt-Q perturbations are closure evidence; failed/cancelled rows remain blocked.
- Mesh/GCI uncertainty is still missing for publication-grade coefficient claims.
- Time-window uncertainty still needs a dedicated package.
- Raw two-tap reducer/junction extraction and station-resolved development
  analysis remain high-value follow-ups.

**Speaker notes**

This slide prevents overclaiming. The work is in a much stronger state than it
was yesterday, but the gate and uncertainty tasks are real. The right message is
that we know which claims are ready for tomorrow and which ones are still in
progress.

## Slide 12 - Close: what can be done today versus what remains thesis work

**Use figure:** optional summary table.

**Bullets**

- Ready for tomorrow: pressure decomposition, heat accounting, thermal residuals,
  friction mdot screen, minor-loss support figures, upcomer regime, gate status.
- Can be started immediately: mesh/GCI intake, time-window uncertainty,
  raw two-tap feature extraction, station-resolved development analysis.
- Thesis/paper direction: common observation schema, separate objective scores,
  predictive heater/cooler boundary models, and regime-aware upcomer treatment.

**Speaker notes**

End with the path forward. The next version of the 1D model should be judged on
multiple objective columns, not just mass flow. The pieces are now laid out:
pressure terms, heat terms, recirculation flags, and uncertainty requirements.
"""
    slide_path.write_text(text)


def build_missing_figures_note(output_dir: Path, generated_figures: Mapping[str, str]) -> None:
    text = f"""# Missing And Nice-To-Have Figures

Generated: `{datetime.now(timezone.utc).isoformat(timespec="seconds")}`

## Created In This Package

- `{generated_figures["minor_loss_k"]}`: `K_apparent` versus `K_local` from the
  July 8 two-tap minor-loss ledger.
- `{generated_figures["minor_loss_separation"]}`: main-pipe phi before and after
  corner-loss attribution from AGENT-210 minor-loss separation.
- `{generated_figures["thermal_replay"]}`: fixed-mdot thermal replay errors from
  AGENT-211 path summary.
- `{generated_figures["t13"]}`: T13 Q-to-Re campaign planning figure from the
  AGENT-210 proposal.

## Still Missing Before Stronger Claims

- Mesh/GCI uncertainty figure: cannot be created honestly until
  `TODO-MESH-UNCERTAINTY` inventories readable mesh levels and QOI comparisons.
- Time-window uncertainty figure: needs drift/amplitude/block-mean uncertainty
  package before steady-window confidence bands are defensible.
- Raw two-tap reducer/junction figure: current two-tap package flags the
  test-section complex as requiring raw extraction.
- Station-resolved development figure: needs pressure-gradient relaxation,
  early/late slope, profile-shape metric, x+, and post-bend reset flags.
- Upcomer invalidity detail figure: needs backflow fraction, reverse momentum,
  wrong-sign area, pressure recovery, and total-pressure monotonicity on the
  same plot/table.

## Recommended Deck Use

Keep the main deck compact. Use the original postprocessor figures for the core
story, then use the four new figures as support slides or backups when questions
come up about minor losses, thermal mismatch, and the next CFD campaign.
"""
    (output_dir / "missing_and_nice_to_have_figures.md").write_text(text)


def build_readme(output_dir: Path, generated_figures: Mapping[str, str]) -> None:
    text = f"""# Tomorrow Presentation Package

Generated: `{datetime.now(timezone.utc).isoformat(timespec="seconds")}`
Task: `AGENT-219`

## Scope

This package expands the July 8 postprocessor story into a slide-ready outline
with bullet points, figure calls, and speaker notes. It also creates four
support figures from existing evidence using a reusable script. It performs no
new OpenFOAM extraction and creates no new closure fit.

## Main Outputs

- `slide_outline_with_speaker_notes.md`
- `slide6_thermal_replay_analysis.md`
- `missing_and_nice_to_have_figures.md`
- `figure_manifest.csv`
- `source_inventory.csv`
- `summary.json`
- `figures/minor_loss_k_apparent_vs_local.svg`
- `figures/minor_loss_separation_phi.svg`
- `figures/fixed_mdot_thermal_replay_error.svg`
- `figures/t13_re_sweep_plan.svg`

## Interpretation Boundary

Tomorrow's defensible claim is that pressure, heat, and regime terms are now
being decomposed into traceable ledgers with admission boundaries. The current
package should not be used to claim final publication-grade closure coefficients
because mesh/GCI, time-window uncertainty, corrected Salt gate admission, and
some raw two-tap feature extraction remain incomplete.

## Reproduce

```bash
cd {REPO_ROOT}
python tools/analyze/build_tomorrow_presentation_package.py
python -m pytest tools/analyze/test_tomorrow_presentation_package.py -q
```
"""
    (output_dir / "README.md").write_text(text)


def write_manifest(output_dir: Path, generated_figures: Mapping[str, str]) -> None:
    rows = [
        {
            "figure": generated_figures["minor_loss_k"],
            "source": rel(INPUTS["minor_loss_two_tap"]),
            "evidence_class": "support_figure_existing_evidence",
            "message": "Corrected/local K is lower than apparent K after adjacent straight-loss subtraction.",
            "caveat": "K_local remains upper-bound because preserved rows lack full centerline tap length.",
        },
        {
            "figure": generated_figures["minor_loss_separation"],
            "source": rel(INPUTS["minor_loss_separation"]),
            "evidence_class": "support_figure_existing_evidence",
            "message": "Corners explain only a small fraction of main-pipe span pressure drop.",
            "caveat": "Upcomer excluded; attribution depends on preserved-evidence assumptions.",
        },
        {
            "figure": generated_figures["thermal_replay"],
            "source": rel(INPUTS["thermal_replay_path_summary"]),
            "evidence_class": "diagnostic_1d_replay",
            "message": "Baseline, CFD cooler duty, and CFD cooler plus heater flux are compared with readable labels.",
            "caveat": "Fixed-mdot replay is diagnostic and not a predictive hydraulic solution.",
        },
        {
            "figure": generated_figures["t13"],
            "source": rel(INPUTS["t13_campaign_note"]),
            "evidence_class": "proposal_not_closure_evidence",
            "message": "T13 Q sweep targets missing Re range for onset and F5/F6 separation.",
            "caveat": "Planning figure only; proposed runs are not admitted CFD evidence.",
        },
    ]
    write_csv(output_dir / "figure_manifest.csv", rows, ["figure", "source", "evidence_class", "message", "caveat"])

    source_rows = [{"key": key, "path": rel(path), "exists": path.exists()} for key, path in INPUTS.items()]
    for key, path in BASE_FIGURES.items():
        source_rows.append({"key": f"base_figure_{key}", "path": path, "exists": (REPO_ROOT / path).exists()})
    write_csv(output_dir / "source_inventory.csv", source_rows, ["key", "path", "exists"])


def build_package(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figures").mkdir(exist_ok=True)
    (output_dir / "tables").mkdir(exist_ok=True)

    generated: dict[str, str] = {}
    tables: dict[str, list[dict[str, object]]] = {}

    generated["minor_loss_k"], tables["minor_loss_k_summary"] = build_minor_loss_k_figure(output_dir)
    generated["minor_loss_separation"], tables["minor_loss_separation_summary"] = build_minor_loss_separation_figure(output_dir)
    generated["thermal_replay"], tables["thermal_replay_summary"] = build_thermal_replay_figure(output_dir)
    generated["t13"], tables["t13_summary"] = build_t13_figure(output_dir)

    write_csv(
        output_dir / "tables" / "minor_loss_k_summary.csv",
        tables["minor_loss_k_summary"],
        ["feature", "mean_K_apparent", "mean_K_local"],
    )
    write_csv(
        output_dir / "tables" / "minor_loss_separation_summary.csv",
        tables["minor_loss_separation_summary"],
        ["leg_class", "mean_phi_original", "mean_phi_pipe_only", "mean_minor_fraction_pct"],
    )
    write_csv(
        output_dir / "tables" / "thermal_replay_summary.csv",
        tables["thermal_replay_summary"],
        [
            "path",
            "path_id",
            "mean_abs_Tmean_error_K",
            "mean_abs_loop_delta_T_error_K",
            "thermal_gate_pass",
            "interpretation",
        ],
    )
    write_csv(output_dir / "tables" / "t13_re_sweep_plan.csv", tables["t13_summary"], ["run_id", "q_heater_W", "expected_Re", "status"])

    build_slide_outline(output_dir, generated)
    build_slide6_thermal_analysis_note(output_dir)
    build_missing_figures_note(output_dir, generated)
    build_readme(output_dir, generated)
    write_manifest(output_dir, generated)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task": "AGENT-219",
        "output_dir": rel(output_dir),
        "figures": list(generated.values()),
        "slide_outline": rel(output_dir / "slide_outline_with_speaker_notes.md"),
        "slide6_thermal_analysis": rel(output_dir / "slide6_thermal_replay_analysis.md"),
        "missing_figures_note": rel(output_dir / "missing_and_nice_to_have_figures.md"),
        "source_count": len(INPUTS) + len(BASE_FIGURES),
        "interpretation_boundary": "communication package only; no new CFD extraction or closure fit",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_package(args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
