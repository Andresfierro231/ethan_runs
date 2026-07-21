#!/usr/bin/env python3
"""Build a presentation/thesis chart package from existing postprocessor values.

This tool is intentionally read-only with respect to CFD case trees. It consumes
the July 8 pressure/heat/observation ledgers plus July 7 friction, F5/Ri,
upcomer, and corrected-Salt monitor products, then writes small SVG charts,
summary CSVs, and narrative notes.

Scientific boundary:

- Salt 2/3/4 Jin mainline rows are admitted mainline evidence, still carrying
  the explicit `coarse_no_gci` limitation.
- Corrected Salt perturbation rows are status/gate evidence only. They are not
  closure-fit observations until the formal gate requalifies them.
- Heat charts report wall-flux, imposed-duty accounting, and the enthalpy
  residuals unlocked by span endpoint temperatures. Upcomer/junction residuals
  remain validation diagnostics rather than fit targets.
- F5/Ri is a failed candidate screen on the current 3-point admitted dataset;
  it is not a validated Richardson-number friction law.

The SVG writer uses only the Python standard library so the package can be
rebuilt in minimal HPC shells without matplotlib.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "work_products/2026-07/2026-07-08/2026-07-08_postprocessor_summary_charts"
)

INPUTS = {
    "pressure_ledger": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv",
    "pressure_readme": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/README.md",
    "heat_ledger": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv",
    "heat_readme": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger/README.md",
    "observations": REPO_ROOT / "work_products/2026-07/2026-07-08/2026-07-08_closure_observation_table/closure_observations.csv",
    "friction_mdot": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv",
    "f5_fit": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/f5_fit_summary.csv",
    "f5_mdot": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv",
    "upcomer_dataset": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv",
    "upcomer_fit": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv",
    "corrected_salt_monitor": REPO_ROOT / "work_products/2026-07/2026-07-07/2026-07-07_corrected_salt_live_monitor/live_salt_sanity_monitor.csv",
}


CASE_LABELS = {
    "salt_1": "Salt 1",
    "salt_2": "Salt 2",
    "salt_3": "Salt 3",
    "salt_4": "Salt 4",
}

SOURCE_LABELS = {
    "viscosity_screening_salt_test_1_jin_coarse_mesh": "Salt 1",
    "viscosity_screening_salt_test_2_jin_coarse_mesh": "Salt 2",
    "viscosity_screening_salt_test_3_jin_coarse_mesh": "Salt 3",
    "viscosity_screening_salt_test_4_jin_coarse_mesh": "Salt 4",
}


COLORS = {
    "blue": "#2878B5",
    "orange": "#D97706",
    "green": "#2F855A",
    "red": "#C53030",
    "purple": "#6B46C1",
    "teal": "#0F766E",
    "gray": "#6B7280",
    "light_gray": "#E5E7EB",
    "dark": "#111827",
    "bg": "#FFFFFF",
}


@dataclass(frozen=True)
class Figure:
    filename: str
    title: str
    evidence_class: str
    source_keys: tuple[str, ...]
    scientific_message: str
    caveat: str


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
    if value is None:
        return default
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "na", "none"}:
        return default
    return float(text)


def safe_text(value: object) -> str:
    return html.escape(str(value), quote=True)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def source_label(source_id: str) -> str:
    if source_id in SOURCE_LABELS:
        return SOURCE_LABELS[source_id]
    for key, label in SOURCE_LABELS.items():
        if key in source_id:
            return label
    return CASE_LABELS.get(source_id, source_id)


def short_case_from_monitor(case_key: str) -> str:
    parts = case_key.split("_")
    if len(parts) >= 4 and parts[0].startswith("salt"):
        q = parts[2].replace("lo", "-").replace("hi", "+")
        return f"{parts[0].title()} {q.upper()}"
    return case_key


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COLORS["bg"]}"/>',
        '<style>',
        'text{font-family:Arial,Helvetica,sans-serif;fill:#111827}',
        '.title{font-size:22px;font-weight:700}',
        '.subtitle{font-size:12px;fill:#4B5563}',
        '.axis{stroke:#374151;stroke-width:1}',
        '.grid{stroke:#E5E7EB;stroke-width:1}',
        '.tick{font-size:11px;fill:#4B5563}',
        '.label{font-size:12px;fill:#111827}',
        '.small{font-size:10px;fill:#4B5563}',
        '.legend{font-size:11px;fill:#111827}',
        '</style>',
    ]


def finish_svg(parts: list[str], path: Path) -> None:
    parts.append("</svg>\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts))


def axis_ticks(min_value: float, max_value: float, count: int = 5) -> list[float]:
    if math.isclose(min_value, max_value):
        span = abs(max_value) if max_value else 1.0
        min_value -= span
        max_value += span
    raw_step = (max_value - min_value) / max(count - 1, 1)
    if raw_step == 0:
        return [min_value]
    magnitude = 10 ** math.floor(math.log10(abs(raw_step)))
    residual = raw_step / magnitude
    if residual > 5:
        nice = 10 * magnitude
    elif residual > 2:
        nice = 5 * magnitude
    elif residual > 1:
        nice = 2 * magnitude
    else:
        nice = magnitude
    start = math.floor(min_value / nice) * nice
    end = math.ceil(max_value / nice) * nice
    ticks = []
    value = start
    # Guard against floating point infinite loops.
    for _ in range(50):
        if value > end + nice * 0.5:
            break
        ticks.append(0.0 if abs(value) < 1e-12 else value)
        value += nice
    return ticks


def fmt_tick(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if abs(value) >= 1:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{value:.3f}".rstrip("0").rstrip(".")


def wrap_text(text: str, width_chars: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        proposed = " ".join(current + [word])
        if len(proposed) > width_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def draw_note(parts: list[str], x: int, y: int, text: str, width_chars: int = 110) -> None:
    for idx, line in enumerate(wrap_text(text, width_chars)):
        parts.append(f'<text x="{x}" y="{y + idx * 14}" class="small">{safe_text(line)}</text>')


def draw_grouped_bars(
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
    left, right, top, bottom = 90, 40, 86, 130
    plot_w = width - left - right
    plot_h = height - top - bottom
    vals = [values.get((g, s), 0.0) for g in groups for s in series]
    max_v = max([0.0] + vals)
    min_v = min([0.0] + vals)
    ticks = axis_ticks(min_v, max_v)
    min_tick, max_tick = min(ticks), max(ticks)

    def y(value: float) -> float:
        return top + (max_tick - value) / (max_tick - min_tick) * plot_h

    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe_text(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe_text(subtitle)}</text>')
    parts.append(f'<text x="18" y="{top + plot_h / 2}" class="label" transform="rotate(-90 18 {top + plot_h / 2})">{safe_text(y_label)}</text>')

    for tick in ticks:
        yy = y(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{left + plot_w}" y2="{yy:.2f}" class="grid"/>')
        parts.append(f'<text x="{left - 8}" y="{yy + 4:.2f}" text-anchor="end" class="tick">{safe_text(fmt_tick(tick))}</text>')
    zero_y = y(0.0)
    parts.append(f'<line x1="{left}" y1="{zero_y:.2f}" x2="{left + plot_w}" y2="{zero_y:.2f}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')

    group_w = plot_w / max(len(groups), 1)
    gap = group_w * 0.16
    bar_w = (group_w - 2 * gap) / max(len(series), 1)
    for gi, group in enumerate(groups):
        gx = left + gi * group_w + gap
        for si, name in enumerate(series):
            value = values.get((group, name), 0.0)
            x = gx + si * bar_w + bar_w * 0.08
            y0 = y(0.0)
            yv = y(value)
            h = abs(yv - y0)
            top_y = min(yv, y0)
            parts.append(
                f'<rect x="{x:.2f}" y="{top_y:.2f}" width="{bar_w * 0.84:.2f}" height="{h:.2f}" fill="{colors.get(name, COLORS["gray"])}"/>'
            )
        parts.append(f'<text x="{left + (gi + 0.5) * group_w}" y="{top + plot_h + 28}" text-anchor="middle" class="tick">{safe_text(group)}</text>')

    legend_x = left
    legend_y = height - 76
    for si, name in enumerate(series):
        lx = legend_x + si * 170
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="14" height="14" fill="{colors.get(name, COLORS["gray"])}"/>')
        parts.append(f'<text x="{lx + 20}" y="{legend_y + 12}" class="legend">{safe_text(name)}</text>')
    draw_note(parts, left, height - 36, note, 128)
    finish_svg(parts, path)


def draw_horizontal_grouped_bars(
    path: Path,
    title: str,
    subtitle: str,
    groups: Sequence[str],
    series: Sequence[str],
    values: Mapping[tuple[str, str], float],
    colors: Mapping[str, str],
    x_label: str,
    note: str,
    width: int = 1240,
    height: int = 1040,
) -> None:
    left, right, top, bottom = 230, 58, 90, 118
    plot_w = width - left - right
    plot_h = height - top - bottom
    vals = [values.get((g, s), 0.0) for g in groups for s in series]
    ticks = axis_ticks(0.0, max([0.0] + vals), count=6)
    max_tick = max(ticks)

    def x(value: float) -> float:
        return left + value / max_tick * plot_w if max_tick else left

    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe_text(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe_text(subtitle)}</text>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 36}" text-anchor="middle" class="label">{safe_text(x_label)}</text>')

    for tick in ticks:
        xx = x(tick)
        parts.append(f'<line x1="{xx:.2f}" y1="{top}" x2="{xx:.2f}" y2="{top + plot_h}" class="grid"/>')
        parts.append(f'<text x="{xx:.2f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{safe_text(fmt_tick(tick))}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')

    row_h = plot_h / max(len(groups), 1)
    inner_gap = 3.0
    bar_h = min(9.5, (row_h - 8.0) / max(len(series), 1) - inner_gap)
    for gi, group in enumerate(groups):
        row_top = top + gi * row_h
        cy = row_top + row_h * 0.52
        parts.append(f'<text x="{left - 10}" y="{cy + 4:.2f}" text-anchor="end" class="tick">{safe_text(group)}</text>')
        cluster_h = len(series) * bar_h + (len(series) - 1) * inner_gap
        y_start = cy - cluster_h / 2.0
        for si, name in enumerate(series):
            value = values.get((group, name), 0.0)
            yy = y_start + si * (bar_h + inner_gap)
            parts.append(
                f'<rect x="{left:.2f}" y="{yy:.2f}" width="{max(x(value) - left, 0.0):.2f}" height="{bar_h:.2f}" fill="{colors.get(name, COLORS["gray"])}"/>'
            )

    legend_x = left
    legend_y = height - 82
    step = max(220, int(plot_w / max(len(series), 1)))
    for si, name in enumerate(series):
        lx = legend_x + si * step
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="14" height="14" fill="{colors.get(name, COLORS["gray"])}"/>')
        parts.append(f'<text x="{lx + 20}" y="{legend_y + 12}" class="legend">{safe_text(name)}</text>')
    draw_note(parts, left, height - 56, note, 128)
    finish_svg(parts, path)


def draw_stacked_diverging(
    path: Path,
    title: str,
    subtitle: str,
    groups: Sequence[str],
    series: Sequence[str],
    values: Mapping[tuple[str, str], float],
    colors: Mapping[str, str],
    x_label: str,
    note: str,
    width: int = 1240,
    height: int = 780,
) -> None:
    left, right, top, bottom = 230, 56, 86, 100
    plot_w = width - left - right
    plot_h = height - top - bottom
    pos_max = 0.0
    neg_min = 0.0
    for group in groups:
        pos = sum(max(values.get((group, s), 0.0), 0.0) for s in series)
        neg = sum(min(values.get((group, s), 0.0), 0.0) for s in series)
        pos_max = max(pos_max, pos)
        neg_min = min(neg_min, neg)
    ticks = axis_ticks(neg_min, pos_max)
    min_tick, max_tick = min(ticks), max(ticks)

    def x(value: float) -> float:
        return left + (value - min_tick) / (max_tick - min_tick) * plot_w

    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe_text(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe_text(subtitle)}</text>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 22}" text-anchor="middle" class="label">{safe_text(x_label)}</text>')

    for tick in ticks:
        xx = x(tick)
        parts.append(f'<line x1="{xx:.2f}" y1="{top}" x2="{xx:.2f}" y2="{top + plot_h}" class="grid"/>')
        parts.append(f'<text x="{xx:.2f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{safe_text(fmt_tick(tick))}</text>')
    zero_x = x(0.0)
    parts.append(f'<line x1="{zero_x:.2f}" y1="{top}" x2="{zero_x:.2f}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')

    row_h = plot_h / max(len(groups), 1)
    bar_h = min(26, row_h * 0.55)
    for gi, group in enumerate(groups):
        cy = top + gi * row_h + row_h * 0.52
        parts.append(f'<text x="{left - 10}" y="{cy + 4:.2f}" text-anchor="end" class="tick">{safe_text(group)}</text>')
        pos_cursor = 0.0
        neg_cursor = 0.0
        for name in series:
            value = values.get((group, name), 0.0)
            if value >= 0:
                x0, x1 = x(pos_cursor), x(pos_cursor + value)
                pos_cursor += value
            else:
                x0, x1 = x(neg_cursor + value), x(neg_cursor)
                neg_cursor += value
            parts.append(
                f'<rect x="{min(x0, x1):.2f}" y="{cy - bar_h / 2:.2f}" width="{abs(x1 - x0):.2f}" height="{bar_h:.2f}" fill="{colors.get(name, COLORS["gray"])}"/>'
            )

    legend_x = left
    legend_y = height - 72
    step = max(135, int(plot_w / max(len(series), 1)))
    for si, name in enumerate(series):
        lx = legend_x + si * step
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="14" height="14" fill="{colors.get(name, COLORS["gray"])}"/>')
        parts.append(f'<text x="{lx + 20}" y="{legend_y + 12}" class="legend">{safe_text(name)}</text>')
    draw_note(parts, left, height - 42, note, 128)
    finish_svg(parts, path)


def draw_scatter(
    path: Path,
    title: str,
    subtitle: str,
    points: Sequence[Mapping[str, float | str]],
    x_key: str,
    y_key: str,
    x_label: str,
    y_label: str,
    note: str,
    line_points: Sequence[tuple[float, float]] | None = None,
    width: int = 920,
    height: int = 620,
) -> None:
    left, right, top, bottom = 86, 42, 84, 92
    plot_w = width - left - right
    plot_h = height - top - bottom
    xs = [float(p[x_key]) for p in points]
    ys = [float(p[y_key]) for p in points]
    if line_points:
        xs += [p[0] for p in line_points]
        ys += [p[1] for p in line_points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xpad = (xmax - xmin) * 0.12 or 1.0
    ypad = (ymax - ymin) * 0.18 or 0.1
    xticks = axis_ticks(xmin - xpad, xmax + xpad)
    yticks = axis_ticks(ymin - ypad, ymax + ypad)
    xmin, xmax = min(xticks), max(xticks)
    ymin, ymax = min(yticks), max(yticks)

    def x(value: float) -> float:
        return left + (value - xmin) / (xmax - xmin) * plot_w

    def y(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">{safe_text(title)}</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">{safe_text(subtitle)}</text>')
    for tick in xticks:
        xx = x(tick)
        parts.append(f'<line x1="{xx:.2f}" y1="{top}" x2="{xx:.2f}" y2="{top + plot_h}" class="grid"/>')
        parts.append(f'<text x="{xx:.2f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{safe_text(fmt_tick(tick))}</text>')
    for tick in yticks:
        yy = y(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{left + plot_w}" y2="{yy:.2f}" class="grid"/>')
        parts.append(f'<text x="{left - 8}" y="{yy + 4:.2f}" text-anchor="end" class="tick">{safe_text(fmt_tick(tick))}</text>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 38}" text-anchor="middle" class="label">{safe_text(x_label)}</text>')
    parts.append(f'<text x="18" y="{top + plot_h / 2}" class="label" transform="rotate(-90 18 {top + plot_h / 2})">{safe_text(y_label)}</text>')
    if line_points:
        poly = " ".join(f"{x(px):.2f},{y(py):.2f}" for px, py in line_points)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{COLORS["orange"]}" stroke-width="2.4"/>')
    for p in points:
        xx, yy = x(float(p[x_key])), y(float(p[y_key]))
        label = str(p.get("label", ""))
        parts.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="6" fill="{COLORS["blue"]}" stroke="#FFFFFF" stroke-width="1.5"/>')
        parts.append(f'<text x="{xx + 8:.2f}" y="{yy - 8:.2f}" class="small">{safe_text(label)}</text>')
    draw_note(parts, left, height - 22, note, 112)
    finish_svg(parts, path)


def draw_status_chart(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    width: int = 1240,
    height: int = 860,
) -> None:
    left, right, top, bottom = 250, 40, 90, 108
    plot_w = width - left - right
    plot_h = height - top - bottom
    sorted_rows = sorted(rows, key=lambda r: (str(r["recommendation"]), str(r["case_key"])))
    max_value = max([float(r["advance_fraction_of_target"]) for r in sorted_rows] + [1.0])
    ticks = axis_ticks(0.0, max(1.0, max_value), count=6)
    max_tick = max(ticks)

    def x(value: float) -> float:
        return left + value / max_tick * plot_w

    color_by_recommendation = {
        "hold_running_wait_for_formal_gate": COLORS["blue"],
        "hold_for_coordinator_review": COLORS["orange"],
        "investigate": COLORS["red"],
        "admit_after_gate": COLORS["green"],
    }
    parts = svg_header(width, height)
    parts.append(f'<text x="{left}" y="34" class="title">Corrected Salt Status/Gate Monitor</text>')
    parts.append(f'<text x="{left}" y="56" class="subtitle">Status-only evidence from live monitor; not closure-fit data</text>')
    for tick in ticks:
        xx = x(tick)
        parts.append(f'<line x1="{xx:.2f}" y1="{top}" x2="{xx:.2f}" y2="{top + plot_h}" class="grid"/>')
        parts.append(f'<text x="{xx:.2f}" y="{top + plot_h + 22}" text-anchor="middle" class="tick">{safe_text(fmt_tick(tick))}</text>')
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" class="axis"/>')
    row_h = plot_h / max(len(sorted_rows), 1)
    for idx, row in enumerate(sorted_rows):
        cy = top + idx * row_h + row_h * 0.54
        value = float(row["advance_fraction_of_target"])
        rec = str(row["recommendation"])
        color = color_by_recommendation.get(rec, COLORS["gray"])
        parts.append(f'<text x="{left - 8}" y="{cy + 4:.2f}" text-anchor="end" class="tick">{safe_text(str(row["label"]))}</text>')
        parts.append(f'<rect x="{left}" y="{cy - row_h * 0.26:.2f}" width="{max(x(value) - left, 1):.2f}" height="{row_h * 0.52:.2f}" fill="{color}"/>')
        flag = "special scrutiny" if str(row["needs_special_gate_scrutiny"]).lower() == "true" else rec.replace("_", " ")
        parts.append(f'<text x="{x(value) + 5:.2f}" y="{cy + 4:.2f}" class="small">{safe_text(flag)}</text>')
    parts.append(f'<text x="{left + plot_w / 2}" y="{height - 42}" text-anchor="middle" class="label">Advance fraction of target extension</text>')
    draw_note(
        parts,
        left,
        height - 18,
        "Rows are live/status diagnostics. Formal operating-point requalification is required before any corrected Salt row enters closure fitting.",
        122,
    )
    finish_svg(parts, path)


def summarize_pressure(rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        case = source_label(row["source_id"])
        length_m = fnum(row["L_m"])
        flow_projected_buoyancy_pa = fnum(row["gh_drho_dxi_pa_m"]) * length_m
        out.append(
            {
                "case": case,
                "source_id": row["source_id"],
                "span": row["span"],
                "gross_prgh_pa": fnum(row["gross_static_dp_pa"]),
                "distributed_friction_pa": fnum(row["distributed_friction_pa"]),
                "density_gradient_buoyancy_pa": flow_projected_buoyancy_pa,
                "station_order_buoyancy_pa": fnum(row["buoyancy_contribution_pa"]),
                "density_gradient_buoyancy_basis": "flow_projected_gh_drho_dxi_times_L",
                "development_loss_pa": fnum(row["development_loss_pa"]),
                "minor_loss_upper_bound_pa": fnum(row["minor_loss_pa"]),
                "residual_pa": fnum(row["residual_pa"]),
                "fit_use_status": row.get("fit_use_status", ""),
                "fit_eligible": row.get("fit_eligible", ""),
                "quality_flags": row.get("quality_flags", ""),
                "admission_note": row.get("admission_note", ""),
            }
        )
    return out


def summarize_heat(rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    statuses: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        case = row.get("case_id") or source_label(row["source_id"])
        group = row["patch_group"]
        totals[(case, group)] += fnum(row.get("heat_to_fluid_W", row.get("wallHeatFlux_integral_W")))
        statuses[(case, group)].add(row.get("enthalpy_change_status", ""))
    out = []
    for (case, group), value in sorted(totals.items()):
        out.append(
            {
                "case": CASE_LABELS.get(case, case),
                "patch_group": group,
                "heat_to_fluid_W": value,
                "enthalpy_change_status": ";".join(sorted(s for s in statuses[(case, group)] if s)),
            }
        )
    return out


def summarize_heat_residuals(rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    by_segment: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        span = str(row.get("span", ""))
        if span == "junction":
            continue
        case = row.get("case_id") or source_label(row["source_id"])
        key = (CASE_LABELS.get(case, case), span)
        if key in by_segment:
            continue
        by_segment[key] = {
            "case": key[0],
            "span": span,
            "segment_wallHeatFlux_sum_W": fnum(row.get("segment_wallHeatFlux_sum_W")),
            "enthalpy_change_W": fnum(row.get("enthalpy_change_W")),
            "wallHeatFlux_vs_enthalpy_residual_W": fnum(row.get("wallHeatFlux_vs_enthalpy_residual_W")),
            "residual_fraction": row.get("residual_fraction", ""),
            "enthalpy_change_status": row.get("enthalpy_change_status", ""),
            "residual_assignment": row.get("residual_assignment", ""),
        }
    return [by_segment[key] for key in sorted(by_segment)]


def summarize_observations(rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str, str, str]] = Counter()
    for row in rows:
        counts[
            (
                row.get("observable_family", ""),
                row.get("fit_use_status", ""),
                row.get("validation_use_status", ""),
                row.get("mesh_status", ""),
            )
        ] += 1
    return [
        {
            "observable_family": key[0],
            "fit_use_status": key[1],
            "validation_use_status": key[2],
            "mesh_status": key[3],
            "row_count": count,
        }
        for key, count in sorted(counts.items())
    ]


def summarize_corrected_status(rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    out = []
    for row in rows:
        out.append(
            {
                "case_key": row["case_key"],
                "label": short_case_from_monitor(row["case_key"]),
                "job_id": row["job_id"],
                "job_state": row["job_state"],
                "q_ratio": fnum(row["q_ratio"]),
                "advance_since_restart_s": fnum(row["advance_since_restart_s"]),
                "advance_fraction_of_target": fnum(row["advance_fraction_of_target"]),
                "mdot_moved_pct": fnum(row["mdot_moved_pct"], default=float("nan")),
                "expected_move_pct": fnum(row["expected_move_pct"], default=float("nan")),
                "moved_enough": row["moved_enough"],
                "mdot_direction_ok": row["mdot_direction_ok"],
                "needs_special_gate_scrutiny": row["needs_special_gate_scrutiny"],
                "recommendation": row["recommendation"],
                "closure_fit_admissible_without_coordinator_review": row["closure_fit_admissible_without_coordinator_review"],
                "scrutiny_reason": row.get("scrutiny_reason", ""),
            }
        )
    return out


def build_package(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(exist_ok=True)
    tables_dir.mkdir(exist_ok=True)

    pressure = read_csv(INPUTS["pressure_ledger"])
    heat = read_csv(INPUTS["heat_ledger"])
    observations = read_csv(INPUTS["observations"])
    friction = read_csv(INPUTS["friction_mdot"])
    f5_fit = read_csv(INPUTS["f5_fit"])
    f5_mdot = read_csv(INPUTS["f5_mdot"])
    upcomer = read_csv(INPUTS["upcomer_dataset"])
    upcomer_fit = read_csv(INPUTS["upcomer_fit"])
    corrected = read_csv(INPUTS["corrected_salt_monitor"])

    pressure_summary = summarize_pressure(pressure)
    heat_summary = summarize_heat(heat)
    heat_residual_summary = summarize_heat_residuals(heat)
    observation_summary = summarize_observations(observations)
    corrected_summary = summarize_corrected_status(corrected)

    write_csv(
        tables_dir / "pressure_terms_summary.csv",
        pressure_summary,
        [
            "case",
            "source_id",
            "span",
            "gross_prgh_pa",
            "distributed_friction_pa",
            "density_gradient_buoyancy_pa",
            "station_order_buoyancy_pa",
            "density_gradient_buoyancy_basis",
            "development_loss_pa",
            "minor_loss_upper_bound_pa",
            "residual_pa",
            "fit_use_status",
            "fit_eligible",
            "quality_flags",
            "admission_note",
        ],
    )
    write_csv(tables_dir / "heat_terms_summary.csv", heat_summary, ["case", "patch_group", "heat_to_fluid_W", "enthalpy_change_status"])
    write_csv(
        tables_dir / "heat_enthalpy_residual_summary.csv",
        heat_residual_summary,
        [
            "case",
            "span",
            "segment_wallHeatFlux_sum_W",
            "enthalpy_change_W",
            "wallHeatFlux_vs_enthalpy_residual_W",
            "residual_fraction",
            "enthalpy_change_status",
            "residual_assignment",
        ],
    )
    write_csv(
        tables_dir / "observation_table_summary.csv",
        observation_summary,
        ["observable_family", "fit_use_status", "validation_use_status", "mesh_status", "row_count"],
    )
    write_csv(
        tables_dir / "corrected_salt_status_summary.csv",
        corrected_summary,
        [
            "case_key",
            "label",
            "job_id",
            "job_state",
            "q_ratio",
            "advance_since_restart_s",
            "advance_fraction_of_target",
            "mdot_moved_pct",
            "expected_move_pct",
            "moved_enough",
            "mdot_direction_ok",
            "needs_special_gate_scrutiny",
            "recommendation",
            "closure_fit_admissible_without_coordinator_review",
            "scrutiny_reason",
        ],
    )
    write_csv(
        tables_dir / "friction_mdot_summary.csv",
        friction,
        [
            "source_id",
            "salt_label",
            "insulation_in",
            "friction_form",
            "mdot_predicted_kg_s",
            "mdot_cfd_kg_s",
            "mdot_err_pct",
            "loop_mean_T_K",
            "dp_total_loop_pa",
            "dp_heater_pa",
            "dp_cooler_pa",
            "dp_downcomer_pa",
            "dp_upcomer_pa",
        ],
    )
    write_csv(
        tables_dir / "f5_fit_screen_summary.csv",
        f5_fit,
        ["leg_class", "n_points", "c_fitted", "R2", "RMSE_phi", "phi_mean", "c_active", "fit_quality", "note"],
    )
    write_csv(
        tables_dir / "upcomer_regime_summary.csv",
        upcomer,
        [
            "label",
            "source_id",
            "Re_upcomer",
            "Ri_median",
            "Ra_median",
            "Pr_median",
            "backflow_fraction",
            "recirculation_intensity",
            "Nu_upcomer",
            "T_bulk_K",
        ],
    )

    figures: list[Figure] = []

    # Main slide-safe pressure chart: keep signed p_rgh density-gradient terms out
    # of the primary mechanical-loss view.
    span_labels = {
        "lower_leg": "lower",
        "right_leg": "right/down",
        "left_lower_leg": "left lower",
        "test_section_span": "test section",
        "left_upper_leg": "left upper",
        "upper_leg": "upper",
    }
    mechanical_groups = [f"{row['case']} {span_labels.get(str(row['span']), str(row['span']))}" for row in pressure_summary]
    mechanical_series = [
        "de-buoyed friction target",
        "development/reset estimate",
        "minor loss upper bound",
    ]
    mechanical_values = {}
    for row in pressure_summary:
        group = f"{row['case']} {span_labels.get(str(row['span']), str(row['span']))}"
        mechanical_values[(group, "de-buoyed friction target")] = float(row["distributed_friction_pa"])
        mechanical_values[(group, "development/reset estimate")] = float(row["development_loss_pa"])
        mechanical_values[(group, "minor loss upper bound")] = float(row["minor_loss_upper_bound_pa"])
    draw_horizontal_grouped_bars(
        figures_dir / "mechanical_pressure_terms_by_span.svg",
        "Mechanical Pressure Terms By Span",
        "Signed p_rgh density-gradient terms removed; compare loss-scale terms only",
        mechanical_groups,
        mechanical_series,
        mechanical_values,
        {
            "de-buoyed friction target": COLORS["blue"],
            "development/reset estimate": COLORS["orange"],
            "minor loss upper bound": COLORS["purple"],
        },
        "Pa over span",
        "Source: July 8 pressure ledger. Development and minor-loss bars are diagnostic estimates, not additive corrections on top of the CFD de-buoyed friction target.",
        width=1240,
        height=1040,
    )
    figures.append(
        Figure(
            "figures/mechanical_pressure_terms_by_span.svg",
            "Mechanical Pressure Terms By Span",
            "admitted_mainline_with_caveats",
            ("pressure_ledger",),
            "Mechanical pressure terms are ordinary-sized across the main spans once signed p_rgh density-gradient source terms are separated from irreversible loss.",
            "Development/reset and minor-loss upper-bound bars are diagnostic estimates and should not be added to the de-buoyed friction target.",
        )
    )

    # Pressure decomposition: one row per case/span, diverging because buoyancy can be signed.
    pressure_groups = [f"{row['case']} {row['span']}" for row in pressure_summary]
    pressure_series = [
        "distributed friction",
        "density-gradient buoyancy",
        "development/reset",
        "minor loss upper bound",
        "residual",
    ]
    pressure_values = {}
    for row in pressure_summary:
        group = f"{row['case']} {row['span']}"
        pressure_values[(group, "distributed friction")] = float(row["distributed_friction_pa"])
        pressure_values[(group, "density-gradient buoyancy")] = float(row["density_gradient_buoyancy_pa"])
        pressure_values[(group, "development/reset")] = float(row["development_loss_pa"])
        pressure_values[(group, "minor loss upper bound")] = float(row["minor_loss_upper_bound_pa"])
        pressure_values[(group, "residual")] = float(row["residual_pa"])
    draw_stacked_diverging(
        figures_dir / "pressure_decomposition_by_span.svg",
        "Pressure-Term Decomposition By Span",
        "Salt 2/3/4 Jin mainline; losses positive, density-gradient term is flow-projected",
        pressure_groups,
        pressure_series,
        pressure_values,
        {
            "distributed friction": COLORS["blue"],
            "density-gradient buoyancy": COLORS["green"],
            "development/reset": COLORS["orange"],
            "minor loss upper bound": COLORS["purple"],
            "residual": COLORS["gray"],
        },
        "Pa over span",
        "Source: July 8 pressure ledger. Minor-loss values are upper bounds; recirculation spans are validation diagnostics, not single-stream friction fits.",
        width=1360,
        height=940,
    )
    figures.append(
        Figure(
            "figures/pressure_decomposition_by_span.svg",
            "Pressure-Term Decomposition By Span",
            "admitted_mainline_with_caveats",
            ("pressure_ledger",),
            "Pressure evidence is now decomposed into mechanical loss, buoyancy, development/reset, feature-loss upper bounds, and residual rather than raw p_rgh slopes.",
            "Coarse mesh only; recirculation spans and minor-loss upper bounds must not be promoted to universal friction coefficients.",
        )
    )

    # Heat source/sink chart.
    heat_groups = sorted({row["case"] for row in heat_summary}, key=lambda x: (x[-1], x))
    heat_series = ["heater", "cooler", "ambient_wall", "test_section", "junction_other"]
    heat_values = {(row["case"], row["patch_group"]): float(row["heat_to_fluid_W"]) for row in heat_summary}
    draw_stacked_diverging(
        figures_dir / "heat_source_sink_by_patch_group.svg",
        "Patchwise Heat Source/Sink Accounting",
        "Positive heat_to_fluid_W is heat into fluid; negative is heat removed",
        heat_groups,
        heat_series,
        heat_values,
        {
            "heater": COLORS["red"],
            "cooler": COLORS["blue"],
            "ambient_wall": COLORS["teal"],
            "test_section": COLORS["orange"],
            "junction_other": COLORS["gray"],
        },
        "W",
        "Source: July 8 patchwise heat ledger. Wall-flux accounting is paired with separate enthalpy-residual diagnostics.",
        width=980,
        height=620,
    )
    figures.append(
        Figure(
            "figures/heat_source_sink_by_patch_group.svg",
            "Patchwise Heat Source/Sink Accounting",
            "admitted_mainline_validation_diagnostic",
            ("heat_ledger",),
            "The loop heat balance is near closed at the wall-flux level, but the test section is a net sink and passive/junction losses are first-order thermal-state evidence.",
            "Patch-group wall flux is not the same quantity as the segment enthalpy residual; use the residual chart for segment closure.",
        )
    )

    residual_groups = sorted({str(row["case"]) for row in heat_residual_summary}, key=lambda x: (x[-1], x))
    residual_series = ["lower_leg", "cooling_branch", "downcomer", "upcomer"]
    residual_values = {
        (str(row["case"]), str(row["span"])): float(row["wallHeatFlux_vs_enthalpy_residual_W"])
        for row in heat_residual_summary
    }
    draw_grouped_bars(
        figures_dir / "heat_enthalpy_residual_by_segment.svg",
        "Heat Ledger Enthalpy Residual By Segment",
        "Residual = segment wallHeatFlux sum - mdot cp DeltaT",
        residual_groups,
        residual_series,
        residual_values,
        {
            "lower_leg": COLORS["red"],
            "cooling_branch": COLORS["blue"],
            "downcomer": COLORS["teal"],
            "upcomer": COLORS["orange"],
        },
        "W",
        "Source: patchwise heat ledger joined to span endpoint temperatures. Upcomer residuals are diagnostic-only because endpoint recirculation is high; junctions are not enthalpy-bracketed.",
        width=980,
        height=620,
    )
    figures.append(
        Figure(
            "figures/heat_enthalpy_residual_by_segment.svg",
            "Heat Ledger Enthalpy Residual By Segment",
            "admitted_mainline_validation_diagnostic",
            ("heat_ledger",),
            "Span endpoint temperatures now quantify lower-leg, cooling-branch, downcomer, and upcomer heat residuals separately from patchwise wall-flux accounting.",
            "Upcomer residuals are recirculation diagnostics, cooler spans only partially bracket the cooler, and junction rows remain unbracketed.",
        )
    )

    # Friction mdot errors.
    friction_groups = ["Salt 2", "Salt 3", "Salt 4"]
    friction_series = ["F1", "F3_hagenbach", "F3_shah_apparent", "F4_leg_class"]
    friction_values = {}
    for row in friction:
        friction_values[(CASE_LABELS.get(row["salt_label"], row["salt_label"]), row["friction_form"])] = fnum(row["mdot_err_pct"])
    draw_grouped_bars(
        figures_dir / "friction_form_mdot_error.svg",
        "1D mdot Error By Friction Form",
        "Matched-insulation diagnostic from AGENT-195; mdot is not the only score while thermal state is mismatched",
        friction_groups,
        friction_series,
        friction_values,
        {
            "F1": COLORS["gray"],
            "F3_hagenbach": COLORS["teal"],
            "F3_shah_apparent": COLORS["blue"],
            "F4_leg_class": COLORS["orange"],
        },
        "mdot error (%)",
        "Source: AGENT-195 mdot comparison. F3 Shah apparent is the best current mdot screen; F4 leg-class over-stiffens the loop in this setup.",
    )
    figures.append(
        Figure(
            "figures/friction_form_mdot_error.svg",
            "1D mdot Error By Friction Form",
            "diagnostic_model_comparison",
            ("friction_mdot",),
            "Developing-flow friction forms reduce the F1 mass-flow overprediction, but hydraulic success cannot be separated from thermal-state matching yet.",
            "Matched insulation values are diagnostic and should not be confused with a fully audited physical scenario contract.",
        )
    )

    # Per-leg pressure drops by form/case.
    leg_series = ["heater", "cooler", "downcomer", "upcomer"]
    leg_groups = [f"{CASE_LABELS.get(row['salt_label'], row['salt_label'])} {row['friction_form']}" for row in friction]
    leg_values = {}
    for row in friction:
        group = f"{CASE_LABELS.get(row['salt_label'], row['salt_label'])} {row['friction_form']}"
        leg_values[(group, "heater")] = fnum(row["dp_heater_pa"])
        leg_values[(group, "cooler")] = fnum(row["dp_cooler_pa"])
        leg_values[(group, "downcomer")] = fnum(row["dp_downcomer_pa"])
        leg_values[(group, "upcomer")] = fnum(row["dp_upcomer_pa"])
    draw_stacked_diverging(
        figures_dir / "friction_per_leg_pressure_drop.svg",
        "Per-Leg Pressure Drop In 1D Friction Screens",
        "Stacked distributed pressure-drop contributions from the AGENT-195 1D runs",
        leg_groups,
        leg_series,
        leg_values,
        {"heater": COLORS["red"], "cooler": COLORS["blue"], "downcomer": COLORS["green"], "upcomer": COLORS["purple"]},
        "Pa",
        "Source: AGENT-195. F4 redistributes and increases loop resistance; upcomer interpretation remains complicated by recirculation in the CFD evidence.",
        width=1280,
        height=840,
    )
    figures.append(
        Figure(
            "figures/friction_per_leg_pressure_drop.svg",
            "Per-Leg Pressure Drop In 1D Friction Screens",
            "diagnostic_model_comparison",
            ("friction_mdot",),
            "The per-leg comparison shows why F4_leg_class suppresses mdot: it adds large heater/downcomer resistance relative to F3 forms.",
            "These are 1D solver terms, not direct CFD pressure-ledger terms.",
        )
    )

    # F5 screen: fit quality by leg class, using R2 and active c.
    f5_groups = [row["leg_class"] for row in f5_fit]
    f5_series = ["c_fitted", "c_active"]
    f5_values = {}
    for row in f5_fit:
        f5_values[(row["leg_class"], "c_fitted")] = fnum(row["c_fitted"])
        f5_values[(row["leg_class"], "c_active")] = fnum(row["c_active"])
    draw_grouped_bars(
        figures_dir / "f5_ri_screen_coefficients.svg",
        "F5 Ri-Corrected Friction Candidate Screen",
        "Fitted coefficients were deactivated because the 3-point forced-intercept fit was poorer than a mean model",
        f5_groups,
        f5_series,
        f5_values,
        {"c_fitted": COLORS["orange"], "c_active": COLORS["blue"]},
        "coefficient c in phi = 1 + c Ri_streamwise",
        "Source: AGENT-200 F5 screen. Upcomer excluded; active coefficients are zero, so F5 currently equals F3 Shah apparent.",
        width=920,
        height=600,
    )
    figures.append(
        Figure(
            "figures/f5_ri_screen_coefficients.svg",
            "F5 Ri-Corrected Friction Candidate Screen",
            "failed_candidate_screen",
            ("f5_fit", "f5_mdot"),
            "The current admitted dataset does not support a 1-parameter Ri multiplier; F5 is a scaffold for future gated perturbation data, not a result.",
            "Three points per leg class and no independent validation; corrected Salt gate must finish before refitting.",
        )
    )

    # Upcomer regime scatter.
    fit = upcomer_fit[0]
    a = fnum(fit["a"])
    b = fnum(fit["b"])
    re_min = fnum(fit["Re_min_calibration"])
    re_max = fnum(fit["Re_max_calibration"])
    line = [(re_min, a + b / re_min), (re_max, a + b / re_max)]
    up_points = [
        {
            "label": row["label"].replace("_jin", "").replace("salt_", "Salt "),
            "Re": fnum(row["Re_upcomer"]),
            "backflow": fnum(row["backflow_fraction"]) * 100.0,
        }
        for row in upcomer
    ]
    line_pct = [(x, y * 100.0) for x, y in line]
    draw_scatter(
        figures_dir / "upcomer_backflow_vs_re.svg",
        "Upcomer Backflow Fraction Versus Re",
        "Three admitted Salt Jin points; onset estimates remain extrapolated",
        up_points,
        "Re",
        "backflow",
        "Re_upcomer",
        "Backflow fraction (%)",
        "Source: AGENT-196. The lower-upcomer trend decreases with Re, but persistent recirculation keeps the upcomer out of ordinary single-stream pipe-friction fitting.",
        line_points=line_pct,
    )
    figures.append(
        Figure(
            "figures/upcomer_backflow_vs_re.svg",
            "Upcomer Backflow Fraction Versus Re",
            "admitted_mainline_regime_diagnostic",
            ("upcomer_dataset", "upcomer_fit"),
            "Backflow weakens from Salt 2 to Salt 4 as Re increases, supporting a separate upcomer regime treatment.",
            "Only three coupled operating points; onset predictions are extrapolated and need corrected-Q or new CFD design points.",
        )
    )

    # Corrected Salt status chart.
    draw_status_chart(figures_dir / "corrected_salt_gate_status.svg", corrected_summary)
    figures.append(
        Figure(
            "figures/corrected_salt_gate_status.svg",
            "Corrected Salt Gate Status",
            "status_only_not_closure_evidence",
            ("corrected_salt_monitor",),
            "Some corrected Salt rows show expected mdot movement, but formal gate completion and special-scrutiny disposition are still required.",
            "Do not use this chart as closure-fit evidence.",
        )
    )

    figure_rows = [
        {
            "figure": fig.filename,
            "title": fig.title,
            "evidence_class": fig.evidence_class,
            "source_keys": ";".join(fig.source_keys),
            "scientific_message": fig.scientific_message,
            "caveat": fig.caveat,
        }
        for fig in figures
    ]
    write_csv(
        output_dir / "figure_manifest.csv",
        figure_rows,
        ["figure", "title", "evidence_class", "source_keys", "scientific_message", "caveat"],
    )

    source_rows = []
    for key, path in INPUTS.items():
        source_rows.append(
            {
                "source_key": key,
                "path": rel(path),
                "exists": path.exists(),
                "role_in_package": source_role(key),
            }
        )
    write_csv(output_dir / "source_inventory.csv", source_rows, ["source_key", "path", "exists", "role_in_package"])

    observed, inferred, blockers, next_steps = build_interpretation(pressure_summary, heat_summary, friction, f5_fit, upcomer, corrected_summary)
    write_readme(output_dir, figures, observed, inferred, blockers, next_steps)
    write_presentation_story(output_dir, observed, inferred, blockers, next_steps)
    write_thesis_story(output_dir, observed, inferred, blockers, next_steps)
    write_next_steps(output_dir, observed, inferred, blockers, next_steps)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task": "TODO-POSTPROCESSOR-CHARTS",
        "output_dir": rel(output_dir),
        "figures": [fig.filename for fig in figures],
        "source_inventory": "source_inventory.csv",
        "figure_manifest": "figure_manifest.csv",
        "tables": sorted(p.name for p in tables_dir.glob("*.csv")),
        "observed_facts": observed,
        "inferred_interpretation": inferred,
        "blockers": blockers,
        "recommended_next_steps": next_steps,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def source_role(key: str) -> str:
    roles = {
        "pressure_ledger": "Primary pressure decomposition table for admitted Salt 2/3/4 spans.",
        "pressure_readme": "Pressure equations, sign convention, and caveats.",
        "heat_ledger": "Primary patchwise heat source/sink table for admitted Salt 2/3/4 rows.",
        "heat_readme": "Heat sign convention, wall-flux/enthalpy boundary, and caveats.",
        "observations": "Canonical observation/admission schema summary.",
        "friction_mdot": "AGENT-195 1D friction-form mdot and per-leg pressure-drop comparison.",
        "f5_fit": "AGENT-200 Ri-corrected F5 candidate-screen coefficients.",
        "f5_mdot": "AGENT-200 confirmation that F5 currently equals F3 Shah apparent.",
        "upcomer_dataset": "AGENT-196 upcomer recirculation/regime dataset.",
        "upcomer_fit": "AGENT-196 three-point backflow trend and onset caveats.",
        "corrected_salt_monitor": "AGENT-181 live corrected-Salt status monitor; status-only, not closure evidence.",
    }
    return roles.get(key, "")


def build_interpretation(
    pressure: Sequence[Mapping[str, object]],
    heat: Sequence[Mapping[str, object]],
    friction: Sequence[Mapping[str, str]],
    f5_fit: Sequence[Mapping[str, str]],
    upcomer: Sequence[Mapping[str, str]],
    corrected: Sequence[Mapping[str, object]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    f3_errors = [fnum(r["mdot_err_pct"]) for r in friction if r["friction_form"] == "F3_shah_apparent"]
    f1_errors = [fnum(r["mdot_err_pct"]) for r in friction if r["friction_form"] == "F1"]
    f4_errors = [fnum(r["mdot_err_pct"]) for r in friction if r["friction_form"] == "F4_leg_class"]
    heat_by_group: dict[str, float] = defaultdict(float)
    for row in heat:
        heat_by_group[str(row["patch_group"])] += float(row["heat_to_fluid_W"])
    heat_residuals = [
        fnum(row.get("wallHeatFlux_vs_enthalpy_residual_W"), default=float("nan"))
        for row in read_csv(INPUTS["heat_ledger"])
        if row.get("span") != "junction" and row.get("wallHeatFlux_vs_enthalpy_residual_W")
    ]
    finite_heat_residuals = [value for value in heat_residuals if not math.isnan(value)]
    special = sum(1 for row in corrected if str(row["needs_special_gate_scrutiny"]).lower() == "true")
    investigate = sum(1 for row in corrected if str(row["recommendation"]) == "investigate")
    up_backflows = [fnum(row["backflow_fraction"]) for row in upcomer]
    f5_bad = [row for row in f5_fit if row.get("fit_quality") in {"poor_set_to_mean", "excluded"}]

    observed = [
        f"July 8 pressure ledger contributes {len(pressure)} admitted Salt 2/3/4 span rows with explicit buoyancy, distributed loss, development/reset, minor-loss upper-bound, and residual terms.",
        f"July 8 patchwise heat ledger contributes {len(heat)} patch-group rows; aggregate heater input, cooler/passive removals, and segment enthalpy residuals are available as validation diagnostics.",
        f"F1 mdot errors are positive across Salt 2/3/4 ({min(f1_errors):.1f}% to {max(f1_errors):.1f}%), while F3 Shah apparent narrows the range ({min(f3_errors):.1f}% to {max(f3_errors):.1f}%).",
        f"F4 leg-class mdot errors are negative across Salt 2/3/4 ({min(f4_errors):.1f}% to {max(f4_errors):.1f}%), consistent with over-stiffening in the current 1D run.",
        f"F5/Ri screen has {len(f5_bad)} leg classes either deactivated or excluded; active F5 coefficients are zero in the current package.",
        f"Upcomer backflow fraction decreases across the admitted Salt series from {max(up_backflows) * 100:.1f}% to {min(up_backflows) * 100:.1f}% as Re increases.",
        f"Corrected Salt live monitor includes {len(corrected)} status rows; {special} need special gate scrutiny and {investigate} are marked investigate.",
    ]
    if finite_heat_residuals:
        observed.insert(
            2,
            f"Heat enthalpy residuals are populated for non-junction spans; current absolute residuals range from {min(abs(v) for v in finite_heat_residuals):.1f} W to {max(abs(v) for v in finite_heat_residuals):.1f} W.",
        )
    inferred = [
        "The strongest presentable story is decomposition and admission discipline: the workflow now separates what CFD directly shows from terms that can become 1D closures.",
        "Developing-flow friction is already a better practical baseline than fully developed F1 for the current Salt 2/3/4 mdot screen.",
        "The remaining mdot gap cannot be assigned to friction alone because the heat ledger now shows first-order segment enthalpy residuals and a net-sink test-section wall flux.",
        "The upcomer should be treated as a regime problem, not as an ordinary single-stream pipe-friction span, until recirculation onset is better bounded.",
        "Corrected Salt perturbations are promising for expanding the operating envelope but remain outside closure fitting until formal gate requalification.",
    ]
    blockers = [
        "No mesh/GCI uncertainty is attached to the presented QOIs yet; all admitted rows remain coarse_no_gci.",
        "Corrected Salt perturbation rows are status-only until the gate completes and special-scrutiny rows are dispositioned.",
        "Thermal enthalpy residuals are available for non-junction spans, but upcomer rows are recirculation diagnostics and cooler endpoints only partially bracket the cooler.",
        "F5/Ri cannot be promoted without more admitted operating points spanning a wider Ri/Re domain.",
    ]
    next_steps = [
        "Use this chart package for tomorrow's high-level evidence story: pressure decomposition, heat accounting, friction screens, upcomer regime, and gate status.",
        "Use the enthalpy-residual chart to separate thermal-state mismatch from pressure and mdot model-form scores.",
        "Build the model-form bakeoff from the closure observation table, scoring pressure distribution, mdot, and thermal-state mismatch separately.",
        "When corrected Salt gate results land, refresh the status chart first, then decide which rows may enter perturbation trend and F5/Ri refit packages.",
        "Pursue mesh/GCI intake before making paper-grade coefficient claims.",
    ]
    return observed, inferred, blockers, next_steps


def write_readme(output_dir: Path, figures: Sequence[Figure], observed: Sequence[str], inferred: Sequence[str], blockers: Sequence[str], next_steps: Sequence[str]) -> None:
    figure_lines = "\n".join(
        f"- `{fig.filename}`: {fig.scientific_message} Caveat: {fig.caveat}" for fig in figures
    )
    source_lines = "\n".join(f"- `{key}`: `{rel(path)}` — {source_role(key)}" for key, path in INPUTS.items())
    text = f"""# Postprocessor Summary Charts

Generated: `{datetime.now().isoformat(timespec="seconds")}`
Task: `TODO-POSTPROCESSOR-CHARTS`

## Scope

This package creates tomorrow-facing charts from existing postprocessor evidence
without new OpenFOAM-heavy extraction. It is a scientific communication package,
not a new closure fit.

## Evidence Classes

- Salt 2/3/4 Jin mainline pressure, heat, friction, and upcomer rows are
  admitted mainline evidence, but still carry the `coarse_no_gci` limitation.
- Corrected Salt Q rows are live/status evidence only and remain excluded from
  closure fitting until formal gate requalification.
- F5/Ri is a failed candidate screen on the current admitted dataset; it is
  not a validated Richardson-number law.

## Figures

{figure_lines}

## Source Inventory

{source_lines}

## Observed Facts

{bullet_lines(observed)}

## Inferred Interpretation

{bullet_lines(inferred)}

## Blockers / Work In Progress

{bullet_lines(blockers)}

## Recommended Next Actions

{bullet_lines(next_steps)}

## Reproduce

```bash
cd {REPO_ROOT}
python tools/analyze/build_postprocessor_summary_charts.py
python -m pytest tools/analyze/test_postprocessor_summary_charts.py -q
```
"""
    (output_dir / "README.md").write_text(text)


def write_presentation_story(output_dir: Path, observed: Sequence[str], inferred: Sequence[str], blockers: Sequence[str], next_steps: Sequence[str]) -> None:
    text = f"""# Presentation Story Draft

## One-Slide Thesis

The CFD postprocessing is now strong enough to show why a predictive 1D model
must be built from decomposed terms rather than a single tuned friction
coefficient: pressure, heat-path, and upcomer-regime effects are all visible and
must be admitted or excluded explicitly.

## Suggested Slide Sequence For Tomorrow

1. **Evidence contract.** Salt 2/3/4 Jin are admitted mainline evidence; corrected
   Salt is status-only; all rows still need mesh/GCI before coefficient claims.
2. **Pressure decomposition.** Show `pressure_decomposition_by_span.svg`.
   Message: raw `p_rgh` slopes are not friction; buoyancy, mechanical loss,
   development/reset, minor losses, and recirculation flags are now separated.
3. **Heat accounting.** Show `heat_source_sink_by_patch_group.svg`.
   Message: the thermal boundary matters first order; the test section is a net
   heat sink in the wall-flux accounting.
4. **Thermal residuals.** Show `heat_enthalpy_residual_by_segment.svg`.
   Message: span endpoint temperatures now expose segment residuals; upcomer and
   cooler residuals stay diagnostic because of recirculation and bracketing limits.
5. **Friction screen.** Show `friction_form_mdot_error.svg` and optionally
   `friction_per_leg_pressure_drop.svg`.
   Message: F3 Shah apparent currently performs best in mdot, while F4
   over-stiffens. Do not claim final mdot predictivity until thermal replay is fixed.
6. **F5/Ri honesty.** Show `f5_ri_screen_coefficients.svg`.
   Message: the current three-point admitted dataset does not support a Ri
   multiplier; the framework waits for gated perturbations.
7. **Upcomer regime.** Show `upcomer_backflow_vs_re.svg`.
   Message: the upcomer is a recirculating mixed-convection regime, not ordinary
   pipe friction.
8. **What is still moving.** Show `corrected_salt_gate_status.svg`.
   Message: perturbations may expand the range, but they are not admitted yet.

## Observed Facts To Say Out Loud

{bullet_lines(observed)}

## Interpretation To Keep Conservative

{bullet_lines(inferred)}

## Do Not Overclaim

{bullet_lines(blockers)}

## Ask / Next Work

{bullet_lines(next_steps)}
"""
    (output_dir / "presentation_story.md").write_text(text)


def write_thesis_story(output_dir: Path, observed: Sequence[str], inferred: Sequence[str], blockers: Sequence[str], next_steps: Sequence[str]) -> None:
    text = f"""# Master's Thesis Story Draft

## Working Chapter Argument

The CFD-to-1D closure workflow should be presented as an evidence reduction
pipeline. The main contribution is not a single new coefficient. It is the
construction of auditable CFD observables that can be mapped onto separate 1D
terms: reversible buoyancy, irreversible distributed resistance, developing-flow
excess, feature/minor losses, thermal boundary exchange, and recirculation
regime diagnostics.

## Numerical Analysis Framing

The July 8 pressure ledger supplies span-level hydraulic decomposition with
source windows and admission flags. The July 8 patchwise heat ledger supplies
the corresponding wall-flux accounting plus non-junction segment enthalpy
residuals from endpoint bulk-temperature extraction. The closure observation
table provides the row-level contract needed to
separate fit targets from validation diagnostics.

## Current Scientific Findings

{bullet_lines(observed)}

## Interpretation For Thesis Prose

{bullet_lines(inferred)}

## Remaining Threats To Validity

{bullet_lines(blockers)}

## Proposed Thesis Next Steps

{bullet_lines(next_steps)}

## Draft Thesis Paragraph

The present CFD evidence indicates that the TAMU loop cannot be reduced to a
single fully developed friction closure without losing key physics. In the
heated and cooled branches, pressure behavior contains both reversible
density-gradient forcing and irreversible mechanical loss. In the upcomer,
recirculation violates the single-stream assumption behind ordinary pipe
friction. In the thermal model, wall-flux accounting shows that passive and
junction losses, as well as net test-section heat removal, are large enough to
affect the buoyancy driver. Therefore the predictive 1D model should be
validated through separate pressure-distribution, heat-balance, mass-flow, and
regime-classification scores rather than through mass flow alone.
"""
    (output_dir / "thesis_story.md").write_text(text)


def write_next_steps(output_dir: Path, observed: Sequence[str], inferred: Sequence[str], blockers: Sequence[str], next_steps: Sequence[str]) -> None:
    text = f"""# Trends And Next Analysis

## Trends

{bullet_lines(inferred)}

## Analysis Ready Today

- Present the generated pressure, heat, friction, F5, upcomer, and status charts.
- Use the closure observation table to start a model-form bakeoff with separated
  fit and validation rows.
- Use the new heat enthalpy residual table to keep thermal mismatch separate
  from mdot and pressure scores.

## Work In Progress

{bullet_lines(blockers)}

## Recommended Sequence

{bullet_lines(next_steps)}
"""
    (output_dir / "trends_and_next_analysis.md").write_text(text)


def bullet_lines(items: Sequence[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = build_package(args.output_dir)
    print(json.dumps({"output_dir": summary["output_dir"], "figures": summary["figures"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
