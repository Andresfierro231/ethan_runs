#!/usr/bin/env python3
"""Build local 1D closure bakeoff tables from frozen CFD contracts.

Workflow role:
    This is a model-comparison and packaging script. It reads the frozen-state
    CFD validation package plus the defended CFD closure bundle, constructs
    baseline and defended Salt 1D comparison surfaces, and publishes tables that
    separate readable full-surface evidence from stricter defended subsets.

Inputs:
    - Frozen-state CFD package selected by `--frozen-dir`.
    - CFD closure bundle selected by `--closure-bundle-dir`.
    - Existing report products needed to align scenario, branch, and heat
      metadata.

Outputs:
    Bakeoff CSV/JSON/README artifacts and an import manifest. These are local
    comparison products; they do not modify the external Fluid repository.

CLI modifiers:
    - `--frozen-dir` changes the frozen CFD evidence package.
    - `--closure-bundle-dir` changes the closure contract source.
    - `--output-dir` redirects generated bakeoff products.
    - `--import-manifest-path` redirects provenance registration.

Boundaries:
    This script compares preexisting model forms and closure bundles. It should
    not be used as the only scientific score: pressure-distribution agreement,
    thermal-state mismatch, fitted-vs-validation separation, and complexity
    penalties belong in the follow-on model-form bakeoff row.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analyze.cfd_closure_bundle import (  # noqa: E402
    DEFAULT_OUTPUT_DIR as DEFAULT_CLOSURE_BUNDLE_DIR,
    load_bundle_branch_policy_rows,
    load_bundle_payload,
    load_bundle_term_contract_rows,
)
from tools.analyze.build_ethan_frozen_state_1d_validation_package import (  # noqa: E402
    DEFAULT_FROZEN_DIR,
    build_scenario_bundle_alignment_rows,
    build_validation_package,
    frozen_case_mdot,
)
from tools.analyze.ethan_closure_modeling_v3_common import csv_dump_rows, finite_float, load_csv_rows, write_json  # noqa: E402
from tools.common import date_stamp, ensure_dir, iso_timestamp  # noqa: E402

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "2026-06" / "2026-06-23" / "2026-06-23_ethan_1d_closure_bakeoff"
DEFAULT_IMPORT_PATH = ROOT / "imports" / "2026-06-23_ethan_1d_closure_bakeoff.json"
CASE_INPUTS_BY_FAMILY: dict[str, dict[str, float]] = {
    "Salt 1": {"heater_power_W": 232.3, "test_section_power_W": 37.0},
    "Salt 2": {"heater_power_W": 265.7, "test_section_power_W": 37.0},
    "Salt 3": {"heater_power_W": 297.5, "test_section_power_W": 37.0},
    "Salt 4": {"heater_power_W": 337.6, "test_section_power_W": 37.0},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local Salt 1D closure bakeoff from the frozen-state CFD contract, "
            "publishing both the raw readable baseline surface and a defended full-coverage "
            "shadow subset without modifying the original June 22 status table."
        )
    )
    parser.add_argument("--frozen-dir", default=str(DEFAULT_FROZEN_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--closure-bundle-dir", default=str(DEFAULT_CLOSURE_BUNDLE_DIR))
    parser.add_argument("--import-manifest-path", default=str(DEFAULT_IMPORT_PATH))
    return parser.parse_args()


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def case_family(label: str) -> str:
    return " ".join(str(label).split()[:2]).strip()


def scenario_setup_metadata(scenario_name: str) -> dict[str, Any]:
    lower = str(scenario_name).strip().lower()
    scenario_variant = "hybrid" if "_hybrid_" in lower else "baseline" if "_baseline_" in lower else "other"
    outer_closure_kind = "per_parent_multiplier" if scenario_variant == "hybrid" else "uniform_base_only"
    base_insulation_in = math.nan
    if "_ins_" in lower and "in_rad_" in lower:
        insulation_token = lower.split("_ins_", 1)[1].split("in_rad_", 1)[0]
        try:
            base_insulation_in = float(insulation_token)
        except ValueError:
            base_insulation_in = math.nan
    radiation_on = ""
    if "rad_1" in lower:
        radiation_on = "true"
    elif "rad_0" in lower:
        radiation_on = "false"
    branchwise_insulation_note = ""
    if scenario_variant == "hybrid":
        branchwise_insulation_note = (
            "heated_incline=0.85x; left_lower_vertical=0.90x; test_section=0.95x; "
            "left_upper_vertical=0.90x; right_vertical=1.40x; "
            "cooled_incline_pre_hx=1.50x; cooled_incline_post_hx=1.50x"
        )
    return {
        "scenario_variant": scenario_variant,
        "outer_closure_kind": outer_closure_kind,
        "base_insulation_in": base_insulation_in,
        "radiation_on": radiation_on,
        "branchwise_insulation_note": branchwise_insulation_note,
    }


def load_heat_lookup(frozen_rows: list[dict[str, str]]) -> dict[str, dict[str, float | str]]:
    lookup: dict[str, dict[str, float | str]] = {}
    for row in frozen_rows:
        family = case_family(row["case_label"])
        package_root = Path(row["package_root"])
        heat_row = load_csv_rows(package_root / "heat_loss_summary.csv")[0]
        branch_rows = load_csv_rows(package_root / "branch_thermal_summary.csv")
        lookup[family] = {
            "source_id": row["source_id"],
            "frozen_case_label": row["case_label"],
            "comparison_ready": row["comparison_ready"],
            "run_status": row["run_status"],
            "package_root": row["package_root"],
            "late_window_time_start_s": finite_float(row.get("late_window_time_start_s")),
            "late_window_time_end_s": finite_float(row.get("late_window_time_end_s")),
            "late_window_time_count": finite_float(row.get("late_window_time_count")),
            "primary_frozen_state_basis": row.get("primary_frozen_state_basis", ""),
            "sensitivity_snapshot_basis": row.get("sensitivity_snapshot_basis", ""),
            "downcomer_to_upcomer_bulk_delta_k": finite_float(row.get("downcomer_to_upcomer_bulk_delta_k")),
            "heater_to_cooler_bulk_delta_k": finite_float(row.get("heater_to_cooler_bulk_delta_k")),
            "cfd_removed_w": finite_float(heat_row.get("cooling_branch_total_removal_w")),
            "cfd_ambient_w": finite_float(heat_row.get("ambient_proxy_w")),
            "cfd_heater_w": finite_float(heat_row.get("section_heater_net_q_w")),
            "cfd_test_section_w": finite_float(heat_row.get("section_test_section_net_q_w")),
            "cfd_junctions_w": finite_float(heat_row.get("section_junctions_net_q_w")),
            "cfd_mdot_kg_s": frozen_case_mdot(branch_rows),
        }
    return lookup


def build_shadow_rows(
    *,
    status_rows: list[dict[str, str]],
    heat_lookup: dict[str, dict[str, float | str]],
) -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    scenario_case_count: dict[str, int] = defaultdict(int)
    scenario_primary_count: dict[str, int] = defaultdict(int)
    scenario_primary_accepted_count: dict[str, int] = defaultdict(int)
    scenario_all_accepted_count: dict[str, int] = defaultdict(int)
    scenario_energy_values: dict[str, list[float]] = defaultdict(list)
    scenario_mdot_values: dict[str, list[float]] = defaultdict(list)

    staged_rows: list[dict[str, Any]] = []
    for row in status_rows:
        family = case_family(row["case_label"])
        heat_row = heat_lookup[family]
        summary_row = load_csv_rows(Path(row["source_summary_csv"]))[0]
        cfd_removed_w = float(heat_row["cfd_removed_w"])
        cfd_ambient_w = float(heat_row["cfd_ambient_w"])
        cfd_heater_w = float(heat_row["cfd_heater_w"])
        one_d_removed_w = finite_float(summary_row.get("qhx_total_W"))
        one_d_ambient_w = finite_float(summary_row.get("qambient_total_W"))
        one_d_total_loss_w = one_d_removed_w + one_d_ambient_w
        cfd_total_loss_w = cfd_removed_w + cfd_ambient_w
        energy_error_w = one_d_total_loss_w - cfd_total_loss_w
        energy_error_pct_of_heater = (
            100.0 * abs(energy_error_w) / abs(cfd_heater_w)
            if math.isfinite(cfd_heater_w) and cfd_heater_w != 0.0
            else math.nan
        )
        one_d_mdot_kg_s = finite_float(summary_row.get("mdot_kg_s"))
        cfd_mdot_kg_s = float(heat_row["cfd_mdot_kg_s"])
        mass_flow_error_pct_vs_cfd = (
            100.0 * abs(one_d_mdot_kg_s - cfd_mdot_kg_s) / abs(cfd_mdot_kg_s)
            if math.isfinite(one_d_mdot_kg_s) and math.isfinite(cfd_mdot_kg_s) and cfd_mdot_kg_s != 0.0
            else math.nan
        )
        shadow_row = dict(row)
        shadow_row.update(
            {
                "case_family": family,
                "frozen_case_label": heat_row["frozen_case_label"],
                "frozen_source_id": heat_row["source_id"],
                "comparison_ready": heat_row["comparison_ready"],
                "frozen_run_status": heat_row["run_status"],
                "one_d_removed_w": one_d_removed_w,
                "one_d_ambient_w": one_d_ambient_w,
                "one_d_total_loss_w": one_d_total_loss_w,
                "cfd_removed_w": cfd_removed_w,
                "cfd_ambient_w": cfd_ambient_w,
                "cfd_total_loss_w": cfd_total_loss_w,
                "cfd_heater_w": cfd_heater_w,
                "cfd_test_section_w": float(heat_row["cfd_test_section_w"]),
                "cfd_junctions_w": float(heat_row["cfd_junctions_w"]),
                "cfd_mdot_kg_s": cfd_mdot_kg_s,
                "late_window_time_start_s": float(heat_row["late_window_time_start_s"]),
                "late_window_time_end_s": float(heat_row["late_window_time_end_s"]),
                "late_window_time_count": float(heat_row["late_window_time_count"]),
                "primary_frozen_state_basis": heat_row["primary_frozen_state_basis"],
                "sensitivity_snapshot_basis": heat_row["sensitivity_snapshot_basis"],
                "downcomer_to_upcomer_bulk_delta_k": float(heat_row["downcomer_to_upcomer_bulk_delta_k"]),
                "heater_to_cooler_bulk_delta_k": float(heat_row["heater_to_cooler_bulk_delta_k"]),
                "total_loss_error_w": energy_error_w,
                "total_loss_error_pct_of_heater": energy_error_pct_of_heater,
                "pressure_residual_pa": finite_float(summary_row.get("pressure_residual_Pa")),
                "pressure_root_bracketed": summary_row.get("pressure_root_bracketed", ""),
                "temperature_root_bracketed": summary_row.get("temperature_root_bracketed", ""),
                "one_d_mdot_kg_s": one_d_mdot_kg_s,
                "one_d_mass_flow_relative_error_pct": finite_float(summary_row.get("mass_flow_relative_error_pct")),
                "one_d_mass_flow_relative_error_pct_vs_cfd": mass_flow_error_pct_vs_cfd,
            }
        )
        staged_rows.append(shadow_row)
        scenario = str(row["scenario"])
        scenario_case_count[scenario] += 1
        if str(heat_row["comparison_ready"]) == "comparison_candidate":
            scenario_primary_count[scenario] += 1
            if truthy(row.get("accepted_for_validation")) and str(row.get("validity_status", "")).strip().lower() == "valid":
                scenario_primary_accepted_count[scenario] += 1
                if math.isfinite(energy_error_pct_of_heater):
                    scenario_energy_values[scenario].append(energy_error_pct_of_heater)
                mdot_error = mass_flow_error_pct_vs_cfd
                if math.isfinite(mdot_error):
                    scenario_mdot_values[scenario].append(abs(mdot_error))
        if truthy(row.get("accepted_for_validation")) and str(row.get("validity_status", "")).strip().lower() == "valid":
            scenario_all_accepted_count[scenario] += 1

    for row in staged_rows:
        scenario = str(row["scenario"])
        row["scenario_case_count"] = scenario_case_count[scenario]
        row["scenario_primary_count"] = scenario_primary_count[scenario]
        row["scenario_primary_accepted_count"] = scenario_primary_accepted_count[scenario]
        row["scenario_all_accepted_count"] = scenario_all_accepted_count[scenario]
        row["scenario_mean_primary_energy_error_pct_of_heater"] = (
            sum(scenario_energy_values[scenario]) / len(scenario_energy_values[scenario])
            if scenario_energy_values[scenario]
            else math.nan
        )
        row["scenario_mean_primary_mdot_error_pct_vs_cfd"] = (
            sum(scenario_mdot_values[scenario]) / len(scenario_mdot_values[scenario])
            if scenario_mdot_values[scenario]
            else math.nan
        )
        output_rows.append(row)
    return output_rows


def summarize_scenarios(shadow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in shadow_rows:
        grouped[str(row["scenario"])].append(row)

    summaries: list[dict[str, Any]] = []
    for scenario, rows in sorted(grouped.items()):
        accepted_rows = [
            row
            for row in rows
            if truthy(row.get("accepted_for_validation")) and str(row.get("validity_status", "")).strip().lower() == "valid"
        ]
        energy_values = [finite_float(row.get("total_loss_error_pct_of_heater")) for row in accepted_rows]
        energy_values = [value for value in energy_values if math.isfinite(value)]
        mdot_values = [abs(finite_float(row.get("one_d_mass_flow_relative_error_pct_vs_cfd"))) for row in accepted_rows]
        mdot_values = [value for value in mdot_values if math.isfinite(value)]
        summaries.append(
            {
                "scenario": scenario,
                "scenario_family": "hybrid" if str(rows[0].get("profile_descriptor_mode", "")) == "ethan_cfd_informed_salt_v1" else "baseline",
                "closure_stack_label": (
                    f"{rows[0].get('profile_descriptor_mode', '')}|{rows[0].get('internal_htc_mode', '')}"
                    f"|ins={scenario_setup_metadata(scenario)['base_insulation_in']}|rad={scenario_setup_metadata(scenario)['radiation_on']}"
                ),
                "scenario_case_count": rows[0]["scenario_case_count"],
                "scenario_primary_count": rows[0]["scenario_primary_count"],
                "scenario_primary_accepted_count": rows[0]["scenario_primary_accepted_count"],
                "scenario_all_accepted_count": rows[0]["scenario_all_accepted_count"],
                "all_rows_accepted_for_validation": int(rows[0]["scenario_all_accepted_count"]) == int(rows[0]["scenario_case_count"]),
                "mean_primary_energy_error_pct_of_heater": (
                    sum(energy_values) / len(energy_values) if energy_values else math.nan
                ),
                "mean_primary_mdot_error_pct_vs_cfd": sum(mdot_values) / len(mdot_values) if mdot_values else math.nan,
                "profile_descriptor_mode": rows[0].get("profile_descriptor_mode", ""),
                "internal_htc_mode": rows[0].get("internal_htc_mode", ""),
            }
        )
    return summaries


def choose_defended_scenario(scenario_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_case_count = max(int(row["scenario_case_count"]) for row in scenario_rows) if scenario_rows else 0
    full_coverage_rows = [
        row
        for row in scenario_rows
        if int(row["scenario_case_count"]) == expected_case_count
        and int(row["scenario_all_accepted_count"]) == expected_case_count
    ]
    if full_coverage_rows:
        return min(
            full_coverage_rows,
            key=lambda row: (
                finite_float(row.get("mean_primary_energy_error_pct_of_heater")),
                finite_float(row.get("mean_primary_mdot_error_pct_vs_cfd")),
                str(row["scenario"]),
            ),
        )
    return min(
        scenario_rows,
        key=lambda row: (
            -int(row["scenario_all_accepted_count"]),
            finite_float(row.get("mean_primary_energy_error_pct_of_heater")),
            finite_float(row.get("mean_primary_mdot_error_pct_vs_cfd")),
            str(row["scenario"]),
        ),
    )


def build_representative_validation_rows(
    *,
    defended_shadow_rows: list[dict[str, Any]],
    defended_case_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    case_metric_lookup = {
        str(row["frozen_case_label"]): row
        for row in defended_case_rows
        if str(row.get("comparison_class")) == "comparison_candidate"
    }
    rows: list[dict[str, Any]] = []
    for row in defended_shadow_rows:
        if str(row.get("comparison_ready")) != "comparison_candidate":
            continue
        metric_row = case_metric_lookup.get(str(row["frozen_case_label"]), {})
        setup = scenario_setup_metadata(str(row["scenario"]))
        rows.append(
            {
                "generated_date": date_stamp(),
                "comparison_basis": "CFD late_window_mean only",
                "frozen_case_label": row["frozen_case_label"],
                "frozen_source_id": row["frozen_source_id"],
                "late_window_time_start_s": finite_float(row["late_window_time_start_s"]),
                "late_window_time_end_s": finite_float(row["late_window_time_end_s"]),
                "late_window_time_count": finite_float(row["late_window_time_count"]),
                "primary_frozen_state_basis": row["primary_frozen_state_basis"],
                "sensitivity_snapshot_basis": row["sensitivity_snapshot_basis"],
                "cfd_removed_w": finite_float(row["cfd_removed_w"]),
                "cfd_ambient_w": finite_float(row["cfd_ambient_w"]),
                "cfd_total_loss_w": finite_float(row["cfd_total_loss_w"]),
                "cfd_heater_net_w": finite_float(row["cfd_heater_w"]),
                "cfd_test_section_net_w": finite_float(row["cfd_test_section_w"]),
                "cfd_junction_net_w": finite_float(row["cfd_junctions_w"]),
                "cfd_mdot_kg_s": finite_float(row["cfd_mdot_kg_s"]),
                "downcomer_to_upcomer_bulk_delta_k": finite_float(row["downcomer_to_upcomer_bulk_delta_k"]),
                "heater_to_cooler_bulk_delta_k": finite_float(row["heater_to_cooler_bulk_delta_k"]),
                "one_d_scenario": row["scenario"],
                "one_d_scenario_variant": setup["scenario_variant"],
                "one_d_outer_closure_kind": setup["outer_closure_kind"],
                "one_d_base_insulation_in": setup["base_insulation_in"],
                "one_d_radiation_on": setup["radiation_on"],
                "one_d_branchwise_insulation_note": setup["branchwise_insulation_note"],
                "one_d_total_loss_w": finite_float(row["one_d_total_loss_w"]),
                "one_d_removed_w": finite_float(row["one_d_removed_w"]),
                "one_d_ambient_w": finite_float(row["one_d_ambient_w"]),
                "one_d_mdot_kg_s": finite_float(row["one_d_mdot_kg_s"]),
                "one_d_energy_error_pct_of_heater": finite_float(metric_row.get("energy_error_pct_of_heater")),
                "one_d_tw_rmse_k": finite_float(metric_row.get("tw_rmse_k")),
                "one_d_tp_rmse_k": finite_float(metric_row.get("tp_rmse_k")),
                "one_d_mass_flow_error_pct_vs_cfd": finite_float(metric_row.get("mass_flow_relative_error_pct_vs_cfd")),
            }
        )
    return rows


def build_heater_partition_rows(representative_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in representative_rows:
        family = case_family(str(row["frozen_case_label"]))
        case_inputs = CASE_INPUTS_BY_FAMILY.get(family, {})
        heater_power_w = finite_float(case_inputs.get("heater_power_W"))
        test_section_power_w = finite_float(case_inputs.get("test_section_power_W"))
        total_modeled_input_w = (
            heater_power_w + test_section_power_w
            if math.isfinite(heater_power_w) and math.isfinite(test_section_power_w)
            else math.nan
        )
        cfd_heater_net_w = finite_float(row["cfd_heater_net_w"])
        rows.append(
            {
                "generated_date": date_stamp(),
                "frozen_case_label": row["frozen_case_label"],
                "heater_power_config_w": heater_power_w,
                "test_section_power_config_w": test_section_power_w,
                "total_modeled_input_w": total_modeled_input_w,
                "cfd_heater_net_to_fluid_w": cfd_heater_net_w,
                "heater_delivery_fraction_of_config": (
                    cfd_heater_net_w / heater_power_w
                    if math.isfinite(cfd_heater_net_w) and math.isfinite(heater_power_w) and heater_power_w != 0.0
                    else math.nan
                ),
                "heater_to_fluid_fraction_of_total_modeled_input": (
                    cfd_heater_net_w / total_modeled_input_w
                    if math.isfinite(cfd_heater_net_w)
                    and math.isfinite(total_modeled_input_w)
                    and total_modeled_input_w != 0.0
                    else math.nan
                ),
                "heater_section_gap_w": (
                    heater_power_w - cfd_heater_net_w
                    if math.isfinite(cfd_heater_net_w) and math.isfinite(heater_power_w)
                    else math.nan
                ),
                "heater_power_not_reaching_fluid_w": (
                    heater_power_w - cfd_heater_net_w
                    if math.isfinite(cfd_heater_net_w) and math.isfinite(heater_power_w)
                    else math.nan
                ),
                "cfd_total_loss_w": finite_float(row["cfd_total_loss_w"]),
                "cfd_removed_w": finite_float(row["cfd_removed_w"]),
                "cfd_ambient_w": finite_float(row["cfd_ambient_w"]),
                "cooling_fraction_of_total_loss": (
                    finite_float(row["cfd_removed_w"]) / finite_float(row["cfd_total_loss_w"])
                    if finite_float(row["cfd_total_loss_w"]) != 0.0
                    else math.nan
                ),
                "ambient_fraction_of_total_loss": (
                    finite_float(row["cfd_ambient_w"]) / finite_float(row["cfd_total_loss_w"])
                    if finite_float(row["cfd_total_loss_w"]) != 0.0
                    else math.nan
                ),
                "cfd_test_section_net_w": finite_float(row["cfd_test_section_net_w"]),
                "cfd_junction_net_w": finite_float(row["cfd_junction_net_w"]),
                "note": (
                    "CFD total loss follows the current frozen contract Q_lost = Q_removed + Q_ambient; "
                    "ambient_proxy_w is a bookkeeping proxy and should not be double-counted outside that contract."
                ),
            }
        )
    return rows


def build_setup_documentation(
    *,
    defended_scenario: dict[str, Any],
    frozen_dir: Path,
    bundle_payload: dict[str, Any],
    defended_bundle_alignment: dict[str, Any],
) -> str:
    defended_name = str(defended_scenario["scenario"])
    setup = scenario_setup_metadata(defended_name)
    friction = bundle_payload["distributed_friction"]
    primary_ua = bundle_payload["primary_ua_surface"]
    secondary_htc = bundle_payload["secondary_htc_surface"]
    direct_nu = bundle_payload["direct_nusselt"]
    return f"""# 1D Setup And Confidence

Generated: `{iso_timestamp()}`

## Comparison basis

- This bakeoff compares the 1D model against CFD-derived frozen-state results, not against experimental temperatures or experimental mass flow.
- The primary CFD truth basis is `late_window_mean` from `reports/{frozen_dir.name}/frozen_state_contract.csv`.
- Experimental values still exist inside the external `Fluid` reporting roots for provenance, but the local frozen-state validation surfaces in this package are CFD-to-1D.

## Active 1D model used here

- Active solver lineage: `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2`
- Active mode: `predictive_airside_hx`
- Legacy second model still in the repo: the older `first_order_model_tamu_loop.py` style path, retained only as historical lineage.
- This bakeoff is using the current `tamu_loop_model_v2` path, not the legacy solver.

## Scenario actually scored here

- Defended full-coverage scenario: `{defended_name}`
- Defended winner setup class: `{setup["scenario_variant"]}` with base `insulation_thickness_in = {setup["base_insulation_in"]:.1f} in` and `radiation_on = {setup["radiation_on"]}`.
- The defended winner is the baseline member, so it does not apply the hybrid branchwise outer-loss multipliers.
- The broader readable `ethan_cfd_informed_salt_v1` family only publishes base `1.0 in` and `2.0 in` conditions, but its hybrid rows can still apply branchwise effective insulation multipliers:
  `heated_incline=0.85x`, `left_lower_vertical=0.90x`, `test_section=0.95x`,
  `left_upper_vertical=0.90x`, `right_vertical=1.40x`,
  `cooled_incline_pre_hx=1.50x`, `cooled_incline_post_hx=1.50x`.
- Therefore the current defended result is not already a global `1.4 in` case.
  If the representative CFD physical setup should be treated as globally
  `1.4 in`, the present defended winner is a setup-mismatched surrogate rather
  than a final physically matched predictive result.

## Branch closure assignment

- Distributed straight friction:
  `{friction["closure_name"]}`
  on `{"|".join(friction["target_regions"])}`, status `{friction["status"]}`
- Direct internal thermal law:
  `{direct_nu["closure_name"]}`
  on `{"|".join(direct_nu["target_regions"])}` only, status `{direct_nu["status"]}`
- Primary thermal closure:
  `{primary_ua["closure_name"]}`
  on `{"|".join(primary_ua["target_regions"])}`
- Secondary thermal diagnostic surface:
  `{secondary_htc["closure_name"]}`
  on `{"|".join(secondary_htc["target_regions"])}`
- Unsupported or blocked branches:
  `right_leg` / downcomer, cooler return, and feature losses remain on residual or calibration-only lanes
- Defended winner bundle alignment:
  `{defended_bundle_alignment.get("bundle_alignment_status", "")}`.
  {defended_bundle_alignment.get("bundle_alignment_note", "")}

## Insulation and radiation treatment

- Insulation is represented as an effective radial resistance on insulated segments.
- The active scenario sets fixed `insulation_thickness_in` and may also apply per-parent effective insulation multipliers.
- In the defended winner, the insulation treatment is uniform at the base thickness with no hybrid branchwise multipliers.
- External convection is modeled with a blended Churchill-Chu natural-convection correlation.
- Radiation is modeled as linearized Stefan-Boltzmann exchange to ambient.
- Radiation is active only when `radiation_on = true`.
- Non-test-section emissivity follows the insulation material default; the test section uses quartz emissivity `0.95`.

## Heat-source and sink treatment

- Salt cases use tracked heater power plus a separate `37 W` quartz test-section source in the current `Fluid/configs/cases.yaml` contract.
- The active predictive mode solves the cooling-jacket duty from the air-side boundary condition.
- The frozen-CFD comparison closes heat loss with `Q_lost = Q_removed + Q_ambient`, where `Q_ambient` is the CFD-side `ambient_proxy_w` bookkeeping quantity.

## Confidence and uncertainty

- Highest confidence:
  CFD late-window heat ledger, left-lower-leg direct developing-flow thermal evidence, and the existence of strong branch-to-branch development differences.
- Medium confidence:
  full-coverage baseline winner on the current frozen surface, as a CFD-matched
  scoring result within the currently published external scenario menu.
- Lower confidence:
  hybrid/profile-descriptor ranking beyond Salt 1, because the readable external `v1` bundle still lacks domain breadth.
- Explicitly uncertain:
  physically matched insulation if the intended CFD setup is `1.4 in`, direct downcomer HTC, and any one-law treatment of the whole upcomer branch.
"""


def surface_summary_row(
    *,
    surface_label: str,
    surface_dir: Path,
) -> dict[str, Any]:
    summary = load_csv_rows(surface_dir / "scenario_ranking.csv")
    top = summary[0] if summary else {}
    return {
        "surface_label": surface_label,
        "surface_dir": str(surface_dir),
        "scenario_count_primary": len(summary),
        "best_primary_scenario": top.get("scenario", ""),
        "best_primary_composite_rank": finite_float(top.get("composite_rank")),
        "best_primary_composite_score": finite_float(top.get("composite_score")),
        "best_primary_mean_energy_error_pct_of_heater": finite_float(top.get("mean_energy_error_pct_of_heater")),
        "best_primary_mean_tw_rmse_k": finite_float(top.get("mean_tw_rmse_k")),
        "best_primary_mean_tp_rmse_k": finite_float(top.get("mean_tp_rmse_k")),
        "best_primary_mean_mass_flow_relative_error_pct_vs_cfd": finite_float(top.get("mean_mass_flow_relative_error_pct_vs_cfd")),
        "all_rows_accepted_for_validation": top.get("all_rows_accepted_for_validation", ""),
    }


def build_readme(
    *,
    frozen_dir: Path,
    baseline_rows: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    defended_scenario: dict[str, Any],
    surface_rows: list[dict[str, Any]],
    bundle_payload: dict[str, Any],
    scenario_bundle_rows: list[dict[str, Any]],
) -> str:
    baseline_count = len(baseline_rows)
    scenario_count = len(scenario_rows)
    defended_name = defended_scenario["scenario"]
    full_case_count = defended_scenario["scenario_case_count"]
    full_accept_count = defended_scenario["scenario_all_accepted_count"]
    baseline_surface = next(row for row in surface_rows if row["surface_label"] == "baseline_full_surface")
    defended_surface = next(row for row in surface_rows if row["surface_label"] == "defended_full_coverage_surface")
    top_bundle_row = next(
        (row for row in scenario_bundle_rows if row.get("scenario") == defended_name),
        scenario_bundle_rows[0] if scenario_bundle_rows else {},
    )
    friction = bundle_payload["distributed_friction"]
    primary_ua = bundle_payload["primary_ua_surface"]
    direct_nu = bundle_payload["direct_nusselt"]
    return f"""# Ethan 1D Closure Bakeoff

Generated: `{iso_timestamp()}`

## Scope

- This package stages a local shadow bakeoff from the `{frozen_dir.name}` Salt contract.
- It does not invent a new `Fluid` rerun. The only readable external diagnostics on disk remain the June 19 `ethan_cfd_informed_salt_v1` bundle.
- Two surfaces are published:
  - `baseline_full_surface`: all readable Salt status rows copied into a local shadow table
  - `defended_full_coverage_surface`: the single full-coverage scenario that kept every Salt case accepted and valid in the shadow table

## Current closure contract used for interpretation

- Distributed straight friction is read from the local CFD closure bundle term
  `{friction["closure_name"]}` on `{", ".join(friction["target_regions"])}`.
- Primary thermal conductance interpretation is read from
  `{primary_ua["closure_name"]}` on `{", ".join(primary_ua["target_regions"])}`.
- Direct fitted `Nu` remains limited to `{direct_nu["closure_name"]}` on
  `{", ".join(direct_nu["target_regions"])}`.
- Defended winner bundle alignment:
  `{top_bundle_row.get("bundle_alignment_status", "")}`.
  {top_bundle_row.get("bundle_alignment_note", "")}

## Current defended result

- Shadow baseline rows: `{baseline_count}` across `{scenario_count}` scenarios.
- Defended full-coverage scenario: `{defended_name}` with `{full_accept_count}/{full_case_count}` accepted Salt rows.
- Baseline surface best primary scenario: `{baseline_surface['best_primary_scenario']}` with mean |energy| `{baseline_surface['best_primary_mean_energy_error_pct_of_heater']:.2f}%` heater and mean mass-flow error vs CFD `{baseline_surface['best_primary_mean_mass_flow_relative_error_pct_vs_cfd']:.2f}%`.
- Defended surface primary scenario: `{defended_surface['best_primary_scenario']}` with mean |energy| `{defended_surface['best_primary_mean_energy_error_pct_of_heater']:.2f}%` heater and mean mass-flow error vs CFD `{defended_surface['best_primary_mean_mass_flow_relative_error_pct_vs_cfd']:.2f}%`.

## Interpretation boundary

- This is a scoring and filtering bakeoff, not a refreshed 1D physics bundle.
- The defended subset is useful because it removes under-covered hybrid rows and keeps one scenario family that stayed readable across Salt 1-4.
- A real closure retune still requires a new external diagnostics bundle; this package only makes the current local modeling boundary explicit.
- The added dated validation table and heater-partition table in this package are CFD-last-window tables, not experiment tables.
- The defended winner is the baseline `1.0 in` radiation-on member, not the hybrid branch-adjusted member.
- The currently scored readable external bundle only publishes base `1.0 in` / `2.0 in` conditions. Hybrid rows can apply branchwise effective insulation multipliers, including `right_vertical = 1.40x`, but no readable global `1.4 in` Salt scenario is published yet.
- If the target CFD insulation is globally `1.4 in`, treat the present winner as a bounded surrogate until that condition is rerun or explicitly published.
- The top-level bakeoff directory already contained extra `11:29` artifacts before this pass completed. They were preserved in place; the new driver guarantees only the shadow status CSVs, `surface_summary.csv`, `summary.json`, `README.md`, and the two rebuilt surface subdirectories.

## Added closure-reference artifacts

- `closure_term_reference.csv`
- `closure_branch_policy.csv`
- `scenario_bundle_alignment.csv`
"""


def write_import_manifest(
    *,
    frozen_dir: Path,
    closure_bundle_dir: Path,
    output_dir: Path,
    surface_rows: list[dict[str, Any]],
    import_manifest_path: Path,
) -> None:
    payload = {
        "generated_at": iso_timestamp(),
        "package": output_dir.name,
        "inputs": {
            "frozen_dir": str(frozen_dir.resolve()),
            "baseline_status_csv": str((frozen_dir / "one_d_readable_status.csv").resolve()),
            "frozen_state_contract": str((frozen_dir / "frozen_state_contract.csv").resolve()),
            "closure_bundle_dir": str(closure_bundle_dir.resolve()),
        },
        "outputs": {
            "report_dir": str(output_dir.resolve()),
            "baseline_surface_dir": str((output_dir / "baseline_full_surface").resolve()),
            "defended_surface_dir": str((output_dir / "defended_full_coverage_surface").resolve()),
            "surface_summary_csv": str((output_dir / "surface_summary.csv").resolve()),
            "dated_representative_validation_csv": str((output_dir / f"{date_stamp()}_representative_salt_last_window_validation_table.csv").resolve()),
            "dated_heater_partition_csv": str((output_dir / f"{date_stamp()}_representative_salt_heater_partition.csv").resolve()),
            "dated_setup_markdown": str((output_dir / f"{date_stamp()}_one_d_setup_and_confidence.md").resolve()),
            "closure_term_reference_csv": str((output_dir / "closure_term_reference.csv").resolve()),
            "closure_branch_policy_csv": str((output_dir / "closure_branch_policy.csv").resolve()),
            "scenario_bundle_alignment_csv": str((output_dir / "scenario_bundle_alignment.csv").resolve()),
        },
        "surface_rows": surface_rows,
    }
    write_json(import_manifest_path, payload)


def main() -> int:
    args = parse_args()
    frozen_dir = Path(args.frozen_dir)
    closure_bundle_dir = Path(args.closure_bundle_dir)
    output_dir = ensure_dir(Path(args.output_dir))
    baseline_surface_dir = ensure_dir(output_dir / "baseline_full_surface")
    defended_surface_dir = ensure_dir(output_dir / "defended_full_coverage_surface")

    baseline_status_rows = load_csv_rows(frozen_dir / "one_d_readable_status.csv")
    frozen_rows = load_csv_rows(frozen_dir / "frozen_state_contract.csv")
    heat_lookup = load_heat_lookup(frozen_rows)
    shadow_rows = build_shadow_rows(status_rows=baseline_status_rows, heat_lookup=heat_lookup)
    scenario_rows = summarize_scenarios(shadow_rows)
    bundle_payload = load_bundle_payload(closure_bundle_dir)
    bundle_term_rows = load_bundle_term_contract_rows(closure_bundle_dir)
    bundle_branch_rows = load_bundle_branch_policy_rows(closure_bundle_dir)
    scenario_bundle_rows = build_scenario_bundle_alignment_rows(
        scenario_rows=scenario_rows,
        bundle_payload=bundle_payload,
    )
    defended_scenario = choose_defended_scenario(scenario_rows)
    defended_name = str(defended_scenario["scenario"])
    defended_shadow_rows = [row for row in shadow_rows if str(row["scenario"]) == defended_name]
    defended_bundle_alignment = next(
        (row for row in scenario_bundle_rows if row.get("scenario") == defended_name),
        {},
    )

    baseline_shadow_path = output_dir / "baseline_shadow_status.csv"
    defended_shadow_path = output_dir / "defended_shadow_status.csv"
    csv_dump_rows(baseline_shadow_path, shadow_rows)
    csv_dump_rows(defended_shadow_path, defended_shadow_rows)
    csv_dump_rows(output_dir / "scenario_shadow_summary.csv", scenario_rows)
    csv_dump_rows(output_dir / "closure_term_reference.csv", bundle_term_rows)
    csv_dump_rows(output_dir / "closure_branch_policy.csv", bundle_branch_rows)
    csv_dump_rows(output_dir / "scenario_bundle_alignment.csv", scenario_bundle_rows)

    build_validation_package(
        frozen_dir=frozen_dir,
        one_d_status_csv=baseline_shadow_path,
        output_dir=baseline_surface_dir,
        closure_bundle_dir=closure_bundle_dir,
        import_manifest_path=None,
    )
    build_validation_package(
        frozen_dir=frozen_dir,
        one_d_status_csv=defended_shadow_path,
        output_dir=defended_surface_dir,
        closure_bundle_dir=closure_bundle_dir,
        import_manifest_path=None,
    )

    surface_rows = [
        surface_summary_row(surface_label="baseline_full_surface", surface_dir=baseline_surface_dir),
        surface_summary_row(surface_label="defended_full_coverage_surface", surface_dir=defended_surface_dir),
    ]
    csv_dump_rows(output_dir / "surface_summary.csv", surface_rows)
    defended_case_rows = load_csv_rows(defended_surface_dir / "case_metric_summary.csv")
    representative_validation_rows = build_representative_validation_rows(
        defended_shadow_rows=defended_shadow_rows,
        defended_case_rows=defended_case_rows,
    )
    heater_partition_rows = build_heater_partition_rows(representative_validation_rows)
    dated_validation_csv = output_dir / f"{date_stamp()}_representative_salt_last_window_validation_table.csv"
    dated_heater_csv = output_dir / f"{date_stamp()}_representative_salt_heater_partition.csv"
    dated_setup_md = output_dir / f"{date_stamp()}_one_d_setup_and_confidence.md"
    csv_dump_rows(dated_validation_csv, representative_validation_rows)
    csv_dump_rows(dated_heater_csv, heater_partition_rows)
    dated_setup_md.write_text(
        build_setup_documentation(
            defended_scenario=defended_scenario,
            frozen_dir=frozen_dir,
            bundle_payload=bundle_payload,
            defended_bundle_alignment=defended_bundle_alignment,
        ),
        encoding="utf-8",
    )

    summary = {
        "generated_at": iso_timestamp(),
        "baseline_shadow_row_count": len(shadow_rows),
        "scenario_count": len(scenario_rows),
        "defended_scenario": defended_name,
        "defended_shadow_row_count": len(defended_shadow_rows),
        "surface_labels": [row["surface_label"] for row in surface_rows],
        "comparison_basis": "CFD late_window_mean only",
        "dated_representative_validation_csv": str(dated_validation_csv),
        "dated_heater_partition_csv": str(dated_heater_csv),
        "dated_setup_markdown": str(dated_setup_md),
        "closure_bundle_dir": str(closure_bundle_dir.resolve()),
        "closure_bundle_term_count": len(bundle_term_rows),
        "closure_bundle_branch_policy_count": len(bundle_branch_rows),
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "README.md").write_text(
        build_readme(
            frozen_dir=frozen_dir,
            baseline_rows=shadow_rows,
            scenario_rows=scenario_rows,
            defended_scenario=defended_scenario,
            surface_rows=surface_rows,
            bundle_payload=bundle_payload,
            scenario_bundle_rows=scenario_bundle_rows,
        ),
        encoding="utf-8",
    )
    write_import_manifest(
        frozen_dir=frozen_dir,
        closure_bundle_dir=closure_bundle_dir,
        output_dir=output_dir,
        surface_rows=surface_rows,
        import_manifest_path=Path(args.import_manifest_path),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
