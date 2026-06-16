#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import WORKSPACE_ROOT, csv_dump, ensure_dir, iso_timestamp, save_matplotlib_figure  # noqa: E402

PACKAGE_DIR = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_transient_axial_package"
STATUS_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "all_salt_case_status.csv"
VALIDATION_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_direct_validation" / "ethan_direct_validation_metrics.csv"
PRESSURE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_ethan_section_transport_package" / "representative_section_summary.csv"
REPRESENTATIVE_CSV = WORKSPACE_ROOT / "reports" / "2026-06-04_all_salt_behavior_package" / "representative_case_selection.csv"
TIMESERIES_CSV = PACKAGE_DIR / "all_salt_transient_timeseries.csv"
LAST_WINDOW_CSV = PACKAGE_DIR / "all_salt_transient_last_window.csv"
AXIAL_LATEST_CSV = PACKAGE_DIR / "all_salt_axial_patch_latest.csv"
PRIMARY_METRICS = ["mdot_mean_abs_kg_s", "tp_mean_k", "TW5", "TW9", "ambient_proxy_w", "total_q_net_w"]
METRIC_DISPLAY = {
    "mdot_mean_abs_kg_s": "|mdot| mean",
    "tp_mean_k": "TP mean",
    "TW5": "TW5",
    "TW9": "TW9",
    "ambient_proxy_w": "Ambient proxy",
    "total_q_net_w": "Net total Q",
}
CASE_COLORS = {"val": "#1f1f1f", "jin": "#0b6e4f", "kirst": "#bc3908", "other": "#5f0f40"}
PLOT_GUIDE = {
    "metric_coverage_end_times.png": {
        "focus": "Shows the latest available time for each primary transient metric by case. It reveals where continued wallHeatFlux data exist beyond probe histories.",
        "terms": [
            "`TP mean` is the mean of the six bulk temperature probes `TP1..TP6`.",
            "`Ambient proxy` is the derived ambient-like loss from wallHeatFlux accounting.",
            "`Net total Q` is the signed all-wall total from `total_Q.dat`; small late values indicate a small residual enthalpy imbalance.",
        ],
    },
    "salt_test_*_transient_tail.png": {
        "focus": "Late-window tail comparison for mass flow, bulk temperature, ambient-loss proxy, and net heat balance. Use this for numerical steadiness rather than full-transient storytelling.",
        "terms": [
            "The x-axis is truncated to the last 80 samples available for each case and metric.",
            "The corresponding late-window slopes are summarized numerically in `case_audit_summary.csv`.",
        ],
    },
    "salt_test_*_axial_temperature_profile.png": {
        "focus": "Latest-time ordered-patch wall-temperature profile along each leg when reconstructed `T` was readable.",
        "terms": [
            "`Ordered patch progress` is a normalized patch index from 0 to 1 within a leg; it is not a geometric arc length.",
            "Missing curves mean the case fell back to q-only axial reporting because `foamPostProcess` could not read reconstructed `T` cleanly.",
        ],
    },
}

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def case_variant(source_id: str, status_row: dict[str, str]) -> str:
    variant = (status_row.get("variant_label") or "").strip().lower()
    if variant:
        return variant
    if source_id.startswith("val_"):
        return "val"
    return "other"


def case_color(source_id: str, status_row: dict[str, str]) -> str:
    return CASE_COLORS.get(case_variant(source_id, status_row), CASE_COLORS["other"])


def case_label(source_id: str) -> str:
    return source_id.replace("viscosity_screening_", "").replace("_coarse_mesh_laminar", "").replace("_coarse_mesh", "").replace("_", " ")


def build_metric_coverage_rows(transient_rows, last_window_rows, status_map):
    grouped = defaultdict(list)
    for row in transient_rows:
        grouped[(row["source_id"], row["metric"])].append(row)
    last_window_map = {(row["source_id"], row["metric"]): row for row in last_window_rows}
    out = []
    for (source_id, metric), rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda item: float(item["time_s"]))
        first = rows[0]
        last = rows[-1]
        status = status_map.get(source_id, {})
        tail = last_window_map.get((source_id, metric), {})
        out.append({
            "source_id": source_id,
            "base_case_id": status.get("base_case_id", ""),
            "variant_label": status.get("variant_label", ""),
            "family": first.get("family", ""),
            "metric": metric,
            "unit": first.get("unit", ""),
            "sample_count": len(rows),
            "time_start_s": float(first["time_s"]),
            "time_end_s": float(last["time_s"]),
            "duration_s": float(last["time_s"]) - float(first["time_s"]),
            "final_value": float(last["value"]),
            "last_window_count": tail.get("window_count", ""),
            "last_window_mean": tail.get("mean", ""),
            "last_window_std": tail.get("std", ""),
            "last_window_slope_per_s": tail.get("slope_per_s", ""),
            "last_window_end_minus_start": tail.get("end_minus_start", ""),
        })
    return out


def build_axial_extraction_audit_rows(axial_rows, status_map):
    grouped = defaultdict(list)
    for row in axial_rows:
        grouped[row["source_id"]].append(row)
    out = []
    for source_id, rows in sorted(grouped.items()):
        status = status_map.get(source_id, {})
        patch_count = len(rows)
        t_count = sum(1 for row in rows if row.get("areaAverage_T_k") not in ("", None))
        nu_count = sum(1 for row in rows if row.get("areaAverage_Nu") not in ("", None))
        q_count = sum(1 for row in rows if row.get("q_avg_w_m2") not in ("", None))
        errors = sorted({str(row.get("axial_field_extraction_error", "")).strip() for row in rows if str(row.get("axial_field_extraction_error", "")).strip()})
        if patch_count and t_count == patch_count and nu_count == patch_count and not errors:
            extraction_status = "full_field_success"
        elif patch_count and (t_count > 0 or nu_count > 0):
            extraction_status = "partial_field_success"
        elif q_count == patch_count:
            extraction_status = "q_only_fallback"
        else:
            extraction_status = "missing"
        latest_times = [safe_float(row.get("time_s")) for row in rows]
        out.append({
            "source_id": source_id,
            "base_case_id": status.get("base_case_id", ""),
            "variant_label": status.get("variant_label", ""),
            "run_status": status.get("run_status", ""),
            "essential_steadiness_class": status.get("essential_steadiness_class", ""),
            "patch_count": patch_count,
            "leg_count": len({row.get("leg_group", "") for row in rows}),
            "patches_with_q_avg": q_count,
            "patches_with_areaAverage_T": t_count,
            "patches_with_areaAverage_Nu": nu_count,
            "latest_patch_time_s": max(v for v in latest_times if v is not None) if any(v is not None for v in latest_times) else "",
            "latest_field_time_label": max((str(row.get("latest_time", "")) for row in rows), default=""),
            "extraction_status": extraction_status,
            "axial_field_extraction_error": " | ".join(errors),
        })
    return out


def coverage_lookup(rows: Iterable[dict[str, object]]):
    return {(str(row["source_id"]), str(row["metric"])): row for row in rows}


def audit_lookup(rows: Iterable[dict[str, object]]):
    return {str(row["source_id"]): row for row in rows}


def build_case_audit_summary(status_map, validation_map, pressure_map, coverage_rows, axial_audit_rows):
    cov = coverage_lookup(coverage_rows)
    axial = audit_lookup(axial_audit_rows)
    out = []
    for source_id in sorted(status_map):
        status = status_map[source_id]
        validation = validation_map.get(source_id, {})
        pressure = pressure_map.get(source_id, {})
        mdot = cov.get((source_id, "mdot_mean_abs_kg_s"), {})
        tp = cov.get((source_id, "tp_mean_k"), {})
        tw5 = cov.get((source_id, "TW5"), {})
        ambient = cov.get((source_id, "ambient_proxy_w"), {})
        total_q = cov.get((source_id, "total_q_net_w"), {})
        axial_row = axial.get(source_id, {})
        out.append({
            "source_id": source_id,
            "base_case_id": status.get("base_case_id", ""),
            "variant_label": status.get("variant_label", ""),
            "run_status": status.get("run_status", ""),
            "essential_steadiness_class": status.get("essential_steadiness_class", ""),
            "usable_for_steady_state_now": status.get("usable_for_steady_state_now", ""),
            "decision": status.get("decision", ""),
            "mdot_time_end_s": mdot.get("time_end_s", ""),
            "tp_time_end_s": tp.get("time_end_s", ""),
            "tw5_time_end_s": tw5.get("time_end_s", ""),
            "ambient_time_end_s": ambient.get("time_end_s", ""),
            "total_q_time_end_s": total_q.get("time_end_s", ""),
            "mdot_last_window_slope_per_s": mdot.get("last_window_slope_per_s", ""),
            "tp_last_window_slope_per_s": tp.get("last_window_slope_per_s", ""),
            "ambient_last_window_slope_per_s": ambient.get("last_window_slope_per_s", ""),
            "total_q_last_window_slope_per_s": total_q.get("last_window_slope_per_s", ""),
            "exp_all_temp_rmse_k": validation.get("exp_all_temp_rmse_k", ""),
            "exp_mdot_abs_error_pct": validation.get("exp_mdot_abs_error_pct", ""),
            "exp_q_external_loss_abs_error_pct": validation.get("exp_q_external_loss_abs_error_pct", ""),
            "upper_leg_abs_delta_p_rgh_pa": pressure.get("upper_leg_abs_delta_p_rgh_pa", ""),
            "left_leg_abs_delta_p_rgh_pa": pressure.get("left_leg_abs_delta_p_rgh_pa", ""),
            "right_leg_abs_delta_p_rgh_pa": pressure.get("right_leg_abs_delta_p_rgh_pa", ""),
            "axial_extraction_status": axial_row.get("extraction_status", ""),
            "patches_with_areaAverage_T": axial_row.get("patches_with_areaAverage_T", ""),
            "patches_with_areaAverage_Nu": axial_row.get("patches_with_areaAverage_Nu", ""),
            "axial_field_extraction_error": axial_row.get("axial_field_extraction_error", ""),
        })
    return out


def plot_metric_coverage(coverage_rows):
    rows = [row for row in coverage_rows if row["metric"] in PRIMARY_METRICS]
    if not rows:
        return
    case_ids = sorted({str(row["source_id"]) for row in rows})
    x = np.arange(len(case_ids))
    width = 0.12
    fig, ax = plt.subplots(figsize=(16, 7), constrained_layout=True)
    for idx, metric in enumerate(PRIMARY_METRICS):
        offsets = x + (idx - (len(PRIMARY_METRICS) - 1) / 2.0) * width
        values = []
        for source_id in case_ids:
            match = next((row for row in rows if row["source_id"] == source_id and row["metric"] == metric), None)
            values.append(float(match["time_end_s"]) if match else math.nan)
        ax.bar(offsets, values, width=width, label=METRIC_DISPLAY[metric])
    ax.set_xticks(x)
    ax.set_xticklabels([case_label(case_id) for case_id in case_ids], rotation=35, ha="right")
    ax.set_ylabel("Latest available time [s]")
    ax.set_title("Primary transient metric coverage by case")
    ax.legend(loc="upper left", ncol=3, fontsize=8)
    save_matplotlib_figure(fig, PACKAGE_DIR, "metric_coverage_end_times", dpi=220)
    plt.close(fig)


def build_timeseries_lookup(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["source_id"], row["metric"])] += [(float(row["time_s"]), float(row["value"]))]
    out = {}
    for key, pairs in grouped.items():
        pairs.sort(key=lambda item: item[0])
        out[key] = (np.array([pair[0] for pair in pairs]), np.array([pair[1] for pair in pairs]))
    return out


def plot_transient_tail(base_case_id, case_ids, lookup, status_map):
    metrics = [
        ("mdot_mean_abs_kg_s", "|mdot| mean [kg/s]"),
        ("tp_mean_k", "TP mean [K]"),
        ("ambient_proxy_w", "Ambient proxy [W]"),
        ("total_q_net_w", "Net total Q [W]"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    for ax, (metric, ylabel) in zip(axes.flatten(), metrics):
        for source_id in case_ids:
            times, values = lookup.get((source_id, metric), (np.array([]), np.array([])))
            if len(times) == 0:
                continue
            count = min(80, len(times))
            ax.plot(times[-count:], values[-count:], linewidth=2.0, color=case_color(source_id, status_map.get(source_id, {})), label=case_label(source_id))
        ax.set_title(METRIC_DISPLAY[metric])
        ax.set_xlabel("Time [s]")
        ax.set_ylabel(ylabel)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(f"{base_case_id}: late-window transient tail comparison")
    save_matplotlib_figure(fig, PACKAGE_DIR, f"{base_case_id}_transient_tail", dpi=220)
    plt.close(fig)


def plot_axial_temperature(base_case_id, case_ids, axial_rows, status_map):
    leg_order = ["lower_leg", "right_leg", "upper_leg", "left_leg"]
    leg_titles = {"lower_leg": "Lower leg / heater leg", "right_leg": "Right leg / downcomer", "upper_leg": "Upper leg / cooling leg", "left_leg": "Left leg / upcomer"}
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), constrained_layout=True)
    axis_map = dict(zip(leg_order, axes.flatten()))
    any_data = False
    for leg in leg_order:
        ax = axis_map[leg]
        for source_id in case_ids:
            series = sorted([row for row in axial_rows if row["source_id"] == source_id and row["leg_group"] == leg and row.get("areaAverage_T_k") not in ("", None)], key=lambda item: float(item["section_progress_0to1"]))
            if not series:
                continue
            any_data = True
            ax.plot([float(row["section_progress_0to1"]) for row in series], [float(row["areaAverage_T_k"]) for row in series], marker="o", linewidth=1.8, color=case_color(source_id, status_map.get(source_id, {})), label=case_label(source_id))
        ax.set_title(leg_titles[leg])
        ax.set_xlabel("Ordered patch progress within leg [-]")
        ax.set_ylabel("Patch-averaged wall T [K]")
    if not any_data:
        plt.close(fig)
        return
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(f"{base_case_id}: latest-time axial wall-temperature profile")
    save_matplotlib_figure(fig, PACKAGE_DIR, f"{base_case_id}_axial_temperature_profile", dpi=220)
    plt.close(fig)


def write_plot_guide():
    lines = [
        "# Plot And Term Guide",
        "",
        "This document explains the main plots in `reports/2026-06-04_ethan_transient_axial_package/`, the quantities on those plots, and how they should be used in a scientific and numerical analysis.",
        "",
        "## Global terms",
        "",
        "- `TP1..TP6`: bulk-fluid temperature probes sampled in the loop.",
        "- `TW1..TW11`: wall-temperature stations. `TW10` is exported for transparency but remains excluded from RMSE scorecards elsewhere.",
        "- `|mdot| mean`: mean absolute loop mass flow from the monitored face zones.",
        "- `Ambient proxy`: derived ambient-like loss reconstructed from `wallHeatFlux.dat`, including passive loss channels and cooling-branch excess beyond the operating-point cooler duty.",
        "- `Net total Q`: signed all-wall total from `total_Q.dat`. A small late-time value means the residual enthalpy imbalance is small.",
        "- `Ordered patch progress`: normalized patch index from 0 to 1 within a leg. It preserves patch ordering but is not a geometric arc length.",
        "- `Nu`: patch-averaged Nusselt number from the reconstructed latest-time field when `foamPostProcess` could read `T` and `Nu` cleanly.",
        "",
        "## Plot guide",
        "",
    ]
    for name, payload in PLOT_GUIDE.items():
        lines.append(f"### `{name}`")
        lines.append("")
        lines.append(payload["focus"])
        lines.append("")
        lines.append("Terms:")
        for term in payload["terms"]:
            lines.append(f"- {term}")
        lines.append("")
    (PACKAGE_DIR / "plot_and_term_guide.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_scientific_analysis(case_rows, axial_audit_rows, representative_rows):
    full_success = [row for row in axial_audit_rows if row["extraction_status"] == "full_field_success"]
    partial = [row for row in axial_audit_rows if row["extraction_status"] == "partial_field_success"]
    q_only = [row for row in axial_audit_rows if row["extraction_status"] == "q_only_fallback"]
    lines = [
        "# Scientific And Numerical Analysis",
        "",
        f"Generated: `{iso_timestamp()}`",
        "",
        "## Scope",
        "",
        "This report audits the transient and axial package from both a scientific and a numerical perspective.",
        "",
        "## Axial extraction audit",
        "",
        f"- Full latest-time `T/Nu/q` patch extraction succeeded for `{len(full_success)}` case(s).",
        f"- Partial latest-time field extraction succeeded for `{len(partial)}` case(s).",
        f"- `{len(q_only)}` case(s) are currently q-only fallbacks because reconstructed `T` could not be read robustly by `foamPostProcess`.",
        "- The recurring failure mode is a malformed reconstructed `T` file with a scalar read error. That is a postprocessing/readability issue, not evidence that the wallHeatFlux histories themselves are invalid.",
        "",
        "## Scientific interpretation",
        "",
        "- The transient products confirm that the strongest numerical steadiness evidence is in Salt 2, Salt 3, and Salt 4 Kirst; Salt 4 Jin remains usable but more cautionary; Salt 1 remains the weakest salt family on practical steady-state credibility.",
        "- The axial q-based reductions remain scientifically useful even where reconstructed `T` fails. They still localize where heat is added, removed, and lost along each leg and they align with the section-transport conclusion that the upper leg and junction-region channels are the main remaining sensitivity areas.",
        "- The metric-coverage audit matters: the active Salt 2 continuation has wallHeatFlux data deeper into time than the continued TP/TW histories, so thermal-balance claims can be fresher than probe-history claims for that case.",
        "",
        "## Numerical interpretation",
        "",
        "- Use `case_audit_summary.csv` for slope-based late-window checks. A small `last_window_slope_per_s` and a small late-time `Net total Q` support practical steady-state use, even if the coded convergence flag never fired.",
        "- Use `metric_coverage_end_times.csv` before comparing tails across cases. Do not over-interpret one metric as if every metric extended to the same latest time.",
        "- Treat axial `Nu` and patch-averaged wall temperature as conditional diagnostics until the reconstructed-`T` read path is made uniformly reliable.",
        "",
        "## Representative groups",
        "",
    ]
    for row in representative_rows:
        lines.append(f"- `{row['base_case_id']}`: manuscript representative `{row.get('primary_manuscript_representative') or 'none yet'}`; sensitivity set `{row.get('sensitivity_rows', '')}`")
    lines.extend(["", "## Case-by-case audit", ""])
    for row in case_rows:
        lines.append(f"### `{row['source_id']}`")
        lines.append("")
        lines.append(f"- Run state: `run_status={row['run_status']}`, `essential_steadiness_class={row['essential_steadiness_class']}`, `usable_for_steady_state_now={row['usable_for_steady_state_now']}`.")
        lines.append(f"- Metric coverage ends: `mdot={row['mdot_time_end_s']}` s, `TP mean={row['tp_time_end_s']}` s, `TW5={row['tw5_time_end_s']}` s, `ambient proxy={row['ambient_time_end_s']}` s, `total_Q={row['total_q_time_end_s']}` s.")
        lines.append(f"- Validation context: `exp_all_temp_rmse_k={row['exp_all_temp_rmse_k']}`, `exp_mdot_abs_error_pct={row['exp_mdot_abs_error_pct']}`, `exp_q_external_loss_abs_error_pct={row['exp_q_external_loss_abs_error_pct']}`.")
        lines.append(f"- Hydraulic context: `upper_leg_abs_delta_p_rgh_pa={row['upper_leg_abs_delta_p_rgh_pa']}`, `left_leg_abs_delta_p_rgh_pa={row['left_leg_abs_delta_p_rgh_pa']}`, `right_leg_abs_delta_p_rgh_pa={row['right_leg_abs_delta_p_rgh_pa']}`.")
        lines.append(f"- Axial extraction: `status={row['axial_extraction_status']}`, `patches_with_areaAverage_T={row['patches_with_areaAverage_T']}`, `patches_with_areaAverage_Nu={row['patches_with_areaAverage_Nu']}`.")
        error_text = str(row.get("axial_field_extraction_error", "")).strip()
        if error_text:
            lines.append(f"- Axial extraction caveat: `{error_text}`.")
        lines.append("")
    lines.extend([
        "## Recommended next analytical moves",
        "",
        "- Keep using the q-based axial products immediately; they are already strong enough for manuscript-facing discussion of where heat is added, removed, and lost.",
        "- Treat `T/Nu`-based axial interpretation as a second-stage refinement that needs a cleaner reconstructed-field path, likely on a compute-node postprocessing route or with a more targeted reconstruction workflow.",
        "- Pair `metric_coverage_end_times.csv` with `case_audit_summary.csv` whenever late-time behavior is discussed so the numerical evidence is honest about mixed metric horizons.",
    ])
    (PACKAGE_DIR / "scientific_numerical_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ensure_dir(PACKAGE_DIR)
    transient_rows = load_csv_rows(TIMESERIES_CSV)
    last_window_rows = load_csv_rows(LAST_WINDOW_CSV)
    axial_rows = load_csv_rows(AXIAL_LATEST_CSV)
    status_map = {row["source_id"]: row for row in load_csv_rows(STATUS_CSV) if row.get("source_id")}
    validation_map = {row["source_id"]: row for row in load_csv_rows(VALIDATION_CSV) if row.get("source_id")}
    pressure_map = {row["source_id"]: row for row in load_csv_rows(PRESSURE_CSV) if row.get("source_id")}
    representative_rows = [row for row in load_csv_rows(REPRESENTATIVE_CSV) if row.get("base_case_id")]
    if not transient_rows or not axial_rows:
        raise SystemExit("Transient/axial base package is incomplete; run build_ethan_transient_axial_package.py first.")
    coverage_rows = build_metric_coverage_rows(transient_rows, last_window_rows, status_map)
    axial_audit_rows = build_axial_extraction_audit_rows(axial_rows, status_map)
    case_rows = build_case_audit_summary(status_map, validation_map, pressure_map, coverage_rows, axial_audit_rows)
    csv_dump(PACKAGE_DIR / "metric_coverage_end_times.csv", list(coverage_rows[0].keys()), coverage_rows)
    csv_dump(PACKAGE_DIR / "axial_field_extraction_audit.csv", list(axial_audit_rows[0].keys()), axial_audit_rows)
    csv_dump(PACKAGE_DIR / "case_audit_summary.csv", list(case_rows[0].keys()), case_rows)
    lookup = build_timeseries_lookup(transient_rows)
    plot_metric_coverage(coverage_rows)
    for row in representative_rows:
        case_ids = [item.strip() for item in str(row.get("sensitivity_rows", "")).split(";") if item.strip()]
        case_ids = [case_id for case_id in case_ids if case_id in status_map]
        if not case_ids:
            continue
        plot_transient_tail(str(row["base_case_id"]), case_ids, lookup, status_map)
        plot_axial_temperature(str(row["base_case_id"]), case_ids, axial_rows, status_map)
    write_plot_guide()
    write_scientific_analysis(case_rows, axial_audit_rows, representative_rows)
    payload = {
        "generated_at": iso_timestamp(),
        "metric_coverage_row_count": len(coverage_rows),
        "axial_field_extraction_audit_row_count": len(axial_audit_rows),
        "case_audit_summary_row_count": len(case_rows),
    }
    (PACKAGE_DIR / "transient_axial_audit_summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
