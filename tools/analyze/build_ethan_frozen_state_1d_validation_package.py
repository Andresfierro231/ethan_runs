#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TMP_MPL_ROOT = ROOT / "tmp" / "mplconfig"
TMP_MPL_ROOT.mkdir(parents=True, exist_ok=True)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float, load_csv_rows, write_json
from tools.common import ensure_dir, iso_timestamp, save_matplotlib_figure

DEFAULT_FROZEN_DIR = ROOT / "reports" / "2026-06-22_ethan_frozen_state_results"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-23_ethan_frozen_state_1d_validation"
PRESENTATION_DIR = ROOT / "reports" / "2026-06-23_presentation"
SCENARIO_ORDER = [
    "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_0",
    "ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1",
    "ethan_cfd_informed_salt_baseline_ins_2.0in_rad_1",
    "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_0",
    "ethan_cfd_informed_salt_hybrid_ins_1.0in_rad_1",
    "ethan_cfd_informed_salt_hybrid_ins_2.0in_rad_1",
]
SENSOR_PATTERN = re.compile(r"^(TP|TW)(\d+)$")
FROZEN_CASE_PATTERN = re.compile(r"^(Salt \d+)")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local Salt frozen-CFD-vs-readable-1D validation package "
            "using the June 22 frozen-state contract and the current readable "
            "1D diagnostics."
        )
    )
    parser.add_argument("--frozen-dir", default=str(DEFAULT_FROZEN_DIR))
    parser.add_argument("--one-d-status-csv")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--import-manifest-path",
        default=str(ROOT / "imports" / "2026-06-23_ethan_frozen_state_1d_validation.json"),
    )
    return parser.parse_args()


def scenario_sort_key(scenario: str) -> tuple[int, str]:
    try:
        return (SCENARIO_ORDER.index(scenario), scenario)
    except ValueError:
        return (len(SCENARIO_ORDER), scenario)


def load_plotting_modules() -> tuple[Any, Any]:
    os.environ.setdefault("MPLCONFIGDIR", str(TMP_MPL_ROOT))
    import matplotlib.pyplot as plt  # type: ignore
    import numpy as np  # type: ignore

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.style.use("ggplot")
    return plt, np


def case_family_from_label(label: str) -> str:
    match = FROZEN_CASE_PATTERN.match(label.strip())
    if not match:
        return label.strip()
    return match.group(1)


def package_label(path: Path) -> str:
    return path.name


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_rmse(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(math.sqrt(sum(value * value for value in payload) / len(payload)))


def safe_mae(values: list[float]) -> float:
    payload = [abs(value) for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(sum(payload) / len(payload))


def safe_max_abs(values: list[float]) -> float:
    payload = [abs(value) for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return float(max(payload))


def sensor_sort_key(label: str) -> tuple[str, int]:
    match = SENSOR_PATTERN.match(label)
    if not match:
        return (label, 0)
    return (match.group(1), int(match.group(2)))


def summary_csv_to_validation_csv(path: Path) -> Path:
    return path.with_name("validation_table.csv")


def summary_csv_to_segment_csv(path: Path) -> Path:
    return path.with_name("segment_states.csv")


def build_sensor_reference_rows(
    *,
    frozen_case_label: str,
    source_id: str,
    boundary_rows: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in boundary_rows:
        label = str(row.get("landmark_label", "")).strip()
        if SENSOR_PATTERN.match(label):
            grouped[label].append(row)

    sensor_rows: list[dict[str, Any]] = []
    sensor_lookup: dict[str, dict[str, Any]] = {}
    for label in sorted(grouped.keys(), key=sensor_sort_key):
        kind = "TP" if label.startswith("TP") else "TW"
        payload = grouped[label]
        ref_field = "t_core_k" if kind == "TP" else "t_wall_area_avg_k"
        ref_values = [finite_float(row.get(ref_field)) for row in payload]
        alt_bulk_values = [finite_float(row.get("bulk_temp_fluid_area_avg_k")) for row in payload]
        wall_values = [finite_float(row.get("t_wall_area_avg_k")) for row in payload]
        reference_k = safe_mean(ref_values)
        sensor_row = {
            "frozen_case_label": frozen_case_label,
            "source_id": source_id,
            "sensor": label,
            "kind": kind,
            "reference_k": reference_k,
            "time_sample_count": len(payload),
            "bulk_proxy_k": safe_mean(alt_bulk_values),
            "wall_proxy_k": safe_mean(wall_values),
            "reference_source_field": ref_field,
        }
        sensor_rows.append(sensor_row)
        sensor_lookup[label] = sensor_row
    return sensor_rows, sensor_lookup


def frozen_case_mdot(branch_rows: list[dict[str, str]]) -> float:
    preferred = [row for row in branch_rows if row.get("branch_name") == "lower_leg"]
    source_rows = preferred if preferred else branch_rows
    values = [finite_float(row.get("mean_mdot_mean_abs_kg_s")) for row in source_rows]
    return safe_mean(values)


def load_frozen_case_context(row: dict[str, str], *, frozen_dir: Path) -> dict[str, Any]:
    package_root = Path(row["package_root"])
    boundary_rows = load_csv_rows(package_root / "boundary_layer_landmark_summary.csv")
    branch_rows = load_csv_rows(package_root / "branch_thermal_summary.csv")
    branch_profile_rows = load_csv_rows(package_root / "branch_thermal_profiles.csv")
    heat_rows = load_csv_rows(package_root / "heat_loss_summary.csv")
    behavior_rows = load_csv_rows(frozen_dir / "branch_behavior_summary.csv")
    behavior_lookup = {item["branch_name"]: item for item in behavior_rows}
    sensor_rows, sensor_lookup = build_sensor_reference_rows(
        frozen_case_label=row["case_label"],
        source_id=row["source_id"],
        boundary_rows=boundary_rows,
    )
    heat_row = heat_rows[0]
    return {
        "source_id": row["source_id"],
        "frozen_case_label": row["case_label"],
        "case_family": case_family_from_label(row["case_label"]),
        "comparison_ready": row["comparison_ready"],
        "run_status": row["run_status"],
        "package_root": str(package_root),
        "late_window_time_start_s": finite_float(row.get("late_window_time_start_s")),
        "late_window_time_end_s": finite_float(row.get("late_window_time_end_s")),
        "late_window_time_count": finite_float(row.get("late_window_time_count")),
        "sensor_reference_rows": sensor_rows,
        "sensor_reference_lookup": sensor_lookup,
        "branch_rows": branch_rows,
        "branch_profile_rows": branch_profile_rows,
        "branch_behavior_lookup": behavior_lookup,
        "cfd_removed_w": finite_float(heat_row.get("cooling_branch_total_removal_w")),
        "cfd_ambient_w": finite_float(heat_row.get("ambient_proxy_w")),
        "cfd_heater_w": finite_float(heat_row.get("section_heater_net_q_w")),
        "cfd_net_total_q_pct_of_heater": finite_float(heat_row.get("net_total_q_pct_of_heater")),
        "cfd_mdot_kg_s": frozen_case_mdot(branch_rows),
    }


def load_one_d_context(row: dict[str, str]) -> dict[str, Any]:
    summary_path = Path(row["source_summary_csv"])
    summary_row = load_csv_rows(summary_path)[0]
    validation_rows = load_csv_rows(summary_csv_to_validation_csv(summary_path))
    segment_rows = load_csv_rows(summary_csv_to_segment_csv(summary_path))
    return {
        "case_label": row["case_label"],
        "scenario": row["scenario"],
        "summary_path": str(summary_path),
        "summary_row": summary_row,
        "validation_rows": validation_rows,
        "segment_rows": segment_rows,
    }


def scenario_family(summary_row: dict[str, str]) -> str:
    mode = str(summary_row.get("profile_descriptor_mode", ""))
    return "hybrid" if mode == "ethan_cfd_informed_salt_v1" else "baseline"


def closure_stack_label(summary_row: dict[str, str]) -> str:
    descriptor = str(summary_row.get("profile_descriptor_mode", ""))
    htc_mode = str(summary_row.get("internal_htc_mode", ""))
    ins = str(summary_row.get("insulation_thickness_in", ""))
    rad = str(summary_row.get("radiation_on", ""))
    return f"{descriptor}|{htc_mode}|ins={ins}|rad={rad}"


def compare_sensor_tables(
    *,
    frozen_context: dict[str, Any],
    one_d_context: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    lookup = frozen_context["sensor_reference_lookup"]
    sensor_rows: list[dict[str, Any]] = []
    tp_errors: list[float] = []
    tw_errors: list[float] = []

    for row in one_d_context["validation_rows"]:
        sensor = str(row.get("sensor", "")).strip()
        if sensor not in lookup:
            continue
        reference_row = lookup[sensor]
        predicted_k = finite_float(row.get("predicted_K"))
        reference_k = finite_float(reference_row.get("reference_k"))
        if not math.isfinite(predicted_k) or not math.isfinite(reference_k):
            continue
        error_k = predicted_k - reference_k
        sensor_row = {
            "frozen_case_label": frozen_context["frozen_case_label"],
            "frozen_source_id": frozen_context["source_id"],
            "comparison_class": frozen_context["comparison_ready"],
            "one_d_case_label": one_d_context["case_label"],
            "scenario": one_d_context["scenario"],
            "sensor": sensor,
            "kind": reference_row["kind"],
            "predicted_k": predicted_k,
            "frozen_reference_k": reference_k,
            "error_k": error_k,
            "abs_error_k": abs(error_k),
            "frozen_reference_source_field": reference_row["reference_source_field"],
            "validation_predicted_source_kind": row.get("prediction_source_kind", ""),
        }
        sensor_rows.append(sensor_row)
        if reference_row["kind"] == "TP":
            tp_errors.append(error_k)
        else:
            tw_errors.append(error_k)

    return sensor_rows, {
        "tp_rmse_k": safe_rmse(tp_errors),
        "tp_mae_k": safe_mae(tp_errors),
        "tp_max_abs_k": safe_max_abs(tp_errors),
        "tp_count": float(len(tp_errors)),
        "tw_rmse_k": safe_rmse(tw_errors),
        "tw_mae_k": safe_mae(tw_errors),
        "tw_max_abs_k": safe_max_abs(tw_errors),
        "tw_count": float(len(tw_errors)),
    }


def compare_case_pair(
    *,
    frozen_context: dict[str, Any],
    one_d_context: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary_row = one_d_context["summary_row"]
    sensor_rows, sensor_metrics = compare_sensor_tables(
        frozen_context=frozen_context,
        one_d_context=one_d_context,
    )
    one_d_removed_w = finite_float(summary_row.get("qhx_total_W"))
    one_d_ambient_w = finite_float(summary_row.get("qambient_total_W"))
    one_d_total_loss_w = one_d_removed_w + one_d_ambient_w
    cfd_total_loss_w = frozen_context["cfd_removed_w"] + frozen_context["cfd_ambient_w"]
    heater_w = frozen_context["cfd_heater_w"]
    energy_error_w = one_d_total_loss_w - cfd_total_loss_w
    cooling_error_w = one_d_removed_w - frozen_context["cfd_removed_w"]
    ambient_error_w = one_d_ambient_w - frozen_context["cfd_ambient_w"]
    mass_flow_error_pct = (
        100.0 * abs(finite_float(summary_row.get("mdot_kg_s")) - frozen_context["cfd_mdot_kg_s"]) / abs(frozen_context["cfd_mdot_kg_s"])
        if math.isfinite(frozen_context["cfd_mdot_kg_s"]) and frozen_context["cfd_mdot_kg_s"] != 0.0
        else math.nan
    )
    pair_row = {
        "frozen_case_label": frozen_context["frozen_case_label"],
        "frozen_source_id": frozen_context["source_id"],
        "case_family": frozen_context["case_family"],
        "comparison_class": frozen_context["comparison_ready"],
        "one_d_case_label": one_d_context["case_label"],
        "scenario": one_d_context["scenario"],
        "scenario_family": scenario_family(summary_row),
        "closure_stack_label": closure_stack_label(summary_row),
        "internal_htc_mode": summary_row.get("internal_htc_mode", ""),
        "profile_descriptor_mode": summary_row.get("profile_descriptor_mode", ""),
        "insulation_thickness_in": finite_float(summary_row.get("insulation_thickness_in")),
        "radiation_on": summary_row.get("radiation_on", ""),
        "accepted_for_validation": summary_row.get("accepted_for_validation", ""),
        "validity_status": summary_row.get("validity_status", ""),
        "current_evidence_status": summary_row.get("current_evidence_status", ""),
        "one_d_removed_w": one_d_removed_w,
        "one_d_ambient_w": one_d_ambient_w,
        "one_d_total_loss_w": one_d_total_loss_w,
        "cfd_removed_w": frozen_context["cfd_removed_w"],
        "cfd_ambient_w": frozen_context["cfd_ambient_w"],
        "cfd_total_loss_w": cfd_total_loss_w,
        "cfd_heater_w": heater_w,
        "energy_error_w": energy_error_w,
        "energy_error_pct_of_heater": 100.0 * abs(energy_error_w) / abs(heater_w) if math.isfinite(heater_w) and heater_w != 0.0 else math.nan,
        "cooling_error_w": cooling_error_w,
        "cooling_error_pct_of_heater": 100.0 * abs(cooling_error_w) / abs(heater_w) if math.isfinite(heater_w) and heater_w != 0.0 else math.nan,
        "ambient_error_w": ambient_error_w,
        "ambient_error_pct_of_heater": 100.0 * abs(ambient_error_w) / abs(heater_w) if math.isfinite(heater_w) and heater_w != 0.0 else math.nan,
        "one_d_mdot_kg_s": finite_float(summary_row.get("mdot_kg_s")),
        "cfd_mdot_kg_s": frozen_context["cfd_mdot_kg_s"],
        "mass_flow_relative_error_pct_vs_cfd": mass_flow_error_pct,
        "tp_rmse_k": sensor_metrics["tp_rmse_k"],
        "tp_mae_k": sensor_metrics["tp_mae_k"],
        "tp_max_abs_k": sensor_metrics["tp_max_abs_k"],
        "tp_count": int(sensor_metrics["tp_count"]),
        "tw_rmse_k": sensor_metrics["tw_rmse_k"],
        "tw_mae_k": sensor_metrics["tw_mae_k"],
        "tw_max_abs_k": sensor_metrics["tw_max_abs_k"],
        "tw_count": int(sensor_metrics["tw_count"]),
    }
    return pair_row, sensor_rows


def aggregate_branch_profiles(
    *,
    frozen_contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    for context in frozen_contexts:
        grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
        for row in context["branch_profile_rows"]:
            branch_name = str(row.get("branch_name", ""))
            if not branch_name:
                continue
            grouped[(branch_name, int(float(row["branch_profile_index"])))].append(row)
        for (branch_name, profile_index), group in sorted(grouped.items()):
            sample_row = group[0]
            behavior = context["branch_behavior_lookup"].get(branch_name, {})
            output_rows.append(
                {
                    "frozen_case_label": context["frozen_case_label"],
                    "frozen_source_id": context["source_id"],
                    "comparison_class": context["comparison_ready"],
                    "branch_name": branch_name,
                    "branch_profile_index": profile_index,
                    "branch_s_fraction": finite_float(sample_row.get("branch_s_fraction")),
                    "branch_s_mid_m": safe_mean([finite_float(row.get("branch_s_mid_m")) for row in group]),
                    "mean_bulk_temp_k": safe_mean([finite_float(row.get("bulk_temp_fluid_area_avg_k")) for row in group]),
                    "mean_wall_temp_k": safe_mean([finite_float(row.get("t_wall_area_avg_k")) for row in group]),
                    "mean_effective_htc_w_m2_k": safe_mean([finite_float(row.get("effective_htc_w_m2_k")) for row in group]),
                    "mean_effective_ua_per_m_w_m_k": safe_mean([finite_float(row.get("effective_ua_per_m_w_m_k")) for row in group]),
                    "mean_mdot_kg_s": safe_mean([finite_float(row.get("mdot_mean_abs_kg_s")) for row in group]),
                    "fit_status": behavior.get("dominant_fit_status", ""),
                    "domain_note": behavior.get("domain_note", ""),
                    "modeling_note": behavior.get("modeling_note", ""),
                }
            )
    return output_rows


def rank_scenarios(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_rows = [row for row in case_rows if row["comparison_class"] == "comparison_candidate"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary_rows:
        grouped[row["scenario"]].append(row)

    scenario_rows: list[dict[str, Any]] = []
    for scenario, rows in sorted(grouped.items(), key=lambda item: scenario_sort_key(item[0])):
        temp_errors = [finite_float(row.get("tp_rmse_k")) for row in rows]
        wall_errors = [finite_float(row.get("tw_rmse_k")) for row in rows]
        energy_errors = [finite_float(row.get("energy_error_pct_of_heater")) for row in rows]
        flow_errors = [finite_float(row.get("mass_flow_relative_error_pct_vs_cfd")) for row in rows]
        summary_row = {
            "scenario": scenario,
            "comparison_pair_count": len(rows),
            "scenario_family": rows[0]["scenario_family"],
            "closure_stack_label": rows[0]["closure_stack_label"],
            "internal_htc_mode": rows[0]["internal_htc_mode"],
            "profile_descriptor_mode": rows[0]["profile_descriptor_mode"],
            "insulation_thickness_in": rows[0]["insulation_thickness_in"],
            "radiation_on": rows[0]["radiation_on"],
            "mean_energy_error_pct_of_heater": safe_mean(energy_errors),
            "mean_tw_rmse_k": safe_mean(wall_errors),
            "mean_tp_rmse_k": safe_mean(temp_errors),
            "mean_mass_flow_relative_error_pct_vs_cfd": safe_mean(flow_errors),
            "all_rows_accepted_for_validation": all(str(row.get("accepted_for_validation", "")).lower() == "true" for row in rows),
        }
        scenario_rows.append(summary_row)

    if not scenario_rows:
        return scenario_rows

    for key in (
        "mean_energy_error_pct_of_heater",
        "mean_tw_rmse_k",
        "mean_tp_rmse_k",
        "mean_mass_flow_relative_error_pct_vs_cfd",
    ):
        values = [finite_float(row.get(key)) for row in scenario_rows]
        finite_values = [value for value in values if math.isfinite(value)]
        scale = max(finite_values) if finite_values else math.nan
        for row in scenario_rows:
            value = finite_float(row.get(key))
            normalized = value / scale if math.isfinite(value) and math.isfinite(scale) and scale > 0.0 else math.nan
            row[f"{key}_normalized"] = normalized

    for row in scenario_rows:
        composite_terms = [
            finite_float(row.get("mean_energy_error_pct_of_heater_normalized")),
            finite_float(row.get("mean_tw_rmse_k_normalized")),
            finite_float(row.get("mean_tp_rmse_k_normalized")),
            finite_float(row.get("mean_mass_flow_relative_error_pct_vs_cfd_normalized")),
        ]
        row["composite_score"] = safe_mean(composite_terms)

    scenario_rows.sort(key=lambda item: (finite_float(item.get("composite_score"), math.inf), scenario_sort_key(item["scenario"])))
    for index, row in enumerate(scenario_rows, start=1):
        row["composite_rank"] = index
    return scenario_rows


def best_rows_by_reference(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_rows = [row for row in case_rows if row["comparison_class"] == "comparison_candidate"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary_rows:
        grouped[row["frozen_case_label"]].append(row)

    output_rows: list[dict[str, Any]] = []
    metrics = {
        "best_overall_scenario": "composite_proxy",
        "best_energy_scenario": "energy_error_pct_of_heater",
        "best_wall_scenario": "tw_rmse_k",
        "best_centerline_scenario": "tp_rmse_k",
        "best_mass_flow_scenario": "mass_flow_relative_error_pct_vs_cfd",
    }
    for frozen_case_label, rows in sorted(grouped.items()):
        working_rows: list[dict[str, Any]] = []
        for row in rows:
            composite_proxy = safe_mean(
                [
                    finite_float(row.get("energy_error_pct_of_heater")),
                    finite_float(row.get("tw_rmse_k")),
                    finite_float(row.get("tp_rmse_k")),
                    finite_float(row.get("mass_flow_relative_error_pct_vs_cfd")),
                ]
            )
            row_with_proxy = dict(row)
            row_with_proxy["composite_proxy"] = composite_proxy
            working_rows.append(row_with_proxy)
        best_row: dict[str, Any] = {
            "frozen_case_label": frozen_case_label,
            "case_family": working_rows[0]["case_family"],
            "comparison_pair_count": len(working_rows),
        }
        for output_key, metric_key in metrics.items():
            chosen = min(working_rows, key=lambda item: finite_float(item.get(metric_key), math.inf))
            best_row[output_key] = chosen["scenario"]
        output_rows.append(best_row)
    return output_rows


def build_readme(
    *,
    frozen_dir: Path,
    scenario_rows: list[dict[str, Any]],
    best_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
) -> str:
    if scenario_rows:
        best_full = scenario_rows[0]
        best_note = (
            f"Best full-coverage readable scenario on the primary frozen set: "
            f"`{best_full['scenario']}` with mean |energy| `{best_full['mean_energy_error_pct_of_heater']:.2f}%` "
            f"of heater, mean TW RMSE `{best_full['mean_tw_rmse_k']:.2f} K`, mean TP RMSE "
            f"`{best_full['mean_tp_rmse_k']:.2f} K`, and mean mass-flow error "
            f"`{best_full['mean_mass_flow_relative_error_pct_vs_cfd']:.2f}%`."
        )
    else:
        best_note = "No primary-set readable scenario ranking was available."

    hybrid_primary_rows = [row for row in comparison_rows if row["comparison_class"] == "comparison_candidate" and row["scenario_family"] == "hybrid"]
    hybrid_note = (
        f"Hybrid/profile-descriptor scenarios reached only `{len(hybrid_primary_rows)}` primary comparison rows, "
        "so they remain under-covered relative to the baseline family."
        if hybrid_primary_rows
        else "No hybrid/profile-descriptor rows were readable on the primary comparison set."
    )
    best_case_lines = []
    for row in best_rows:
        best_case_lines.append(
            f"- {row['frozen_case_label']}: overall `{row['best_overall_scenario']}`, "
            f"energy `{row['best_energy_scenario']}`, TW `{row['best_wall_scenario']}`, "
            f"TP `{row['best_centerline_scenario']}`, mdot `{row['best_mass_flow_scenario']}`"
        )
    best_case_block = "\n".join(best_case_lines) if best_case_lines else "- none"
    return f"""# Ethan Frozen-State 1D Validation

Generated: `{iso_timestamp()}`

## Scope

- This package compares the current readable Salt 1D diagnostics against the
  `{package_label(frozen_dir)}` CFD contract.
- Primary comparison set: frozen CFD rows labeled `comparison_candidate`.
- Provisional appendix: frozen CFD rows labeled `convergence_audit_required`.
- Straight sections are not assumed fully developed by default.
- `upcomer` remains a separate modeling problem, and `right_leg` / downcomer
  remains blocked for direct internal `Nu`.

## Current best readable picture

- {best_note}
- {hybrid_note}
- Because the current readable external replay still comes from the June 19
  `ethan_cfd_informed_salt_v1` bundle, these results should be treated as the
  best current local scoring surface rather than a final refreshed-closure
  replay.

## Per-reference winners on the primary set

{best_case_block}

## Heat-loss contract used here

- Compare `Q_lost = Q_removed + Q_ambient` on both sides.
- CFD side:
  `cooling_branch_total_removal_w + ambient_proxy_w`.
- 1D side:
  `qhx_total_W + qambient_total_W`.
- Do not infer a hidden cooler `h`, and do not double-count `ambient_proxy_w`.
"""


def plot_scenario_heatmap(rows: list[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    plt, np = load_plotting_modules()
    metrics = [
        ("mean_energy_error_pct_of_heater", "Energy [% heater]"),
        ("mean_tw_rmse_k", "TW RMSE [K]"),
        ("mean_tp_rmse_k", "TP RMSE [K]"),
        ("mean_mass_flow_relative_error_pct_vs_cfd", "mdot err [%]"),
    ]
    scenarios = [row["scenario"] for row in rows]
    data = np.array([[finite_float(row.get(metric_key)) for metric_key, _ in metrics] for row in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(10.5, max(3.0, 0.7 * len(rows) + 1.5)))
    image = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels([label for _, label in metrics], rotation=20, ha="right")
    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels(scenarios)
    ax.set_title("Primary frozen-set scenario ranking metrics")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = data[i, j]
            if math.isfinite(float(value)):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(image, ax=ax, shrink=0.85)
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "primary_scenario_metric_heatmap")


def plot_best_sensor_parity(
    *,
    best_case_rows: list[dict[str, Any]],
    sensor_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    plt, _np = load_plotting_modules()
    best_lookup = {row["frozen_case_label"]: row["best_overall_scenario"] for row in best_case_rows}
    selected = [
        row
        for row in sensor_rows
        if row["frozen_case_label"] in best_lookup and row["scenario"] == best_lookup[row["frozen_case_label"]]
    ]
    fig, ax = plt.subplots(figsize=(7.5, 7.0))
    colors = {"TP": "#1f77b4", "TW": "#d62728"}
    for kind in ("TP", "TW"):
        payload = [row for row in selected if row["kind"] == kind]
        if not payload:
            continue
        ax.scatter(
            [row["frozen_reference_k"] for row in payload],
            [row["predicted_k"] for row in payload],
            label=kind,
            color=colors[kind],
            alpha=0.8,
        )
    all_values = [row["frozen_reference_k"] for row in selected] + [row["predicted_k"] for row in selected]
    lower = min(all_values) if all_values else 0.0
    upper = max(all_values) if all_values else 1.0
    ax.plot([lower, upper], [lower, upper], color="0.2", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Frozen CFD reference [K]")
    ax.set_ylabel("1D prediction [K]")
    ax.set_title("Best-overall readable scenario parity on primary frozen references")
    ax.legend(loc="best")
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "primary_best_sensor_parity")


def plot_best_energy_partition(
    *,
    best_case_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    plt, np = load_plotting_modules()
    selected_rows = []
    best_lookup = {row["frozen_case_label"]: row["best_overall_scenario"] for row in best_case_rows}
    for row in comparison_rows:
        if row["comparison_class"] == "comparison_candidate" and row["scenario"] == best_lookup.get(row["frozen_case_label"]):
            selected_rows.append(row)
    selected_rows.sort(key=lambda item: item["frozen_case_label"])
    labels = [row["frozen_case_label"] for row in selected_rows]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    ax.bar(x - width / 2, [row["cfd_removed_w"] for row in selected_rows], width, label="CFD removed", color="#4c78a8")
    ax.bar(x - width / 2, [row["cfd_ambient_w"] for row in selected_rows], width, bottom=[row["cfd_removed_w"] for row in selected_rows], label="CFD ambient", color="#9ecae9")
    ax.bar(x + width / 2, [row["one_d_removed_w"] for row in selected_rows], width, label="1D removed", color="#f58518")
    ax.bar(x + width / 2, [row["one_d_ambient_w"] for row in selected_rows], width, bottom=[row["one_d_removed_w"] for row in selected_rows], label="1D ambient", color="#ffbf79")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10)
    ax.set_ylabel("Heat loss [W]")
    ax.set_title("Primary frozen-set heat partition: best-overall readable scenario")
    ax.legend(loc="best", ncol=2)
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "primary_best_energy_partition")


def plot_best_mass_flow(
    *,
    best_case_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    plt, np = load_plotting_modules()
    best_lookup = {row["frozen_case_label"]: row["best_overall_scenario"] for row in best_case_rows}
    selected_rows = [
        row
        for row in comparison_rows
        if row["comparison_class"] == "comparison_candidate" and row["scenario"] == best_lookup.get(row["frozen_case_label"])
    ]
    selected_rows.sort(key=lambda item: item["frozen_case_label"])
    labels = [row["frozen_case_label"] for row in selected_rows]
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(x - width / 2, [row["cfd_mdot_kg_s"] for row in selected_rows], width, label="Frozen CFD", color="#4c78a8")
    ax.bar(x + width / 2, [row["one_d_mdot_kg_s"] for row in selected_rows], width, label="1D", color="#f58518")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10)
    ax.set_ylabel("Mass flow [kg/s]")
    ax.set_title("Primary frozen-set mass flow comparison")
    ax.legend(loc="best")
    fig.tight_layout()
    return save_matplotlib_figure(fig, output_dir, "primary_best_mass_flow")


def plot_branch_development(
    *,
    branch_profile_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, str]:
    plt, _np = load_plotting_modules()
    primary_rows = [row for row in branch_profile_rows if row["comparison_class"] == "comparison_candidate"]
    case_order = sorted({row["frozen_case_label"] for row in primary_rows})
    fig, axes = plt.subplots(len(case_order), 1, figsize=(10.5, max(4.5, 3.2 * len(case_order))), squeeze=False)
    colors = {
        "left_lower_leg": "#1f77b4",
        "test_section_span": "#2ca02c",
        "left_upper_leg": "#9467bd",
        "upcomer": "#8c564b",
        "right_leg": "#d62728",
        "lower_leg": "#ff7f0e",
        "upper_leg": "#7f7f7f",
    }
    for axis, case_label in zip(axes.flat, case_order):
        payload = [row for row in primary_rows if row["frozen_case_label"] == case_label]
        branches = sorted({row["branch_name"] for row in payload})
        for branch_name in branches:
            branch_payload = sorted(
                [row for row in payload if row["branch_name"] == branch_name],
                key=lambda item: finite_float(item.get("branch_s_fraction")),
            )
            x_vals = [row["branch_s_fraction"] for row in branch_payload]
            bulk_vals = [row["mean_bulk_temp_k"] for row in branch_payload]
            wall_vals = [row["mean_wall_temp_k"] for row in branch_payload]
            color = colors.get(branch_name, None)
            axis.plot(x_vals, bulk_vals, color=color, linewidth=1.8, label=f"{branch_name} bulk")
            axis.plot(x_vals, wall_vals, color=color, linewidth=1.2, linestyle="--", label=f"{branch_name} wall")
        axis.set_title(case_label)
        axis.set_xlabel("branch progress fraction")
        axis.set_ylabel("Temperature [K]")
        axis.legend(loc="upper left", fontsize=7, ncol=2)
    fig.suptitle("Primary frozen-set branch development by case", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return save_matplotlib_figure(fig, output_dir, "primary_branch_development")


def write_import_manifest(
    *,
    frozen_dir: Path,
    one_d_status_csv: Path,
    import_manifest_path: Path | None,
    output_dir: Path,
    summary: dict[str, Any],
) -> None:
    if import_manifest_path is None:
        return
    payload = {
        "generated_at": iso_timestamp(),
        "package": output_dir.name,
        "summary": summary,
        "inputs": {
            "frozen_state_contract": str((frozen_dir / "frozen_state_contract.csv").resolve()),
            "frozen_state_readable_1d": str(one_d_status_csv.resolve()),
            "frozen_state_branch_behavior": str((frozen_dir / "branch_behavior_summary.csv").resolve()),
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "summary_json": str((output_dir / "summary.json").resolve()),
            "case_metric_summary_csv": str((output_dir / "case_metric_summary.csv").resolve()),
            "scenario_ranking_csv": str((output_dir / "scenario_ranking.csv").resolve()),
        },
    }
    write_json(import_manifest_path, payload)


def build_validation_package(
    *,
    frozen_dir: Path,
    one_d_status_csv: Path,
    output_dir: Path,
    import_manifest_path: Path | None,
) -> dict[str, Any]:
    frozen_rows = load_csv_rows(frozen_dir / "frozen_state_contract.csv")
    one_d_rows = load_csv_rows(one_d_status_csv)
    frozen_contexts = [load_frozen_case_context(row, frozen_dir=frozen_dir) for row in frozen_rows]
    one_d_contexts = [load_one_d_context(row) for row in one_d_rows]

    sensor_reference_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    sensor_error_rows: list[dict[str, Any]] = []
    for frozen_context in frozen_contexts:
        sensor_reference_rows.extend(frozen_context["sensor_reference_rows"])
        for one_d_context in one_d_contexts:
            if one_d_context["case_label"] != frozen_context["case_family"]:
                continue
            pair_row, pair_sensor_rows = compare_case_pair(
                frozen_context=frozen_context,
                one_d_context=one_d_context,
            )
            comparison_rows.append(pair_row)
            sensor_error_rows.extend(pair_sensor_rows)

    scenario_rows = rank_scenarios(comparison_rows)
    best_case_rows = best_rows_by_reference(comparison_rows)
    branch_profile_rows = aggregate_branch_profiles(frozen_contexts=frozen_contexts)

    csv_dump_rows(output_dir / "case_metric_summary.csv", comparison_rows)
    csv_dump_rows(output_dir / "sensor_error_summary.csv", sensor_error_rows)
    csv_dump_rows(output_dir / "cfd_sensor_reference.csv", sensor_reference_rows)
    csv_dump_rows(output_dir / "scenario_ranking.csv", scenario_rows)
    csv_dump_rows(output_dir / "best_case_scenarios.csv", best_case_rows)
    csv_dump_rows(output_dir / "cfd_branch_profile_summary.csv", branch_profile_rows)

    figures = {
        "primary_scenario_metric_heatmap": plot_scenario_heatmap(scenario_rows, output_dir),
        "primary_best_sensor_parity": plot_best_sensor_parity(
            best_case_rows=best_case_rows,
            sensor_rows=sensor_error_rows,
            output_dir=output_dir,
        ),
        "primary_best_energy_partition": plot_best_energy_partition(
            best_case_rows=best_case_rows,
            comparison_rows=comparison_rows,
            output_dir=output_dir,
        ),
        "primary_best_mass_flow": plot_best_mass_flow(
            best_case_rows=best_case_rows,
            comparison_rows=comparison_rows,
            output_dir=output_dir,
        ),
        "primary_branch_development": plot_branch_development(
            branch_profile_rows=branch_profile_rows,
            output_dir=output_dir,
        ),
    }

    summary = {
        "generated_at": iso_timestamp(),
        "frozen_reference_count": len(frozen_contexts),
        "primary_frozen_reference_count": sum(1 for row in frozen_contexts if row["comparison_ready"] == "comparison_candidate"),
        "comparison_row_count": len(comparison_rows),
        "sensor_error_row_count": len(sensor_error_rows),
        "scenario_count_primary": len(scenario_rows),
        "best_primary_scenario": scenario_rows[0]["scenario"] if scenario_rows else "",
        "best_primary_composite_score": finite_float(scenario_rows[0].get("composite_score")) if scenario_rows else math.nan,
        "best_case_count_primary": len(best_case_rows),
        "figure_stems": sorted(figures.keys()),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(
            frozen_dir=frozen_dir,
            scenario_rows=scenario_rows,
            best_rows=best_case_rows,
            comparison_rows=comparison_rows,
        ),
        encoding="utf-8",
    )
    write_import_manifest(
        frozen_dir=frozen_dir,
        one_d_status_csv=one_d_status_csv,
        import_manifest_path=import_manifest_path,
        output_dir=output_dir,
        summary=summary,
    )
    return summary


def main() -> int:
    args = parse_args()
    frozen_dir = Path(args.frozen_dir)
    output_dir = ensure_dir(Path(args.output_dir))
    one_d_status_csv = Path(args.one_d_status_csv) if args.one_d_status_csv else frozen_dir / "one_d_readable_status.csv"
    import_manifest_path = Path(args.import_manifest_path) if args.import_manifest_path else None
    build_validation_package(
        frozen_dir=frozen_dir,
        one_d_status_csv=one_d_status_csv,
        output_dir=output_dir,
        import_manifest_path=import_manifest_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
