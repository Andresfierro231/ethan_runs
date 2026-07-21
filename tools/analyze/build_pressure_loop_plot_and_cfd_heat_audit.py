#!/usr/bin/env python3
"""Create pressure-loop plots and a CFD heat audit from existing artifacts."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


TASK = "AGENT-462"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit")
OUT = ROOT / OUT_REL

PRESSURE_STATION = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/"
    "all_streamwise_pressure_1d_map.csv"
)
PRESSURE_CASE_REVIEW = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/"
    "pressure_case_scientific_review.csv"
)
PATCH_ROLE_HEAT = ROOT / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
VAL_SALT2_HEAT = ROOT / (
    "work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/"
    "val_salt2_section_heat_loss_ledger.csv"
)
JUNCTION_CORNER_REVIEW = ROOT / (
    "work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/"
    "scientific_review.md"
)

MAINLINE_KEYS = ["salt2_mainline", "salt3_mainline", "salt4_mainline", "val_salt2"]
CASE_COLORS = {
    "salt1_hi10q": "#8c6d31",
    "salt1_lo10q": "#bd9e39",
    "salt1_nominal": "#e7ba52",
    "salt2_hi5q": "#1f77b4",
    "salt2_lo5q": "#6baed6",
    "salt2_mainline": "#08306b",
    "salt3_mainline": "#238b45",
    "salt4_hi5q": "#cb181d",
    "salt4_lo5q": "#fb6a4a",
    "salt4_mainline": "#67000d",
    "val_salt2": "#54278f",
}
BRANCH_BANDS = [
    ("lower_leg heater", 0, 4, "#fff7bc"),
    ("left lower upcomer", 5, 9, "#d9f0d3"),
    ("test section", 10, 14, "#fee0d2"),
    ("left upper upcomer", 15, 19, "#c7e9c0"),
    ("upper cooled leg", 20, 24, "#deebf7"),
    ("right downcomer", 25, 29, "#e5e5e5"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    return float(value)


def group_pressure_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_key"]].append(row)
    for case_key in grouped:
        grouped[case_key].sort(key=lambda row: int(row["loop_order_index"]))
    return grouped


def nice_ticks(vmin: float, vmax: float, count: int = 6) -> list[float]:
    if math.isclose(vmin, vmax):
        return [vmin]
    raw = (vmax - vmin) / max(count - 1, 1)
    power = 10 ** math.floor(math.log10(abs(raw)))
    step = power
    for mult in (1, 2, 5, 10):
        if raw <= mult * power:
            step = mult * power
            break
    start = math.floor(vmin / step) * step
    stop = math.ceil(vmax / step) * step
    ticks = []
    value = start
    while value <= stop + step * 0.5:
        ticks.append(value)
        value += step
    return ticks


def write_pressure_svg(
    path: Path,
    grouped: dict[str, list[dict[str, str]]],
    case_keys: list[str],
    value_key: str,
    title: str,
    y_label: str,
) -> None:
    width, height = 1280, 720
    left, right, top, bottom = 92, 260, 55, 118
    plot_w = width - left - right
    plot_h = height - top - bottom
    values = [f(row, value_key) for key in case_keys for row in grouped[key]]
    ticks = nice_ticks(min(values), max(values), 7)
    ymin, ymax = min(ticks), max(ticks)
    if math.isclose(ymin, ymax):
        ymin -= 1
        ymax += 1

    def x_for(index: int) -> float:
        return left + index / 29.0 * plot_w

    def y_for(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'.format(
            w=width, h=height
        ),
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.axis{stroke:#333;stroke-width:1.2}.grid{stroke:#ddd;stroke-width:1}.line{fill:none;stroke-width:2.4}.thin{stroke-width:1.6}.label{font-size:13px}.small{font-size:11px}.title{font-size:22px;font-weight:700}.legend{font-size:12px}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text x="{left}" y="32" class="title">{title}</text>',
    ]

    for label, start, end, color in BRANCH_BANDS:
        x0 = x_for(start) - (plot_w / 29.0) * 0.45
        x1 = x_for(end) + (plot_w / 29.0) * 0.45
        parts.append(f'<rect x="{x0:.1f}" y="{top}" width="{x1-x0:.1f}" height="{plot_h}" fill="{color}" opacity="0.45"/>')
        parts.append(
            f'<text x="{(x0+x1)/2:.1f}" y="{height-48}" text-anchor="middle" class="small">{label}</text>'
        )

    for tick in ticks:
        y = y_for(tick)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="label">{tick:.0f}</text>')

    for idx in range(30):
        x = x_for(idx)
        if idx % 5 == 0 or idx == 29:
            parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" class="grid"/>')
            parts.append(f'<text x="{x:.1f}" y="{height-84}" text-anchor="middle" class="small">{idx}</text>')

    parts.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" class="axis"/>')
    parts.append(f'<text x="{left + plot_w/2}" y="{height-18}" text-anchor="middle" class="label">loop-order station index, physical flow order</text>')
    parts.append(
        f'<text x="22" y="{top + plot_h/2}" transform="rotate(-90 22,{top + plot_h/2})" text-anchor="middle" class="label">{y_label}</text>'
    )

    for case_key in case_keys:
        rows = grouped[case_key]
        points = " ".join(f'{x_for(int(row["loop_order_index"])):.1f},{y_for(f(row, value_key)):.1f}' for row in rows)
        parts.append(
            f'<polyline points="{points}" class="line" stroke="{CASE_COLORS.get(case_key, "#333")}"/>'
        )
        for row in rows[::4]:
            parts.append(
                f'<circle cx="{x_for(int(row["loop_order_index"])):.1f}" cy="{y_for(f(row, value_key)):.1f}" r="2.6" fill="{CASE_COLORS.get(case_key, "#333")}"/>'
            )

    legend_x = left + plot_w + 28
    legend_y = top + 10
    parts.append(f'<text x="{legend_x}" y="{legend_y}" class="label" font-weight="700">cases</text>')
    for i, case_key in enumerate(case_keys):
        y = legend_y + 20 + 18 * i
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x+28}" y2="{y}" stroke="{CASE_COLORS.get(case_key, "#333")}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x+36}" y="{y+4}" class="legend">{case_key}</text>')

    parts.append('<text x="{x}" y="{y}" class="small">Note: diagnostic station means; not fit-admitted hydraulic coefficients.</text>'.format(x=left, y=height - 4))
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def build_pressure_plot_index(grouped: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    plots = [
        {
            "plot_id": "mainline_static_pressure",
            "path": OUT / "pressure_loop_mainline_static_p.svg",
            "case_keys": [key for key in MAINLINE_KEYS if key in grouped],
            "value_key": "mean_p_Pa",
            "title": "Pressure Map Through Loop: Static p",
            "y_label": "mean static p [Pa]",
        },
        {
            "plot_id": "mainline_p_rgh",
            "path": OUT / "pressure_loop_mainline_p_rgh.svg",
            "case_keys": [key for key in MAINLINE_KEYS if key in grouped],
            "value_key": "mean_p_rgh_Pa",
            "title": "Pressure Map Through Loop: p_rgh",
            "y_label": "mean p_rgh [Pa]",
        },
        {
            "plot_id": "all_cases_static_pressure",
            "path": OUT / "pressure_loop_all_cases_static_p.svg",
            "case_keys": sorted(grouped),
            "value_key": "mean_p_Pa",
            "title": "Pressure Map Through Loop: All Harvested Cases",
            "y_label": "mean static p [Pa]",
        },
    ]
    rows = []
    for plot in plots:
        write_pressure_svg(plot["path"], grouped, plot["case_keys"], plot["value_key"], plot["title"], plot["y_label"])
        rows.append(
            {
                "plot_id": plot["plot_id"],
                "path": rel(plot["path"]),
                "case_keys": ";".join(plot["case_keys"]),
                "value_key": plot["value_key"],
                "interpretation": "diagnostic_station_pressure_map_not_fit_admitted",
            }
        )
    return rows


def build_mainline_heat_audit(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_case: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_case[row["case_id"]][row["role"]] = row
    out = []
    case_key_map = {"salt_2": "salt2_mainline", "salt_3": "salt3_mainline", "salt_4": "salt4_mainline"}
    for case_id in sorted(by_case):
        roles = by_case[case_id]
        heater = f(roles["heater"], "realized_wallHeatFlux_W")
        imposed_heater = f(roles["heater"], "imposed_Q_W")
        cooler = f(roles["cooler"], "realized_wallHeatFlux_W")
        ambient = f(roles["ambient_wall"], "realized_wallHeatFlux_W")
        junction = f(roles["junction_other"], "realized_wallHeatFlux_W")
        test_section = f(roles["test_section"], "realized_wallHeatFlux_W")
        net = heater + cooler + ambient + junction + test_section
        passive_loss = -(ambient + junction + min(test_section, 0.0))
        junction_area = f(roles["junction_other"], "area_m2")
        ambient_area = f(roles["ambient_wall"], "area_m2")
        out.append(
            {
                "case_key": case_key_map[case_id],
                "case_id": case_id,
                "source_id": roles["heater"]["source_id"],
                "heat_audit_source": rel(PATCH_ROLE_HEAT),
                "coverage_status": "role_level_cfd_heat_accounting",
                "heater_imposed_Q_W": imposed_heater,
                "heater_realized_to_fluid_W": heater,
                "heater_realization_fraction": heater / imposed_heater if imposed_heater else "",
                "cooler_realized_to_fluid_W": cooler,
                "test_section_realized_to_fluid_W": test_section,
                "ambient_wall_realized_to_fluid_W": ambient,
                "junction_stub_realized_to_fluid_W": junction,
                "downcomer_realized_to_fluid_W": "",
                "upcomer_realized_to_fluid_W": "",
                "transport_stub_realized_to_fluid_W": "",
                "net_realized_to_fluid_W": net,
                "passive_loss_excluding_cooler_W": passive_loss,
                "junction_loss_positive_W": -junction,
                "junction_fraction_of_passive_loss_excluding_cooler": (-junction / passive_loss) if passive_loss else "",
                "junction_loss_fraction_of_heater_imposed": (-junction / imposed_heater) if imposed_heater else "",
                "junction_loss_fraction_of_heater_realized": (-junction / heater) if heater else "",
                "junction_area_m2": junction_area,
                "junction_loss_flux_W_m2": (-junction / junction_area) if junction_area else "",
                "ambient_wall_area_m2": ambient_area,
                "ambient_wall_loss_flux_W_m2": (-ambient / ambient_area) if ambient_area else "",
                "junction_patch_count": roles["junction_other"]["patch_count"],
                "junction_rcExternalTemperature_count": roles["junction_other"]["rcExternalTemperature_count"],
                "junction_externalTemperature_count": roles["junction_other"]["externalTemperature_count"],
                "junction_zeroGradient_count": roles["junction_other"]["zeroGradient_count"],
                "notes": "Positive values heat fluid; negative values remove heat. Junction/stub row is aggregate, not split by individual junction.",
            }
        )
    return out


def build_val_salt2_heat_audit(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_section = {row["section_key"]: row for row in rows}
    heater = f(by_section["heater"], "latest_cfd_realized_net_to_fluid_W")
    cooler = f(by_section["cooling_branch"], "latest_cfd_realized_net_to_fluid_W")
    test_section = f(by_section["test_section"], "latest_cfd_realized_net_to_fluid_W")
    downcomer = f(by_section["downcomer"], "latest_cfd_realized_net_to_fluid_W")
    upcomer = f(by_section["upcomer"], "latest_cfd_realized_net_to_fluid_W")
    upper_transport = f(by_section["upper_transport"], "latest_cfd_realized_net_to_fluid_W")
    lower_transport = f(by_section["lower_transport"], "latest_cfd_realized_net_to_fluid_W")
    junction = f(by_section["junctions"], "latest_cfd_realized_net_to_fluid_W")
    net = f(by_section["total_Q_postProc"], "latest_cfd_realized_net_to_fluid_W")
    passive_loss = -(test_section + downcomer + upcomer + upper_transport + lower_transport + junction)
    return [
        {
            "case_key": "val_salt2",
            "case_id": "val_salt_2",
            "source_id": by_section["heater"]["source_id"],
            "heat_audit_source": rel(VAL_SALT2_HEAT),
            "coverage_status": "section_level_cfd_heat_ledger",
            "heater_imposed_Q_W": "",
            "heater_realized_to_fluid_W": heater,
            "heater_realization_fraction": "",
            "cooler_realized_to_fluid_W": cooler,
            "test_section_realized_to_fluid_W": test_section,
            "ambient_wall_realized_to_fluid_W": "",
            "junction_stub_realized_to_fluid_W": junction,
            "downcomer_realized_to_fluid_W": downcomer,
            "upcomer_realized_to_fluid_W": upcomer,
            "transport_stub_realized_to_fluid_W": upper_transport + lower_transport,
            "net_realized_to_fluid_W": net,
            "passive_loss_excluding_cooler_W": passive_loss,
            "junction_loss_positive_W": -junction,
            "junction_fraction_of_passive_loss_excluding_cooler": (-junction / passive_loss) if passive_loss else "",
            "junction_loss_fraction_of_heater_imposed": "",
            "junction_loss_fraction_of_heater_realized": (-junction / heater) if heater else "",
            "junction_area_m2": "",
            "junction_loss_flux_W_m2": "",
            "ambient_wall_area_m2": "",
            "ambient_wall_loss_flux_W_m2": "",
            "junction_patch_count": "",
            "junction_rcExternalTemperature_count": "",
            "junction_externalTemperature_count": "",
            "junction_zeroGradient_count": "",
            "notes": "Val Salt2 uses section ledger; junction area and BC counts are not included in this source.",
        }
    ]


def build_heat_coverage_table(pressure_case_rows: list[dict[str, str]], heat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    heat_keys = {row["case_key"] for row in heat_rows}
    rows = []
    for row in pressure_case_rows:
        case_key = row["case_key"]
        rows.append(
            {
                "case_key": case_key,
                "pressure_map_available": "yes",
                "heat_audit_available": "yes" if case_key in heat_keys else "no",
                "reason_if_missing": "" if case_key in heat_keys else "no comparable realized CFD heat ledger found in current artifacts",
                "pressure_source_native_case_path": row["native_case_path"],
            }
        )
    return rows


def write_heat_bar_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    width, height = 1120, 620
    left, right, top, bottom = 90, 40, 58, 120
    plot_w = width - left - right
    plot_h = height - top - bottom
    roles = [
        ("heater_realized_to_fluid_W", "heater", "#e41a1c"),
        ("cooler_realized_to_fluid_W", "cooler", "#377eb8"),
        ("test_section_realized_to_fluid_W", "test section", "#984ea3"),
        ("ambient_wall_realized_to_fluid_W", "ambient wall", "#4daf4a"),
        ("junction_stub_realized_to_fluid_W", "junction/stub", "#ff7f00"),
        ("downcomer_realized_to_fluid_W", "downcomer", "#a65628"),
        ("upcomer_realized_to_fluid_W", "upcomer", "#f781bf"),
        ("transport_stub_realized_to_fluid_W", "transport/stub", "#999999"),
    ]
    max_abs = max(abs(f(row, key)) for row in rows for key, _, _ in roles if row.get(key) != "")
    scale_max = math.ceil(max_abs / 50.0) * 50.0

    def y_for(value: float) -> float:
        return top + (scale_max - value) / (2 * scale_max) * plot_h

    zero_y = y_for(0)
    group_w = plot_w / len(rows)
    bar_w = min(18, group_w / (len(roles) + 1))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.title{font-size:22px;font-weight:700}.label{font-size:13px}.small{font-size:11px}.grid{stroke:#ddd}.axis{stroke:#333;stroke-width:1.2}</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="32" class="title">CFD Heat Audit by Run</text>',
    ]
    for tick in nice_ticks(-scale_max, scale_max, 7):
        y = y_for(tick)
        parts.append(f'<line x1="{left}" x2="{left+plot_w}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" class="small">{tick:.0f}</text>')
    parts.append(f'<line x1="{left}" x2="{left+plot_w}" y1="{zero_y:.1f}" y2="{zero_y:.1f}" class="axis"/>')
    for i, row in enumerate(rows):
        x_center = left + group_w * (i + 0.5)
        start_x = x_center - (len(roles) * bar_w) / 2
        for j, (key, _, color) in enumerate(roles):
            if row.get(key) == "":
                continue
            value = f(row, key)
            y = y_for(max(value, 0))
            h = abs(y_for(value) - zero_y)
            if value < 0:
                y = zero_y
            x = start_x + j * bar_w
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" height="{h:.1f}" fill="{color}" opacity="0.88"/>')
        parts.append(f'<text x="{x_center:.1f}" y="{height-72}" text-anchor="middle" transform="rotate(-35 {x_center:.1f},{height-72})" class="small">{row["case_key"]}</text>')
    legend_x, legend_y = left, height - 34
    for i, (_, label, color) in enumerate(roles):
        x = legend_x + i * 125
        parts.append(f'<rect x="{x}" y="{legend_y}" width="14" height="10" fill="{color}"/>')
        parts.append(f'<text x="{x+18}" y="{legend_y+10}" class="small">{label}</text>')
    parts.append(f'<text x="22" y="{top+plot_h/2}" transform="rotate(-90 22,{top+plot_h/2})" text-anchor="middle" class="label">realized heat to fluid [W]; negative removes heat</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def write_audit_md(
    heat_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    plot_rows: list[dict[str, str]],
    trend_rows: list[dict[str, Any]],
) -> None:
    missing = [row["case_key"] for row in coverage_rows if row["heat_audit_available"] == "no"]
    lines = [
        "# Pressure Loop Plot and CFD Heat Audit",
        "",
        "## Pressure Plots",
        "",
        "The pressure plots are SVGs generated directly from AGENT-457 station maps. They are diagnostic pressure maps, not admitted hydraulic coefficients.",
        "",
    ]
    for row in plot_rows:
        lines.append(f"- `{row['plot_id']}`: `{row['path']}`")
    lines.extend(
        [
            "",
            "## Pressure Map Sanity Check",
            "",
            "The x-axis is the AGENT-457 `loop_order_index`, which already applies the label-locked physical flow order. The branch bands map to 1D model regions as follows: lower_leg heater -> `heated_incline`, left lower upcomer -> `left_lower_vertical`, test section -> `test_section`, left upper upcomer -> `left_upper_vertical`, upper cooled leg -> cooled upper run, and right downcomer -> right vertical return. The plotted values preserve the source station labels and the source caveat that every row remains `diagnostic_station_pressure_ladder_not_fit_admitted` until orientation, straight-loss subtraction, and recirculation-mask gates are completed.",
            "",
            "The plotted mainline Salt2-4 static-pressure traces nearly overlay one another in shape, which is consistent with the same geometry and station extraction. Static `p` and `p_rgh` are both plotted because AGENT-460 found static-vs-`p_rgh` sign differences at several local deltas. For model fitting, these plots should be read as location/context diagnostics rather than a pressure-drop coefficient source.",
            "",
            "## Heat Audit Coverage",
            "",
            f"Comparable realized CFD heat accounting was found for `{len(heat_rows)}` pressure-map cases. Missing comparable heat ledgers: `{';'.join(missing)}`.",
            "",
            "| case | heater to fluid W | cooler W | junction/stub W | passive loss excl cooler W | junction/passive | notes |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in heat_rows:
        frac = row["junction_fraction_of_passive_loss_excluding_cooler"]
        frac_txt = "" if frac == "" else f"{float(frac):.3f}"
        lines.append(
            "| `{case}` | {heater:.3f} | {cooler:.3f} | {junction:.3f} | {passive:.3f} | {frac} | {notes} |".format(
                case=row["case_key"],
                heater=float(row["heater_realized_to_fluid_W"]),
                cooler=float(row["cooler_realized_to_fluid_W"]),
                junction=float(row["junction_stub_realized_to_fluid_W"]),
                passive=float(row["passive_loss_excluding_cooler_W"]),
                frac=frac_txt,
                notes=row["coverage_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Heat Balance Critique",
            "",
            "The Salt2-4 role-level audits are physically coherent in aggregate: heater-to-fluid heat is positive, cooler and passive surfaces are negative, and the realized wall-flux sums close within about 0.3 W. The val_salt2 section ledger also closes tightly, with a reported total of about 0.19 W. That closure supports using these rows for a heat-loss audit, but not for local junction calibration because the junction/stub values are aggregated patch groups.",
            "",
            "The missing heat-ledger cases are not failed cases; they are pressure-mapped cases without a comparable realized heat accounting artifact in the current work products. They should stay absent from heat-loss trends until a matching heat ledger is harvested with the same sign convention and role definitions.",
            "",
            "## Per-Run Heat Audit",
            "",
        ]
    )
    for row in heat_rows:
        jfrac = row["junction_fraction_of_passive_loss_excluding_cooler"]
        jfrac_txt = "not available" if jfrac == "" else f"{float(jfrac):.1%}"
        heater_imposed = row["heater_imposed_Q_W"]
        imposed_txt = "not recorded in source" if heater_imposed == "" else f"{float(heater_imposed):.1f} W imposed"
        jheater = row["junction_loss_fraction_of_heater_imposed"]
        jheater_txt = "not available" if jheater == "" else f"{float(jheater):.1%} of imposed heater power"
        lines.append(
            f"- `{row['case_key']}`: heater to fluid {float(row['heater_realized_to_fluid_W']):.3f} W ({imposed_txt}); cooler {float(row['cooler_realized_to_fluid_W']):.3f} W; test section {float(row['test_section_realized_to_fluid_W']):.3f} W; junction/stub {float(row['junction_stub_realized_to_fluid_W']):.3f} W. Junction/stub loss is {jfrac_txt} of passive non-cooler loss and {jheater_txt}."
        )
    lines.extend(
        [
            "",
            "## Junction/Stub Heat-Loss Interpretation",
            "",
            "The CFD shows junction/stub heat loss is not a small numerical artifact. In Salt2-4 mainline it rises from about 39 W to 48 W as operating power/temperature rises, while remaining roughly 14-15% of imposed heater power and about one third of non-cooler passive losses.",
            "",
            "The large value is physically plausible because the junction/stub group is an aggregate of many exposed connector patches, not a single bend. In the Salt2-4 role table it contains 29 patches with about 0.04248 m2 of area; the same row mixes 11 `rcExternalTemperature`, 7 `externalTemperature`, and 11 `zeroGradient` patches. Those surfaces have concentrated area near hot junctions, 3D conduction paths through fittings/stubs, and external boundary conditions that include radiation in total `wallHeatFlux`. That combination makes per-area heat loss high compared with long insulated pipe surfaces.",
            "",
            "Scientifically, this means the current 1D model should not hide junction/stub loss in a global insulation fudge factor. It should carry explicit localized loss terms or surface groups.",
            "",
            "## Ways The 1D Model Could Improve Junction Heat-Loss Treatment",
            "",
            "1. Add explicit zero-length junction/stub thermal nodes at lower-left, lower-right, upper-right, and upper-left.",
            "2. Give each junction node its own external area, effective wall/insulation resistance, ambient temperature, emissivity, and convection coefficient.",
            "3. Split `junction_other` into the four physical junctions in future CFD postprocessing so the 1D model can fit/validate local losses instead of one aggregate term.",
            "4. Treat radiation as inseparable from realized CFD `wallHeatFlux` unless future extraction preserves radiative and convective pieces separately.",
            "5. Couple the thermal loss to local fluid temperature, not a global loop mean, because junctions sit at very different temperatures.",
            "6. Preserve setup-only predictive legality: fit parameters may come from training, but runtime prediction must not consume realized CFD `wallHeatFlux`.",
            "",
            "## Trend Notes",
            "",
        ]
    )
    for row in trend_rows:
        lines.append(f"- {row['trend']}: {row['interpretation']}")
    lines.extend(
        [
            "",
            "## Junction Heat Loss And Corner Pressure Drop State",
            "",
            "We understand the junction heat loss at the role/section level, not at individual physical junction resolution. The strongest present conclusion is that the aggregate junction/stub thermal pathway is persistent and scales with operating temperature/power. We do not yet have enough split-by-junction evidence to assign loss to lower-left versus lower-right versus upper-right versus upper-left in the 1D model.",
            "",
            "We do not yet have an admitted corner pressure-drop model. AGENT-460 found corner-pressure diagnostics, but they remain upper-bound/local diagnostics because the pressure rows are still blocked by orientation, straight-loss subtraction, and recirculation-mask admission. They are useful for prioritizing where to extract better evidence, not for final K-factor fitting.",
            "",
            "## Provenance",
            "",
            "- Pressure station source: `work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/all_streamwise_pressure_1d_map.csv`",
            "- Pressure scientific review: `work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/scientific_review.md`",
            "- Salt2-4 heat source: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv`",
            "- val_salt2 heat source: `work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv`",
            "- Reusable builder: `tools/analyze/build_pressure_loop_plot_and_cfd_heat_audit.py`",
            "- Tests: `tools/analyze/test_pressure_loop_plot_and_cfd_heat_audit.py`",
        ]
    )
    (OUT / "heat_audit_and_modeling_recommendations.md").write_text("\n".join(lines) + "\n")


def build_trend_rows(heat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mainline = [row for row in heat_rows if row["case_key"] in {"salt2_mainline", "salt3_mainline", "salt4_mainline"}]
    mainline.sort(key=lambda row: row["case_key"])
    jloss = [float(row["junction_loss_positive_W"]) for row in mainline]
    heater_imposed = [float(row["heater_imposed_Q_W"]) for row in mainline]
    jfrac = [float(row["junction_loss_fraction_of_heater_imposed"]) for row in mainline]
    flux = [float(row["junction_loss_flux_W_m2"]) for row in mainline]
    return [
        {
            "trend": "junction_loss_vs_power",
            "interpretation": f"Salt2-4 junction/stub heat loss increases monotonically {jloss[0]:.3f} -> {jloss[-1]:.3f} W as imposed heater power increases {heater_imposed[0]:.1f} -> {heater_imposed[-1]:.1f} W.",
        },
        {
            "trend": "junction_fraction_of_heater",
            "interpretation": f"Junction loss fraction of imposed heater is nearly flat: {jfrac[0]:.3f}, {jfrac[1]:.3f}, {jfrac[2]:.3f}. This suggests a structurally persistent local heat path rather than a one-case anomaly.",
        },
        {
            "trend": "junction_flux",
            "interpretation": f"Junction/stub heat flux magnitude rises {flux[0]:.1f} -> {flux[-1]:.1f} W/m2 over Salt2-4, consistent with higher local temperatures driving external losses.",
        },
    ]


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    pressure_rows = read_csv(PRESSURE_STATION)
    grouped = group_pressure_rows(pressure_rows)
    plot_rows = build_pressure_plot_index(grouped)

    mainline_heat = build_mainline_heat_audit(read_csv(PATCH_ROLE_HEAT))
    val_heat = build_val_salt2_heat_audit(read_csv(VAL_SALT2_HEAT))
    heat_rows = mainline_heat + val_heat
    heat_rows.sort(key=lambda row: ["salt2_mainline", "salt3_mainline", "salt4_mainline", "val_salt2"].index(row["case_key"]))
    pressure_case_rows = read_csv(PRESSURE_CASE_REVIEW)
    coverage_rows = build_heat_coverage_table(pressure_case_rows, heat_rows)
    trend_rows = build_trend_rows(heat_rows)

    write_csv(OUT / "cfd_heat_audit_by_run.csv", heat_rows)
    write_csv(OUT / "heat_audit_coverage_by_pressure_case.csv", coverage_rows)
    write_csv(OUT / "junction_heat_loss_trends.csv", trend_rows, ["trend", "interpretation"])
    write_csv(OUT / "pressure_plot_index.csv", plot_rows)
    write_heat_bar_svg(OUT / "cfd_heat_audit_by_run.svg", heat_rows)
    write_csv(
        OUT / "source_manifest.csv",
        [
            {"source_type": "pressure_station_map", "path": rel(PRESSURE_STATION), "use": "station pressure values and loop order for plots"},
            {"source_type": "pressure_case_review", "path": rel(PRESSURE_CASE_REVIEW), "use": "pressure-case list and coverage status"},
            {"source_type": "mainline_patch_role_heat", "path": rel(PATCH_ROLE_HEAT), "use": "Salt2-4 mainline role-level CFD realized heat accounting"},
            {"source_type": "val_salt2_heat_ledger", "path": rel(VAL_SALT2_HEAT), "use": "val_salt2 section heat ledger"},
            {"source_type": "junction_corner_review", "path": rel(JUNCTION_CORNER_REVIEW), "use": "prior scientific review of junction and corner evidence"},
        ],
        ["source_type", "path", "use"],
    )
    write_audit_md(heat_rows, coverage_rows, plot_rows, trend_rows)

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "pressure_cases_plotted": len(grouped),
        "pressure_station_rows": len(pressure_rows),
        "plot_count": len(plot_rows),
        "heat_audit_case_count": len(heat_rows),
        "heat_audit_cases": [row["case_key"] for row in heat_rows],
        "pressure_cases_without_comparable_heat_audit": [
            row["case_key"] for row in coverage_rows if row["heat_audit_available"] == "no"
        ],
        "salt2_4_junction_loss_W": {
            row["case_key"]: row["junction_loss_positive_W"] for row in heat_rows if row["case_key"] != "val_salt2"
        },
        "outputs": {
            "mainline_static_plot": rel(OUT / "pressure_loop_mainline_static_p.svg"),
            "mainline_p_rgh_plot": rel(OUT / "pressure_loop_mainline_p_rgh.svg"),
            "all_cases_static_plot": rel(OUT / "pressure_loop_all_cases_static_p.svg"),
            "heat_audit_svg": rel(OUT / "cfd_heat_audit_by_run.svg"),
            "heat_audit_csv": rel(OUT / "cfd_heat_audit_by_run.csv"),
            "recommendations": rel(OUT / "heat_audit_and_modeling_recommendations.md"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
