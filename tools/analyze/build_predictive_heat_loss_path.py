#!/usr/bin/env python3
"""Build a repo-local predictive heat-loss path package.

This is a synthesis builder, not a solver runner. It reads already published
thermal boundary, interface, and fixed-mdot replay artifacts; derives compact
control-volume and residual tables; and keeps blocked thermal-closure rows out
of fit admission.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable


REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path"

SEGMENT_REDUCTION_CSV = (
    REPO
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv"
)
PATCH_ROLE_SUMMARY_CSV = (
    REPO
    / "work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/patch_role_area_heat_summary.csv"
)
ENTHALPY_RESIDUALS_CSV = (
    REPO
    / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv"
)
FIXED_MDOT_REPLAY_CSV = (
    REPO
    / "work_products/2026-07/2026-07-08/2026-07-08_thermal_mismatch_remedy_deep_dive/fixed_mdot_replay_results.csv"
)
REMEDY_PATH_SUMMARY_CSV = (
    REPO
    / "work_products/2026-07/2026-07-08/2026-07-08_thermal_mismatch_remedy_deep_dive/remedy_path_summary.csv"
)
ENERGY_DEFECT_BUDGET_CSV = (
    REPO
    / "work_products/2026-07/2026-07-08/2026-07-08_thermal_mismatch_remedy_deep_dive/energy_defect_budget.csv"
)
INTERFACE_SAMPLES_CSV = (
    REPO
    / "work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv"
)
SEGMENT_HTC_DIR = REPO / "work_products/2026-07/2026-07-01/2026-07-01_claude_thermal_downcomer"

SOURCE_PACKAGES = {
    "thermal_boundary_patch_role_table": str(SEGMENT_REDUCTION_CSV.parent.relative_to(REPO)),
    "patchwise_heat_ledger_enthalpy_interfaces": str(ENTHALPY_RESIDUALS_CSV.parent.relative_to(REPO)),
    "thermal_mismatch_remedy_deep_dive": str(FIXED_MDOT_REPLAY_CSV.parent.relative_to(REPO)),
    "thermal_openfoam_interface_sampling": str(INTERFACE_SAMPLES_CSV.parent.relative_to(REPO)),
    "legacy_segment_htc_uaprime": str(SEGMENT_HTC_DIR.relative_to(REPO)),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: render_value(row.get(key, "")) for key in fieldnames})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def render_value(value: object) -> object:
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.6g}"
    return value


def num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def case_id_from_source(source_id: str) -> str:
    match = re.search(r"salt_test_(\d+)", source_id)
    if not match:
        raise ValueError(f"cannot derive case_id from source_id={source_id!r}")
    return f"salt_{match.group(1)}"


def bool_text(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def classify_effective_thermal_status(htc_row: dict[str, str] | None) -> str:
    """Return the conservative admission status for effective h/Nu inputs."""
    if not htc_row:
        return "not_available_for_segment"
    if bool_text(htc_row.get("thermally_blocked")):
        return "blocked_by_source_segment_htc_flag"
    status = str(htc_row.get("status", "")).strip()
    if status != "computed":
        return f"blocked_source_status_{status or 'missing'}"
    if str(htc_row.get("mesh_independence", "")).strip() != "ESTABLISHED":
        return "validation_only_mesh_unestablished"
    if str(htc_row.get("nu_direct_admitted", "")).strip().lower() != "true":
        return "validation_only_nu_not_direct_admitted"
    return "fit_candidate_pending_latest_time_and_uncertainty"


def classify_control_volume_fit_status(
    segment_row: dict[str, str],
    enthalpy_row: dict[str, str] | None,
    htc_status: str,
) -> str:
    if segment_row["one_d_segment"] == "junction":
        return "blocked_junction_not_control_volume_bracketed"
    if enthalpy_row is None:
        return "blocked_no_physical_interface_bracket"
    quality_flags = str(enthalpy_row.get("quality_flags", ""))
    bracket_status = str(enthalpy_row.get("bracket_status", ""))
    max_recirc = num(enthalpy_row.get("max_interface_recirc_ratio"))
    if "not_bracketed" in bracket_status:
        return "blocked_no_physical_interface_bracket"
    if "diagnostic_only" in bracket_status or "recirculation_cell_diagnostic_only" in quality_flags:
        return "diagnostic_only_high_recirculation"
    if max_recirc is not None and max_recirc >= 0.5:
        return "diagnostic_only_high_recirculation"
    if htc_status.startswith("fit_candidate"):
        return "fit_candidate_needs_uncertainty_and_holdout"
    return "validation_only_effective_thermal_not_fit_safe"


def cooler_error_reduction(baseline_error_k: float, parity_error_k: float) -> tuple[float, float]:
    reduction = abs(baseline_error_k) - abs(parity_error_k)
    pct = 100.0 * reduction / abs(baseline_error_k) if baseline_error_k else 0.0
    return reduction, pct


def load_segment_htc_rows(htc_dir: Path = SEGMENT_HTC_DIR) -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for path in sorted(htc_dir.glob("segment_htc_uaprime_*.csv")):
        suffix = path.name.removeprefix("segment_htc_uaprime_").removesuffix(".csv")
        case_id = case_id_from_source(suffix)
        for row in read_csv(path):
            row = dict(row)
            row["source_id"] = suffix
            row["case_id"] = case_id
            rows[(case_id, row["segment"])] = row
    return rows


def build_control_volume_effective_table(
    segment_rows: list[dict[str, str]],
    enthalpy_rows: list[dict[str, str]],
    htc_rows: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    enthalpy_by_segment = {
        (row["case_id"], row["physical_segment"]): row for row in enthalpy_rows
    }
    output: list[dict[str, object]] = []
    for row in segment_rows:
        enthalpy = enthalpy_by_segment.get((row["case_id"], row["one_d_segment"]))
        htc = htc_rows.get((row["case_id"], row["one_d_segment"]))
        htc_status = classify_effective_thermal_status(htc)
        fit_status = classify_control_volume_fit_status(row, enthalpy, htc_status)
        area = num(row.get("area_m2")) or 0.0
        ext_h = num(row.get("area_weighted_h_W_m2K")) or 0.0
        realized = num(row.get("realized_wallHeatFlux_W")) or 0.0
        imposed = num(row.get("imposed_Q_W")) or 0.0
        residual = num(enthalpy.get("wallHeatFlux_vs_enthalpy_residual_W")) if enthalpy else None

        output.append(
            {
                "source_id": row["source_id"],
                "case_id": row["case_id"],
                "one_d_segment": row["one_d_segment"],
                "component_parent_spans": row["component_parent_spans"],
                "area_m2": area,
                "external_h_W_m2K": ext_h,
                "external_hA_W_per_K": area * ext_h,
                "area_weighted_Ta_K": num(row.get("area_weighted_Ta_K")),
                "area_weighted_Tsur_K": num(row.get("area_weighted_Tsur_K")),
                "area_weighted_emissivity": num(row.get("area_weighted_emissivity")),
                "radiation_parity_mode": "inseparable_rcExternalTemperature_wall_heat_flux",
                "realized_wallHeatFlux_W_positive_to_fluid": realized,
                "imposed_Q_W_positive_to_fluid": imposed,
                "imposed_minus_realized_W": imposed - realized,
                "abs_imposed_minus_realized_W": abs(imposed - realized),
                "enthalpy_change_W": num(enthalpy.get("enthalpy_change_W")) if enthalpy else None,
                "wallHeatFlux_vs_enthalpy_residual_W": residual,
                "abs_enthalpy_residual_W": abs(residual) if residual is not None else None,
                "residual_fraction": num(enthalpy.get("residual_fraction")) if enthalpy else None,
                "bracket_status": enthalpy.get("bracket_status", "") if enthalpy else "missing",
                "max_interface_recirc_ratio": num(enthalpy.get("max_interface_recirc_ratio")) if enthalpy else None,
                "interface_quality_flags": enthalpy.get("quality_flags", "") if enthalpy else "missing",
                "T_bulk_inlet_K": num(enthalpy.get("T_bulk_inlet_K")) if enthalpy else None,
                "T_bulk_outlet_K": num(enthalpy.get("T_bulk_outlet_K")) if enthalpy else None,
                "delta_T_K": num(enthalpy.get("delta_T_K")) if enthalpy else None,
                "mdot_kg_s": num(enthalpy.get("mdot_kg_s")) if enthalpy else None,
                "cp_jkgk": num(enthalpy.get("cp_jkgk")) if enthalpy else None,
                "effective_htc_W_m2K": num(htc.get("htc_wm2k")) if htc else None,
                "Nu_eff": num(htc.get("Nu")) if htc else None,
                "uaprime_W_mK": num(htc.get("uaprime_wmk")) if htc else None,
                "T_wall_K": num(htc.get("T_wall_k")) if htc else None,
                "T_bulk_for_htc_K": num(htc.get("T_bulk_k")) if htc else None,
                "internal_delta_T_K": num(htc.get("delta_T_k")) if htc else None,
                "segment_htc_mesh": htc.get("mesh", "") if htc else "",
                "segment_htc_mesh_independence": htc.get("mesh_independence", "") if htc else "",
                "thermal_effective_status": htc_status,
                "fit_use_status": fit_status,
            }
        )
    return output


def build_cooler_hx_duty_table(
    role_rows: list[dict[str, str]],
    replay_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    cooler_by_case = {
        row["case_id"]: row for row in role_rows if row.get("role") == "cooler"
    }
    replay_by_case_path = {
        (row["case_id"], row["path_id"]): row for row in replay_rows
    }
    output: list[dict[str, object]] = []
    for case_id in sorted(cooler_by_case):
        p0 = replay_by_case_path[(case_id, "P0_fixed_mdot_current_1d_contract")]
        p1 = replay_by_case_path[(case_id, "P1_cfd_cooler_duty_only")]
        cooler = cooler_by_case[case_id]
        baseline_error = num(p0["Tmean_error_K"]) or 0.0
        parity_error = num(p1["Tmean_error_K"]) or 0.0
        reduction, pct = cooler_error_reduction(baseline_error, parity_error)
        cfd_realized = abs(num(cooler["realized_wallHeatFlux_W"]) or 0.0)
        cfd_imposed = abs(num(cooler["imposed_Q_W"]) or 0.0)
        baseline_qhx = num(p0["qhx_total_W"]) or 0.0
        output.append(
            {
                "case_id": case_id,
                "baseline_1d_qhx_total_W": baseline_qhx,
                "cfd_cooler_imposed_abs_W": cfd_imposed,
                "cfd_cooler_realized_abs_W": cfd_realized,
                "cfd_cooler_realized_minus_imposed_abs_W": cfd_realized - cfd_imposed,
                "cooler_extra_removal_vs_baseline_1d_W": cfd_realized - baseline_qhx,
                "baseline_Tmean_error_K": baseline_error,
                "cfd_cooler_duty_Tmean_error_K": parity_error,
                "Tmean_abs_error_reduction_K": reduction,
                "Tmean_abs_error_reduction_pct": pct,
                "cooler_duty_mismatch_class": "first_order_external_hx_boundary_error",
            }
        )
    return output


def replay_mode_family(path_id: str) -> str:
    if path_id.startswith("P0_"):
        return "baseline_current_1d_contract"
    if path_id.startswith("P1_"):
        return "external_hx_cooler_duty_parity"
    if path_id.startswith("P2_"):
        return "internal_source_contract_diagnostic"
    if path_id.startswith("P3_"):
        return "source_plus_test_section_sink_diagnostic"
    if path_id.startswith("P4_"):
        return "full_wall_flux_prescribed_diagnostic"
    return "unknown"


def build_replay_mode_scores(
    replay_rows: list[dict[str, str]],
    summary_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    summary_by_path = {row["path_id"]: row for row in summary_rows}
    rows: list[dict[str, object]] = []
    for row in replay_rows:
        summary = summary_by_path.get(row["path_id"], {})
        rows.append(
            {
                "case_id": row["case_id"],
                "path_id": row["path_id"],
                "mode_family": replay_mode_family(row["path_id"]),
                "root_found": row["root_found"],
                "Tmean_error_K": num(row["Tmean_error_K"]),
                "abs_Tmean_error_K": abs(num(row["Tmean_error_K"]) or 0.0),
                "loop_delta_T_error_K": num(row["loop_delta_T_error_K"]),
                "qhx_total_W": num(row["qhx_total_W"]),
                "qambient_total_W": num(row["qambient_total_W"]),
                "source_total_W": num(row["source_total_W"]),
                "prescribed_loss_total_W": num(row["prescribed_loss_total_W"]),
                "mean_abs_Tmean_error_K_by_path": num(summary.get("mean_abs_Tmean_error_K")),
                "passes_thermal_gate": summary.get("passes_thermal_gate", "False"),
                "predictive_fit_role": "screen_only_no_parameter_fit",
                "description": row["description"],
            }
        )
    return rows


def build_fit_parameter_summary(control_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fit_candidate_count = sum(
        1 for row in control_rows if str(row["fit_use_status"]).startswith("fit_candidate")
    )
    validation_only_count = sum(
        1 for row in control_rows if str(row["fit_use_status"]).startswith("validation_only")
    )
    diagnostic_count = sum(
        1 for row in control_rows if str(row["fit_use_status"]).startswith("diagnostic_only")
    )
    blocked_count = sum(1 for row in control_rows if str(row["fit_use_status"]).startswith("blocked"))
    common_status = "blocked_pending_clean_thermal_admission_and_uncertainty"
    return [
        {
            "parameter_family": "external_hx",
            "parameter_name": "cooler_UA_multiplier_or_epsilon_NTU_parameter",
            "applies_to": "cooler_branch_HX_boundary",
            "initial_value": "1.0 after CFD duty parity calibration",
            "bounds_or_prior": "positive, low-dimensional, shared across Salt cases",
            "training_rows_available": 3,
            "validation_rows_available": 0,
            "fit_status": "highest_priority_next_fit_after heldout setup",
            "rationale": "P1 CFD cooler-duty replay reduces mean absolute Tmean error from 63.746 K to 4.456 K.",
        },
        {
            "parameter_family": "external_ambient",
            "parameter_name": "ambient_wall_h_multiplier",
            "applies_to": "ambient_wall segments excluding cooler/heater/junction connectors",
            "initial_value": "1.0",
            "bounds_or_prior": "positive, shared by segment role or global external environment",
            "training_rows_available": validation_only_count,
            "validation_rows_available": 0,
            "fit_status": common_status,
            "rationale": "Segment external hA values are available, but wall flux includes inseparable rcExternalTemperature radiation.",
        },
        {
            "parameter_family": "external_radiation",
            "parameter_name": "rcExternalTemperature_effective_radiation_scale",
            "applies_to": "rcExternalTemperature wall heat flux",
            "initial_value": "fixed_1.0",
            "bounds_or_prior": "do not separate until OpenFOAM emits a radiation ledger or a controlled rerun exists",
            "training_rows_available": 0,
            "validation_rows_available": 0,
            "fit_status": "blocked_inseparable_from_wallHeatFlux",
            "rationale": "AGENT-264 found emissivity/Tsur affect heat flux but no separate radiation output term is available.",
        },
        {
            "parameter_family": "internal_nu",
            "parameter_name": "global_internal_Nu_multiplier",
            "applies_to": "pipe-flow Nu law in 1D thermal model",
            "initial_value": "1.0",
            "bounds_or_prior": "positive, one global multiplier before segment-specific terms",
            "training_rows_available": fit_candidate_count,
            "validation_rows_available": 0,
            "fit_status": common_status,
            "rationale": "CFD Nu is a postprocessed effective quantity; current segment rows are mesh-unestablished or diagnostic.",
        },
        {
            "parameter_family": "internal_profile",
            "parameter_name": "thermal_development_or_profile_descriptor",
            "applies_to": "lower_leg/upcomer/downcomer effective internal HTC trend",
            "initial_value": "0.0 correction",
            "bounds_or_prior": "low-dimensional monotone or sign-constrained descriptor",
            "training_rows_available": diagnostic_count,
            "validation_rows_available": 0,
            "fit_status": common_status,
            "rationale": "High recirculation and reconstructed-T blockers prevent profile terms from being fit-safe now.",
        },
        {
            "parameter_family": "admission_gate",
            "parameter_name": "heldout_case_and_time_mesh_uncertainty_gate",
            "applies_to": "all fitted thermal corrections",
            "initial_value": "required",
            "bounds_or_prior": "no thesis-strength claim before heldout, time-window, and mesh uncertainty pass",
            "training_rows_available": fit_candidate_count,
            "validation_rows_available": 0,
            "fit_status": "required_before_predictive_claim",
            "rationale": f"Current control-volume statuses: fit={fit_candidate_count}, validation={validation_only_count}, diagnostic={diagnostic_count}, blocked={blocked_count}.",
        },
    ]


def build_heldout_validation_scores(replay_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_case_path = {(row["case_id"], row["path_id"]): row for row in replay_rows}
    cases = sorted({row["case_id"] for row in replay_rows})
    output: list[dict[str, object]] = []
    for case_id in cases:
        p0 = by_case_path[(case_id, "P0_fixed_mdot_current_1d_contract")]
        p1 = by_case_path[(case_id, "P1_cfd_cooler_duty_only")]
        p0_error = num(p0["Tmean_error_K"]) or 0.0
        p1_error = num(p1["Tmean_error_K"]) or 0.0
        reduction, pct = cooler_error_reduction(p0_error, p1_error)
        train_cases = [case for case in cases if case != case_id]
        output.append(
            {
                "heldout_case_id": case_id,
                "candidate_training_cases": ";".join(train_cases),
                "baseline_abs_Tmean_error_K": abs(p0_error),
                "cooler_duty_parity_abs_Tmean_error_K": abs(p1_error),
                "cooler_duty_parity_improvement_K": reduction,
                "cooler_duty_parity_improvement_pct": pct,
                "validation_status": "readiness_only_no_parameters_fit",
                "admission_note": "mainline Salt2-4 diagnostic rows only; corrected-Q and low-heat heldout rows are not admitted here",
            }
        )
    return output


def count_interface_flags(interface_rows: list[dict[str, str]]) -> dict[str, int]:
    high_backflow = 0
    no_qr = 0
    for row in interface_rows:
        flags = row.get("quality_flags", "")
        if "high_backflow_fraction" in flags:
            high_backflow += 1
        if row.get("radiation_output_term") == "absent_no_qr_output":
            no_qr += 1
    return {"high_backflow_interface_rows": high_backflow, "no_qr_interface_rows": no_qr}


def build_uncertainty_readiness(
    control_rows: list[dict[str, object]],
    interface_counts: dict[str, int],
) -> list[dict[str, object]]:
    fit_candidate_count = sum(
        1 for row in control_rows if str(row["fit_use_status"]).startswith("fit_candidate")
    )
    return [
        {
            "uncertainty_axis": "time_window_stationarity",
            "current_evidence": "late-window and replay digests exist for mainline rows",
            "ready_for_fit": "partial",
            "required_next_gate": "attach fitted correction scoring to late-window spread and corrected-Q terminal windows",
        },
        {
            "uncertainty_axis": "mesh_hydraulic",
            "current_evidence": "Salt2 pressure-only medium/fine family comparison completed; pressure-gradient fit-safe spans are limited",
            "ready_for_fit": "partial_pressure_only",
            "required_next_gate": "keep pressure-only admission separate from thermal UA/HTC/Nu",
        },
        {
            "uncertainty_axis": "mesh_thermal",
            "current_evidence": "current effective HTC/Nu rows are coarse or reconstructed-T blocked",
            "ready_for_fit": "no",
            "required_next_gate": "clean reconstructed T or validated decomposed-field thermal sampler plus mesh comparison",
        },
        {
            "uncertainty_axis": "radiation_separability",
            "current_evidence": "rcExternalTemperature heat flux includes emissivity/Tsur effect but no separate radiation ledger",
            "ready_for_fit": "no",
            "required_next_gate": "controlled radiation-parity rerun or solver output term before separating external convection and radiation",
        },
        {
            "uncertainty_axis": "interface_backflow",
            "current_evidence": f"{interface_counts['high_backflow_interface_rows']} interface rows carry high-backflow flags",
            "ready_for_fit": "diagnostic_only",
            "required_next_gate": "profile-aware interface sampling and sign review before internal Nu admission",
        },
        {
            "uncertainty_axis": "corrected_Q_low_heat_validation",
            "current_evidence": "corrected-Q policy/short-name work exists, but this package does not admit new rows",
            "ready_for_fit": "not_in_this_package",
            "required_next_gate": "row-specific admission after terminal/latest-time and uncertainty checks",
        },
        {
            "uncertainty_axis": "parameter_identifiability",
            "current_evidence": f"{fit_candidate_count} control-volume rows currently pass all fit-candidate gates in this synthesis",
            "ready_for_fit": "no",
            "required_next_gate": "fit HX boundary first, then add internal Nu/global external terms only if heldout residuals require them",
        },
    ]


def build_summary(
    control_rows: list[dict[str, object]],
    cooler_rows: list[dict[str, object]],
    replay_rows: list[dict[str, object]],
    interface_counts: dict[str, int],
) -> dict[str, object]:
    p0_errors = [
        row["abs_Tmean_error_K"]
        for row in replay_rows
        if row["path_id"] == "P0_fixed_mdot_current_1d_contract"
    ]
    p1_errors = [
        row["abs_Tmean_error_K"]
        for row in replay_rows
        if row["path_id"] == "P1_cfd_cooler_duty_only"
    ]
    fit_counts: dict[str, int] = {}
    for row in control_rows:
        status = str(row["fit_use_status"])
        group = status.split("_", 1)[0]
        fit_counts[group] = fit_counts.get(group, 0) + 1
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_id": "AGENT-270",
        "source_packages": SOURCE_PACKAGES,
        "control_volume_rows": len(control_rows),
        "cooler_hx_rows": len(cooler_rows),
        "replay_score_rows": len(replay_rows),
        "fit_use_status_counts": fit_counts,
        "fit_candidate_control_volume_rows": sum(
            1 for row in control_rows if str(row["fit_use_status"]).startswith("fit_candidate")
        ),
        "baseline_mean_abs_Tmean_error_K": mean(p0_errors) if p0_errors else None,
        "cooler_duty_parity_mean_abs_Tmean_error_K": mean(p1_errors) if p1_errors else None,
        "cooler_duty_mean_abs_error_reduction_K": (
            mean(p0_errors) - mean(p1_errors) if p0_errors and p1_errors else None
        ),
        "cooler_duty_mean_abs_error_reduction_pct": (
            100.0 * (mean(p0_errors) - mean(p1_errors)) / mean(p0_errors)
            if p0_errors and p1_errors and mean(p0_errors)
            else None
        ),
        "high_backflow_interface_rows": interface_counts["high_backflow_interface_rows"],
        "no_qr_interface_rows": interface_counts["no_qr_interface_rows"],
        "thermal_closure_admission_decision": "no_new_admission_changes",
        "primary_finding": "cooler/HX duty parity remains first-order; internal Nu/profile fitting is blocked until thermal admission and uncertainty gates clear",
    }


def make_readme(summary: dict[str, object]) -> str:
    return f"""# Predictive heat-loss path package

Task: `AGENT-270`

This package converts the current thermal evidence stack into a practical path
toward predictive heat loss. It is a synthesis package only: it does not edit
Fluid, launch OpenFOAM, mutate native solver outputs, or admit blocked thermal
rows into closure fits.

## Outputs

- `control_volume_effective_thermal_table.csv`: segment/control-volume table
  with CFD realized wall heat, imposed heat, external `hA`, physical-interface
  enthalpy residuals, and available effective internal `h`, `Nu`, and `UA'`.
- `cooler_hx_duty_comparison.csv`: separates the current 1D cooler/HX duty
  error from internal Nu and ambient-wall residual lanes.
- `one_d_replay_mode_scores.csv`: normalized fixed-mdot replay modes.
- `fit_parameter_summary.csv`: low-dimensional correction candidates and their
  current fit status.
- `heldout_validation_scores.csv`: held-out Salt2/3/4 readiness scaffold only;
  no fitted parameters are claimed.
- `uncertainty_readiness.csv`: time-window, mesh, radiation, interface, and
  corrected-Q readiness gates.
- `summary.json`: machine-readable package summary.

## Main findings

1. The cooler/HX boundary remains first-order. The fixed-mdot baseline mean
   absolute Tmean error is {summary['baseline_mean_abs_Tmean_error_K']:.3f} K,
   while replacing only the predictive cooler duty with CFD cooler duty reduces
   it to {summary['cooler_duty_parity_mean_abs_Tmean_error_K']:.3f} K.
2. Current control-volume rows are useful diagnostics, but they are not
   thesis-strength thermal fit rows. The synthesis has
   {summary['fit_candidate_control_volume_rows']} fit-candidate rows after mesh,
   interface, and thermal-admission gates.
3. Radiation must stay inseparable from `rcExternalTemperature` wall heat flux
   until a separate solver output term or controlled rerun exists.
4. Internal Nu is treated as a postprocessed CFD effective quantity
   (`h_eff = q_wall / (T_wall - T_bulk)`, `Nu_eff = h_eff D_h/k_bulk`), while
   the 1D model remains a predictive resistance network. This package keeps
   those roles separate.

## Recommended next sequence

1. Fit the external cooler/HX parameterization first using held-out Salt cases.
2. Only after that residual is reduced, test one global internal Nu multiplier
   before segment/profile descriptors.
3. Add ambient external h/radiation terms only with an inseparable or
   explicitly audited radiation contract.
4. Promote corrected-Q/low-heat rows only after row-specific terminal,
   latest-time, and uncertainty admission checks.
5. Attach time-window and mesh uncertainty before making predictive claims.

## Source packages

{chr(10).join(f'- `{name}`: `{path}`' for name, path in SOURCE_PACKAGES.items())}
"""


def build_package(out_dir: Path = OUT_DIR) -> dict[str, object]:
    segment_rows = read_csv(SEGMENT_REDUCTION_CSV)
    role_rows = read_csv(PATCH_ROLE_SUMMARY_CSV)
    enthalpy_rows = read_csv(ENTHALPY_RESIDUALS_CSV)
    replay_raw_rows = read_csv(FIXED_MDOT_REPLAY_CSV)
    replay_summary_rows = read_csv(REMEDY_PATH_SUMMARY_CSV)
    interface_rows = read_csv(INTERFACE_SAMPLES_CSV)
    htc_rows = load_segment_htc_rows()

    control_rows = build_control_volume_effective_table(segment_rows, enthalpy_rows, htc_rows)
    cooler_rows = build_cooler_hx_duty_table(role_rows, replay_raw_rows)
    replay_rows = build_replay_mode_scores(replay_raw_rows, replay_summary_rows)
    fit_rows = build_fit_parameter_summary(control_rows)
    heldout_rows = build_heldout_validation_scores(replay_raw_rows)
    interface_counts = count_interface_flags(interface_rows)
    uncertainty_rows = build_uncertainty_readiness(control_rows, interface_counts)
    summary = build_summary(control_rows, cooler_rows, replay_rows, interface_counts)

    write_csv(
        out_dir / "control_volume_effective_thermal_table.csv",
        control_rows,
        [
            "source_id",
            "case_id",
            "one_d_segment",
            "component_parent_spans",
            "area_m2",
            "external_h_W_m2K",
            "external_hA_W_per_K",
            "area_weighted_Ta_K",
            "area_weighted_Tsur_K",
            "area_weighted_emissivity",
            "radiation_parity_mode",
            "realized_wallHeatFlux_W_positive_to_fluid",
            "imposed_Q_W_positive_to_fluid",
            "imposed_minus_realized_W",
            "abs_imposed_minus_realized_W",
            "enthalpy_change_W",
            "wallHeatFlux_vs_enthalpy_residual_W",
            "abs_enthalpy_residual_W",
            "residual_fraction",
            "bracket_status",
            "max_interface_recirc_ratio",
            "interface_quality_flags",
            "T_bulk_inlet_K",
            "T_bulk_outlet_K",
            "delta_T_K",
            "mdot_kg_s",
            "cp_jkgk",
            "effective_htc_W_m2K",
            "Nu_eff",
            "uaprime_W_mK",
            "T_wall_K",
            "T_bulk_for_htc_K",
            "internal_delta_T_K",
            "segment_htc_mesh",
            "segment_htc_mesh_independence",
            "thermal_effective_status",
            "fit_use_status",
        ],
    )
    write_csv(
        out_dir / "cooler_hx_duty_comparison.csv",
        cooler_rows,
        [
            "case_id",
            "baseline_1d_qhx_total_W",
            "cfd_cooler_imposed_abs_W",
            "cfd_cooler_realized_abs_W",
            "cfd_cooler_realized_minus_imposed_abs_W",
            "cooler_extra_removal_vs_baseline_1d_W",
            "baseline_Tmean_error_K",
            "cfd_cooler_duty_Tmean_error_K",
            "Tmean_abs_error_reduction_K",
            "Tmean_abs_error_reduction_pct",
            "cooler_duty_mismatch_class",
        ],
    )
    write_csv(
        out_dir / "one_d_replay_mode_scores.csv",
        replay_rows,
        [
            "case_id",
            "path_id",
            "mode_family",
            "root_found",
            "Tmean_error_K",
            "abs_Tmean_error_K",
            "loop_delta_T_error_K",
            "qhx_total_W",
            "qambient_total_W",
            "source_total_W",
            "prescribed_loss_total_W",
            "mean_abs_Tmean_error_K_by_path",
            "passes_thermal_gate",
            "predictive_fit_role",
            "description",
        ],
    )
    write_csv(
        out_dir / "fit_parameter_summary.csv",
        fit_rows,
        [
            "parameter_family",
            "parameter_name",
            "applies_to",
            "initial_value",
            "bounds_or_prior",
            "training_rows_available",
            "validation_rows_available",
            "fit_status",
            "rationale",
        ],
    )
    write_csv(
        out_dir / "heldout_validation_scores.csv",
        heldout_rows,
        [
            "heldout_case_id",
            "candidate_training_cases",
            "baseline_abs_Tmean_error_K",
            "cooler_duty_parity_abs_Tmean_error_K",
            "cooler_duty_parity_improvement_K",
            "cooler_duty_parity_improvement_pct",
            "validation_status",
            "admission_note",
        ],
    )
    write_csv(
        out_dir / "uncertainty_readiness.csv",
        uncertainty_rows,
        ["uncertainty_axis", "current_evidence", "ready_for_fit", "required_next_gate"],
    )
    write_json(out_dir / "summary.json", summary)
    (out_dir / "README.md").write_text(make_readme(summary))
    return summary


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_package(args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
