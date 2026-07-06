#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from tools.common import ensure_dir, iso_timestamp
from tools.analyze.ethan_closure_modeling_v3_common import ROOT, csv_dump_rows, finite_float, load_csv_rows, write_json

NONDIM_DIR = ROOT / "reports" / "2026-06-17_ethan_nondimensional_dashboard_package"
STRAIGHT_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_straight_hydraulic_sensitivity_refresh"
THERMAL_DIR = ROOT / "reports" / "2026-06-19_ethan_salt_thermal_closure_hardening_v3"
FEATURE_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_feature_path_hydraulic_hardening_v2"
MODEL_DIR = ROOT / "reports" / "2026-06-22_ethan_salt_model_dependency_package_v4"
BLOCKER_DIR = ROOT / "reports" / "2026-06-19_ethan_blocker_report_and_followon_wave"
LITREV_HANDOFF_DIR = ROOT / "reports" / "2026-06-19_ethan_litrev_to_1d_modeling_handoff"
ONE_D_DIAG_DIR = (ROOT / ".." / "cfd-modeling-tools" / "tamu_first_order_model" / "Fluid" / "results" / "diagnostics" / "ethan_cfd_informed_salt_v1").resolve()
ONE_D_BUNDLE_SNAPSHOT = (
    ROOT
    / ".."
    / "cfd-modeling-tools"
    / "tamu_first_order_model"
    / "Fluid"
    / "validation_data"
    / "ethan_cfd_informed_salt_v1"
    / "closure_snapshot.json"
).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06-22_ethan_frozen_state_results"

BRANCH_ALIAS = {
    "left_lower_leg": "upcomer_direct_leg",
    "left_upper_leg": "upcomer_direct_leg",
    "test_section_span": "upcomer_direct_leg",
    "upcomer": "derived_upcomer",
    "right_leg": "downcomer",
    "lower_leg": "heater_leg",
    "upper_leg": "cooler_leg",
}

BRANCH_MODELING_NOTES = {
    "left_lower_leg": "Best current direct internal HTC and Nu evidence lane; use as the defended direct developing-flow thermal branch.",
    "left_upper_leg": "Carry as a primary UA' or HTC state-surface branch only; direct Nu is not yet defended.",
    "test_section_span": "Carry as a primary UA' or HTC state-surface branch only; direct Nu is not yet defended and entry effects remain active.",
    "upcomer": "Derived sensitivity-only branch; model separately from the straight direct branches and consider a convection-cell style closure coupled to the loop state.",
    "right_leg": "Downcomer return branch remains blocked for direct Nu; cooler-adjacent return observables are still missing.",
    "lower_leg": "Heating-dominant branch; direct thermal closure is not defended under the current residual and support gates.",
    "upper_leg": "Cooler-side branch; direct thermal closure remains blocked and should stay inside the residual bucket for now.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze the latest retained Salt data into a pseudo-steady results "
            "package that summarizes branch behavior, closure status, drift, data "
            "needs, and the current readable 1D replay status."
        )
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_mean(values: list[float]) -> float:
    payload = [value for value in values if math.isfinite(value)]
    if not payload:
        return math.nan
    return sum(payload) / len(payload)


def normalized_delta(latest: float, mean_value: float) -> float:
    if not math.isfinite(latest) or not math.isfinite(mean_value) or mean_value == 0.0:
        return math.nan
    return abs(latest - mean_value) / abs(mean_value)


def frozen_state_contract_rows(dashboard_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for row in dashboard_rows:
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["display_label"],
                "run_status": row["run_status"],
                "comparison_ready": row["comparison_ready"],
                "late_window_time_start_s": finite_float(row.get("late_window_time_start_s")),
                "late_window_time_end_s": finite_float(row.get("late_window_time_end_s")),
                "late_window_time_count": finite_float(row.get("late_window_time_count")),
                "primary_frozen_state_basis": "late_window_mean",
                "sensitivity_snapshot_basis": "latest_retained_time",
                "package_root": row["package_root"],
                "downcomer_to_upcomer_bulk_delta_k": finite_float(row.get("downcomer_to_upcomer_bulk_delta_k")),
                "heater_to_cooler_bulk_delta_k": finite_float(row.get("heater_to_cooler_bulk_delta_k")),
            }
        )
    return rows_out


def branch_behavior_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["branch_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for branch_name, group in sorted(grouped.items()):
        fit_used_count = sum(1 for row in group if row["fit_use_status"] == "fit_used")
        sensitivity_count = sum(1 for row in group if row["fit_use_status"] == "sensitivity_only")
        excluded_count = sum(1 for row in group if row["fit_use_status"] == "excluded")
        rows_out.append(
            {
                "branch_name": branch_name,
                "branch_alias": BRANCH_ALIAS.get(branch_name, branch_name),
                "case_count": len(group),
                "fit_used_case_count": fit_used_count,
                "sensitivity_only_case_count": sensitivity_count,
                "excluded_case_count": excluded_count,
                "mean_re_effective": safe_mean([finite_float(row.get("mean_re_effective")) for row in group]),
                "mean_nu_effective": safe_mean([finite_float(row.get("mean_nu_effective")) for row in group]),
                "mean_htc_effective_w_m2_k": safe_mean([finite_float(row.get("mean_htc_effective_w_m2_k")) for row in group]),
                "mean_support_fraction": safe_mean([finite_float(row.get("mean_support_fraction")) for row in group]),
                "mean_residual_fraction_of_wall_heat": safe_mean([finite_float(row.get("mean_residual_fraction_of_wall_heat")) for row in group]),
                "domain_note": group[0].get("domain_note", ""),
                "dominant_fit_status": Counter(row["fit_use_status"] for row in group).most_common(1)[0][0],
                "modeling_note": BRANCH_MODELING_NOTES.get(branch_name, ""),
            }
        )
    return rows_out


def branch_drift_rows(time_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in time_rows:
        grouped[(row["source_id"], row["branch_name"])].append(row)
    case_rows: list[dict[str, Any]] = []
    for (source_id, branch_name), group in sorted(grouped.items()):
        group.sort(key=lambda row: finite_float(row.get("time_s")))
        latest = group[-1]
        mean_nu = safe_mean([finite_float(row.get("nu_effective")) for row in group])
        mean_htc = safe_mean([finite_float(row.get("htc_effective_w_m2_k")) for row in group])
        mean_residual = safe_mean([finite_float(row.get("residual_fraction_of_wall_heat")) for row in group])
        latest_nu = finite_float(latest.get("nu_effective"))
        latest_htc = finite_float(latest.get("htc_effective_w_m2_k"))
        latest_residual = finite_float(latest.get("residual_fraction_of_wall_heat"))
        case_rows.append(
            {
                "source_id": source_id,
                "case_label": latest["case_label"],
                "branch_name": branch_name,
                "latest_time_s": finite_float(latest.get("time_s")),
                "time_row_count": len(group),
                "nu_mean": mean_nu,
                "nu_latest": latest_nu,
                "nu_latest_vs_mean_fraction": normalized_delta(latest_nu, mean_nu),
                "htc_mean_w_m2_k": mean_htc,
                "htc_latest_w_m2_k": latest_htc,
                "htc_latest_vs_mean_fraction": normalized_delta(latest_htc, mean_htc),
                "residual_mean_fraction": mean_residual,
                "residual_latest_fraction": latest_residual,
                "residual_latest_vs_mean_fraction": normalized_delta(latest_residual, mean_residual),
            }
        )
    return case_rows


def branch_drift_rollup(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["branch_name"]].append(row)
    rows_out: list[dict[str, Any]] = []
    for branch_name, group in sorted(grouped.items()):
        rows_out.append(
            {
                "branch_name": branch_name,
                "case_count": len(group),
                "mean_nu_latest_vs_mean_fraction": safe_mean([finite_float(row.get("nu_latest_vs_mean_fraction")) for row in group]),
                "max_nu_latest_vs_mean_fraction": max((finite_float(row.get("nu_latest_vs_mean_fraction")) for row in group), default=math.nan),
                "mean_htc_latest_vs_mean_fraction": safe_mean([finite_float(row.get("htc_latest_vs_mean_fraction")) for row in group]),
                "max_htc_latest_vs_mean_fraction": max((finite_float(row.get("htc_latest_vs_mean_fraction")) for row in group), default=math.nan),
                "mean_residual_latest_vs_mean_fraction": safe_mean([finite_float(row.get("residual_latest_vs_mean_fraction")) for row in group]),
                "max_residual_latest_vs_mean_fraction": max((finite_float(row.get("residual_latest_vs_mean_fraction")) for row in group), default=math.nan),
            }
        )
    return rows_out


def straight_summary_rows(fit_rows: list[dict[str, str]], retained_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped_time: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in retained_rows:
        grouped_time[(row["source_id"], row["section_name"])].append(row)
    rows_out: list[dict[str, Any]] = []
    for row in fit_rows:
        time_group = grouped_time.get((row["source_id"], row["section_name"]), [])
        time_group.sort(key=lambda item: finite_float(item.get("time_s")))
        latest = time_group[-1] if time_group else None
        mean_target = safe_mean([finite_float(item.get("friction_target_value")) for item in time_group])
        latest_target = finite_float(latest.get("friction_target_value")) if latest else math.nan
        rows_out.append(
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "section_name": row["section_name"],
                "section_kind": row["section_kind"],
                "re_case_mean": finite_float(row.get("re_value")),
                "friction_case_mean": finite_float(row.get("friction_target_value")),
                "direct_to_shear_ratio_case_mean": finite_float(row.get("direct_to_shear_ratio")),
                "support_fraction_case_mean": finite_float(row.get("support_fraction")),
                "latest_retained_time_s": finite_float(latest.get("time_s")) if latest else math.nan,
                "latest_retained_friction": latest_target,
                "latest_vs_retained_mean_fraction": normalized_delta(latest_target, mean_target),
                "time_resolution_status": row["time_resolution_status"],
                "development_note": "Not assumed fully developed; admitted only as a CFD-supported straight-section closure on the bounded Salt straight subset.",
            }
        )
    return rows_out


def straight_refresh_summary(
    fit_rows: list[dict[str, str]],
    sensitivity_rows: list[dict[str, str]],
    late_window_rows: list[dict[str, str]],
) -> dict[str, Any]:
    base_set = {(row["source_id"], row["section_name"]) for row in fit_rows}
    late_fit_rows = [row for row in late_window_rows if row["fit_use_status"] == "fit_used"]
    late_set = {(row["source_id"], row["section_name"]) for row in late_fit_rows}
    sensitivity = next(
        (row for row in sensitivity_rows if row["sensitivity_name"] == "late_window_choice"),
        {},
    )
    dropped_rows: list[dict[str, str]] = []
    for row in late_window_rows:
        key = (row["source_id"], row["section_name"])
        if key in base_set and row["fit_use_status"] != "fit_used":
            dropped_rows.append(row)
    return {
        "base_fit_row_count": len(base_set),
        "late_window_fit_row_count": len(late_set),
        "qualitative_conclusion_changed": str(sensitivity.get("qualitative_conclusion_changed", "")),
        "note": sensitivity.get("note", ""),
        "dropped_rows": [
            {
                "source_id": row["source_id"],
                "case_label": row["case_label"],
                "section_name": row["section_name"],
                "exclusion_reason_primary": row["exclusion_reason_primary"],
                "support_fraction": finite_float(row.get("support_fraction")),
            }
            for row in dropped_rows
        ],
    }


def refreshed_closure_map(rows: list[dict[str, str]], model_summary: dict[str, Any], feature_fit: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if row["closure_name"] == "feature_keff_individual":
            item["status"] = feature_fit["recommended_status"]
            item["mathematical_form"] = "Per-feature geometric constant on stable patch-endpoint pathwise K_eff rows"
            item["coefficients_or_rule"] = (
                "feature names="
                + "|".join(feature_fit.get("stable_feature_names", []))
                + "; log-space constants="
                + "|".join(str(value) for value in feature_fit["constant_model"].get("coefficients", []))
            )
            item["validity_window"] = "Stable feature names only; patch-endpoint p/p_rgh path plus local-boundary reference basis"
            item["source_artifact"] = "reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_feature_keff_fit_results.json"
            item["v1_usage"] = "Optional provisional feature bucket on stable feature classes only"
        if row["closure_name"] == "straight_friction_class_aware_re_power_law":
            item["status"] = model_summary["straight_section_status"]
            item["source_artifact"] = "reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_friction_fit_results.json"
        if row["closure_name"] == "left_lower_leg_nu_branch_aware_re_power_law":
            item["status"] = model_summary["thermal_status"]
            item["source_artifact"] = "reports/2026-06-22_ethan_salt_model_dependency_package_v4/salt_nu_fit_results.json"
        output.append(item)
    return output


def phase_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "phase_order": 1,
            "phase_name": "Freeze current closures",
            "status": "in_progress",
            "board_task": "AGENT-100",
            "goal": "Use the current provisional straight friction and left-lower-leg direct Nu or HTC evidence as the working Salt pseudo-steady closure set.",
        },
        {
            "phase_order": 2,
            "phase_name": "Refresh straight subset after continuations",
            "status": "complete",
            "board_task": "AGENT-104",
            "goal": "Preserved `20 s` Salt windows were frozen from the continuation roots and the straight-section late-window subset was rebuilt from those retained-time packages.",
        },
        {
            "phase_order": 3,
            "phase_name": "Pathwise feature hardening",
            "status": "complete",
            "board_task": "AGENT-103",
            "goal": "Build the retained-time feature-path p versus p_rgh decomposition, subtract the same-basis straight reference, and reopen feature K_eff on the stable feature subset.",
        },
        {
            "phase_order": 4,
            "phase_name": "1D replay refresh",
            "status": "in_progress",
            "board_task": "AGENT-102",
            "goal": "The local replay against the frozen CFD state is built, but the tracked external Fluid lane is still on the June 19 `v1` bundle and lacks a producer for a refreshed June 22 validation bundle.",
        },
    ]


def data_needs_rows() -> list[dict[str, Any]]:
    return [dict(row) for row in load_csv_rows(LITREV_HANDOFF_DIR / "required_future_cfd_observables.csv")]


def one_d_status_rows() -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    if not ONE_D_DIAG_DIR.exists():
        return rows_out
    for path in sorted(ONE_D_DIAG_DIR.glob("ethan_cfd_informed_salt_*/Salt_*/summary.csv")):
        row = next(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
        rows_out.append(
            {
                "case_label": row["case"],
                "scenario": row["scenario"],
                "accepted_for_validation": row["accepted_for_validation"],
                "validity_status": row["validity_status"],
                "air_outlet_temperature_error_k": finite_float(row.get("air_outlet_temperature_error_K")),
                "mass_flow_relative_error_pct": finite_float(row.get("mass_flow_relative_error_pct")),
                "temperature_periodicity_error_k": finite_float(row.get("temperature_periodicity_error_K")),
                "profile_descriptor_mode": row.get("profile_descriptor_mode", ""),
                "internal_htc_mode": row.get("internal_htc_mode", ""),
                "current_evidence_status": row.get("current_evidence_status", ""),
                "source_summary_csv": str(path),
            }
        )
    return rows_out


def best_one_d_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_label"]].append(row)
    best_rows: list[dict[str, Any]] = []
    for case_label, group in sorted(grouped.items()):
        valid = [
            row
            for row in group
            if str(row["accepted_for_validation"]).lower() == "true" and row["validity_status"] == "valid"
        ]
        pool = valid or group
        best = min(
            pool,
            key=lambda row: (
                abs(finite_float(row.get("air_outlet_temperature_error_k"))),
                abs(finite_float(row.get("mass_flow_relative_error_pct"))),
            ),
        )
        best_rows.append(best)
    return best_rows


def main() -> int:
    args = parse_args()
    output_dir = ensure_dir(Path(args.output_dir))

    dashboard_rows = load_csv_rows(NONDIM_DIR / "salt_dashboard.csv")
    thermal_case_rows = load_csv_rows(THERMAL_DIR / "thermal_closure_by_case.csv")
    thermal_time_rows = load_csv_rows(THERMAL_DIR / "thermal_closure_rows.csv")
    straight_fit_rows = load_csv_rows(STRAIGHT_DIR / "straight_fit_ready_rows.csv")
    straight_retained_rows = load_csv_rows(STRAIGHT_DIR / "straight_retained_time_rows.csv")
    straight_sensitivity_rows = load_csv_rows(STRAIGHT_DIR / "straight_sensitivity_runs.csv")
    straight_late_window_rows = load_csv_rows(STRAIGHT_DIR / "straight_late_window_rows.csv")
    feature_stability_rows = load_csv_rows(FEATURE_DIR / "feature_stability_summary.csv")
    model_summary = load_json(MODEL_DIR / "summary.json")
    feature_fit = load_json(MODEL_DIR / "salt_feature_keff_fit_results.json")
    closure_rows = load_csv_rows(BLOCKER_DIR / "one_d_closure_map.csv")

    frozen_rows = frozen_state_contract_rows(dashboard_rows)
    branch_rows = branch_behavior_rows(thermal_case_rows)
    branch_drift_case_rows = branch_drift_rows(thermal_time_rows)
    branch_drift_rows_rollup = branch_drift_rollup(branch_drift_case_rows)
    straight_rows = straight_summary_rows(straight_fit_rows, straight_retained_rows)
    straight_refresh = straight_refresh_summary(
        straight_fit_rows,
        straight_sensitivity_rows,
        straight_late_window_rows,
    )
    closure_map_rows = refreshed_closure_map(closure_rows, model_summary, feature_fit)
    phase_rows = phase_plan_rows()
    data_need_rows = data_needs_rows()
    one_d_rows = one_d_status_rows()
    one_d_best = best_one_d_rows(one_d_rows)

    csv_dump_rows(output_dir / "frozen_state_contract.csv", frozen_rows)
    csv_dump_rows(output_dir / "branch_behavior_summary.csv", branch_rows)
    csv_dump_rows(output_dir / "branch_drift_by_case.csv", branch_drift_case_rows)
    csv_dump_rows(output_dir / "branch_drift_rollup.csv", branch_drift_rows_rollup)
    csv_dump_rows(output_dir / "straight_section_summary.csv", straight_rows)
    csv_dump_rows(output_dir / "closure_map_current.csv", closure_map_rows)
    csv_dump_rows(output_dir / "phase_plan.csv", phase_rows)
    csv_dump_rows(output_dir / "data_needs.csv", data_need_rows)
    csv_dump_rows(output_dir / "feature_stability_summary.csv", feature_stability_rows)
    csv_dump_rows(output_dir / "one_d_readable_status.csv", one_d_rows)
    csv_dump_rows(output_dir / "one_d_best_readable_rows.csv", one_d_best)

    summary = {
        "generated_at": iso_timestamp(),
        "salt_case_count": len(dashboard_rows),
        "branch_count": len(branch_rows),
        "straight_fit_row_count": len(straight_fit_rows),
        "straight_late_window_fit_row_count": straight_refresh["late_window_fit_row_count"],
        "straight_late_window_dropped_rows": straight_refresh["dropped_rows"],
        "feature_reopened_status": feature_fit["recommended_status"],
        "best_one_d_case_count": len(one_d_best),
    }
    write_json(output_dir / "summary.json", summary)

    best_one_d_note = "No readable external 1D diagnostics found."
    if one_d_best:
        example = one_d_best[0]
        best_one_d_note = (
            "Readable Fluid diagnostics exist, but they predate the June 22 feature-path refresh. "
            f"Example best row: {example['case_label']} / {example['scenario']} "
            f"with air-outlet error {example['air_outlet_temperature_error_k']:.2f} K and mass-flow error "
            f"{example['mass_flow_relative_error_pct']:.2f}%."
        )

    bundle_note = (
        "The tracked external Fluid surface is still stale relative to the June 22 closure set."
    )
    if ONE_D_BUNDLE_SNAPSHOT.exists():
        bundle_snapshot = load_json(ONE_D_BUNDLE_SNAPSHOT)
        generated_on = bundle_snapshot.get("generated_on")
        if generated_on:
            bundle_note = (
                "The tracked external Fluid surface is still stale relative to the June 22 closure set: "
                f"its current bundle snapshot was generated on `{generated_on}`."
            )

    dropped_row_note = "No case-mean defended straight rows dropped in the late-window rebuild."
    if straight_refresh["dropped_rows"]:
        dropped = straight_refresh["dropped_rows"][0]
        dropped_row_note = (
            f"The late-window rebuild drops `{dropped['case_label']} / {dropped['section_name']}` "
            f"from the case-mean defended set because `{dropped['exclusion_reason_primary']}` "
            f"(support fraction `{dropped['support_fraction']:.3f}`)."
        )

    readme = f"""# Ethan Frozen-State Results

Generated: `{iso_timestamp()}`

## Frozen-state contract

- Primary pseudo-steady basis: retained late-window mean.
- Sensitivity overlay: latest retained-time snapshot.
- Straight sections are **not** assumed fully developed by default here. The
  admitted straight friction rows remain bounded CFD-supported closures on the
  preserved Salt straight subset, with fully developed values used only as
  references elsewhere in the repo.

## Main findings

- The best current direct internal HTC or Nu evidence remains `left_lower_leg`.
- `upcomer` remains sensitivity-only and should be modeled differently from the
  direct straight branches; this package keeps that boundary explicit.
- `right_leg` or downcomer remains blocked for direct Nu, so cooler-adjacent
  return behavior still needs more retained-time branch observables.
- The refreshed Salt straight package now uses the preserved `20 s` windows
  from the continuation roots. The defended straight set moves from
  `{straight_refresh["base_fit_row_count"]}` case-mean rows to
  `{straight_refresh["late_window_fit_row_count"]}` late-window rows.
- {dropped_row_note}
- Feature `K_eff` is reopened to `{feature_fit["recommended_status"]}` on a
  stable patch-endpoint pathwise basis for `{"|".join(feature_fit.get("stable_feature_names", []))}`.

## 1D status

{best_one_d_note}

{bundle_note}

The local frozen-state replay package is current, but the external rerun with
the refreshed closure set remains in progress on `AGENT-102` because the
external `Fluid` repo still lacks a producer for a refreshed Ethan CFD-informed
Salt validation bundle.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
