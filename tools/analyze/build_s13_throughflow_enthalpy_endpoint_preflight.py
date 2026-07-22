#!/usr/bin/env python3
"""Build the S13 throughflow enthalpy endpoint preflight package.

This is a fail-closed readiness pass. It defines the throughflow endpoint
contract needed by the S13 residual-complete open-CV equation and checks
whether completed packages already contain same-basis endpoint, mdot, T_bulk,
cp, storage, and named-loss evidence. It does not launch OpenFOAM/postProcess,
sample native output, compute residual values, or release cp/Qwall/source values.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TODO-S13-THROUGHFLOW-ENTHALPY-ENDPOINT-PREFLIGHT-2026-07-22"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight"

RESIDUAL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"
EXACT_LABEL = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun"
SOURCE_PROPERTY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight"
POSTPROC = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_salt14_postprocessing_inventory_model_form_package"
OLD_SPAN = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_span_endpoint_temperatures"
OLD_INTERFACES = ROOT / "work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces"

CASE_SOURCE_ID = {
    "salt_2": "viscosity_screening_salt_test_2_jin_coarse_mesh",
    "salt_3": "viscosity_screening_salt_test_3_jin_coarse_mesh",
    "salt_4": "viscosity_screening_salt_test_4_jin_coarse_mesh",
}
CASE_POSTPROC_ID = {
    "salt_2": "salt_test_2_jin",
    "salt_3": "salt_test_3_jin",
    "salt_4": "salt_test_4_jin",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def fnum(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def fmt(value: Any, digits: int = 12) -> str:
    parsed = fnum(value)
    if parsed is None:
        return ""
    return f"{parsed:.{digits}g}"


def require_inputs() -> None:
    required = [
        RESIDUAL / "summary.json",
        RESIDUAL / "required_input_matrix.csv",
        RESIDUAL / "throughflow_enthalpy_harvest_contract.csv",
        RESIDUAL / "case_budget_skeleton.csv",
        EXACT_LABEL / "summary.json",
        EXACT_LABEL / "aggregated_terminal_window_reductions.csv",
        SOURCE_PROPERTY / "field_release_contract.csv",
        POSTPROC / "summary.json",
        POSTPROC / "salt14_postprocessing_window_stats.csv",
        OLD_SPAN / "span_endpoint_temperatures.csv",
        OLD_INTERFACES / "interface_temperature_samples.csv",
    ]
    missing = [rel(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing S13 throughflow preflight inputs: " + "; ".join(missing))


def load_upcomer_interface_rows() -> dict[str, list[dict[str, str]]]:
    rows = read_csv(OLD_INTERFACES / "interface_temperature_samples.csv")
    grouped: dict[str, list[dict[str, str]]] = {case: [] for case in CASE_SOURCE_ID}
    for row in rows:
        case = row.get("case_id", "")
        if case in grouped and row.get("physical_segment") == "upcomer":
            grouped[case].append(row)
    return grouped


def load_postproc_support() -> dict[str, dict[str, Any]]:
    keep = {case: {"mdot_rows": 0, "temperature_rows": 0, "max_mdot_rel_std_pct": "", "max_temperature_std_K": ""} for case in CASE_SOURCE_ID}
    max_mdot_rel: dict[str, float] = {case: 0.0 for case in CASE_SOURCE_ID}
    max_temp_std: dict[str, float] = {case: 0.0 for case in CASE_SOURCE_ID}
    with (POSTPROC / "salt14_postprocessing_window_stats.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            case = next((key for key, post_id in CASE_POSTPROC_ID.items() if row.get("case_id") == post_id), None)
            if case is None:
                continue
            quantity = row.get("quantity", "")
            if quantity == "mdot_kg_s":
                keep[case]["mdot_rows"] += 1
                mean = abs(fnum(row.get("mean")) or 0.0)
                std = abs(fnum(row.get("std")) or 0.0)
                if mean > 0.0:
                    max_mdot_rel[case] = max(max_mdot_rel[case], 100.0 * std / mean)
            elif quantity in {"temperature_K", "temperature_station_avg_K", "slab_T_K"}:
                keep[case]["temperature_rows"] += 1
                std = abs(fnum(row.get("std")) or 0.0)
                max_temp_std[case] = max(max_temp_std[case], std)
    for case in keep:
        keep[case]["max_mdot_rel_std_pct"] = fmt(max_mdot_rel[case], 6)
        keep[case]["max_temperature_std_K"] = fmt(max_temp_std[case], 6)
    return keep


def exact_label_counts() -> dict[str, dict[str, Any]]:
    rows = read_csv(EXACT_LABEL / "aggregated_terminal_window_reductions.csv")
    out: dict[str, dict[str, Any]] = {
        case: {
            "exact_label_rows": 0,
            "mesh_levels": set(),
            "window_roles": set(),
            "qoi_labels": set(),
            "has_Q_wall_W": False,
            "has_exchange_mdot_proxy": False,
            "has_throughflow_enthalpy": False,
        }
        for case in CASE_SOURCE_ID
    }
    for row in rows:
        case = row.get("case_id", "")
        if case not in out:
            continue
        item = out[case]
        item["exact_label_rows"] += 1
        item["mesh_levels"].add(row.get("mesh_level", ""))
        item["window_roles"].add(row.get("window_role", ""))
        qoi = row.get("qoi_label", "")
        item["qoi_labels"].add(qoi)
        item["has_Q_wall_W"] = item["has_Q_wall_W"] or qoi == "Q_wall_W"
        item["has_exchange_mdot_proxy"] = item["has_exchange_mdot_proxy"] or qoi == "mdot_exchange_positive_outward_proxy_kg_s"
        item["has_throughflow_enthalpy"] = item["has_throughflow_enthalpy"] or qoi == "H_throughflow_net_W"
    for item in out.values():
        item["mesh_levels"] = ";".join(sorted(item["mesh_levels"]))
        item["window_roles"] = ";".join(sorted(item["window_roles"]))
        item["qoi_labels"] = ";".join(sorted(item["qoi_labels"]))
    return out


def cp_release_ready() -> bool:
    rows = read_csv(SOURCE_PROPERTY / "field_release_contract.csv")
    for row in rows:
        if row.get("field_or_basis") == "cp_J_kg_K":
            return str(row.get("release_ready", "")).lower() == "true"
    return False


def build_endpoint_definition_contract(case_budgets: list[dict[str, str]]) -> list[dict[str, Any]]:
    upcomer = load_upcomer_interface_rows()
    rows: list[dict[str, Any]] = []
    for budget in case_budgets:
        case = budget["case_id"]
        endpoints = upcomer.get(case, [])
        inlet = next((row for row in endpoints if row.get("interface_role") == "physical_segment_inlet"), {})
        outlet = next((row for row in endpoints if row.get("interface_role") == "physical_segment_outlet"), {})
        inlet_recirc = fnum(inlet.get("recirculation_ratio"))
        outlet_recirc = fnum(outlet.get("recirculation_ratio"))
        max_recirc = max([value for value in [inlet_recirc, outlet_recirc] if value is not None], default=None)
        rows.append(
            {
                "case_id": case,
                "target_time_window_s": budget["target_time_window_s"],
                "throughflow_cv": "composite_upcomer_open_cv",
                "inlet_endpoint": "left_lower_leg:s00",
                "outlet_endpoint": "left_upper_leg:s04",
                "positive_mdot_convention": "positive along nominal main throughflow from lower-left upcomer inlet to upper-left outlet",
                "historical_endpoint_rows": len(endpoints),
                "historical_endpoint_status": "coarse_diagnostic_available" if len(endpoints) >= 2 else "missing",
                "historical_inlet_T_used_K": inlet.get("T_used_K", ""),
                "historical_outlet_T_used_K": outlet.get("T_used_K", ""),
                "historical_max_endpoint_recirculation_ratio": fmt(max_recirc),
                "same_basis_harvest_ready": False,
                "blocking_reason": "historical coarse endpoint temperatures are not a released same-basis S13 residual row; true throughflow mdot, cp release, storage, and named losses are still missing",
            }
        )
    return rows


def build_required_input_status(
    case_budgets: list[dict[str, str]],
    exact_counts: dict[str, dict[str, Any]],
    postproc: dict[str, dict[str, Any]],
    cp_ready: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    requirements = [
        ("throughflow_endpoint_face_masks", "endpoint-mask", "coarse physical-segment endpoints exist only as historical diagnostic surfaces", False),
        ("throughflow_normal_convention", "normal", "nominal main-throughflow direction defined in preflight; no released same-basis endpoint face normals", False),
        ("T_in_bulk_K", "thermal-field", "historical coarse endpoint T exists; current same-basis S13 endpoint T missing", False),
        ("T_out_bulk_K", "thermal-field", "historical coarse endpoint T exists; current same-basis S13 endpoint T missing", False),
        ("mdot_throughflow_kg_s", "mass-flow", "postProcessing loop mdot rows exist but CFD mdot is forbidden as predictive runtime input and not an endpoint surface integral", False),
        ("cp_J_kg_K", "property", "row-specific cp release remains blocked" if not cp_ready else "cp release ready", cp_ready),
        ("Q_storage_W", "storage", "storage/drift lane not proven negligible on same CV/window", False),
        ("Q_other_named_losses_W", "loss-owner", "named non-wall source/sink/loss owner manifest missing", False),
        ("same_window_Q_wall_W_and_Q_source", "heat-flow", "S13 Q_wall/source skeleton exists, but Qwall/source release and formal GCI remain closed", False),
    ]
    for budget in case_budgets:
        case = budget["case_id"]
        for label, kind, evidence, ready in requirements:
            exact = exact_counts[case]
            if label == "same_window_Q_wall_W_and_Q_source":
                evidence = (
                    f"exact_label_rows={exact['exact_label_rows']}; Q_wall_W={exact['has_Q_wall_W']}; "
                    f"exchange_mdot_proxy={exact['has_exchange_mdot_proxy']}; H_throughflow_net_W={exact['has_throughflow_enthalpy']}"
                )
            if label == "mdot_throughflow_kg_s":
                evidence = (
                    f"postProcessing mdot rows={postproc[case]['mdot_rows']}; "
                    f"max_rel_std_pct={postproc[case]['max_mdot_rel_std_pct']}; no endpoint mdot_throughflow_kg_s release"
                )
            rows.append(
                {
                    "case_id": case,
                    "target_time_window_s": budget["target_time_window_s"],
                    "required_label": label,
                    "input_kind": kind,
                    "current_evidence": evidence,
                    "release_or_harvest_ready": ready,
                    "admissibility_role": "required_for_residual_value",
                    "next_action": next_action_for(label),
                }
            )
    return rows


def next_action_for(label: str) -> str:
    actions = {
        "throughflow_endpoint_face_masks": "generate staged endpoint face masks for composite_upcomer_open_cv inlet/outlet",
        "throughflow_normal_convention": "publish endpoint normal/sign convention with continuity mismatch columns",
        "T_in_bulk_K": "sample mass-flux-weighted inlet T_bulk on same window and endpoint faces",
        "T_out_bulk_K": "sample mass-flux-weighted outlet T_bulk on same window and endpoint faces",
        "mdot_throughflow_kg_s": "surface-integrate rho*U dot n on inlet/outlet endpoint faces and report mismatch",
        "cp_J_kg_K": "complete row-specific cp/source-property release gate before enthalpy residual use",
        "Q_storage_W": "quantify storage or mark residual incomplete with explicit storage lane",
        "Q_other_named_losses_W": "inventory named losses/sinks/sources for the same open CV",
        "same_window_Q_wall_W_and_Q_source": "join same-window heat-flow rows to throughflow endpoint rows without relabeling source-side heat as Q_wall",
    }
    return actions[label]


def build_existing_evidence_disposition(
    exact_counts: dict[str, dict[str, Any]], postproc: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    exact_total = sum(int(item["exact_label_rows"]) for item in exact_counts.values())
    return [
        {
            "evidence_family": "S13_residual_contract",
            "source_path": rel(RESIDUAL / "throughflow_enthalpy_harvest_contract.csv"),
            "status": "defines_required_labels_fail_closed",
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "equation and required labels are defined, but required input matrix has 0 same-basis residual-computable rows",
        },
        {
            "evidence_family": "S13_medium_fine_exact_exchange_rows",
            "source_path": rel(EXACT_LABEL / "aggregated_terminal_window_reductions.csv"),
            "status": f"exact_exchange_QOI_rows_present={exact_total}",
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "rows cover Q_wall_W, exchange mdot proxy, tau, and wall/core contrast, not H_throughflow_net_W endpoint enthalpy",
        },
        {
            "evidence_family": "historical_coarse_upcomer_endpoint_T",
            "source_path": rel(OLD_INTERFACES / "interface_temperature_samples.csv"),
            "status": "coarse_upcomer_endpoint_temperature_rows_exist",
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "coarse reconstructed endpoint T rows are not current same-basis S13 residual rows and include high-recirculation inlet flags",
        },
        {
            "evidence_family": "salt14_postProcessing_window_stats",
            "source_path": rel(POSTPROC / "salt14_postprocessing_window_stats.csv"),
            "status": "diagnostic_mdot_and_temperature_stats_present",
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "postProcessing mdot/probe values are diagnostic and forbidden as predictive runtime inputs; not endpoint-face enthalpy integrals",
        },
        {
            "evidence_family": "source_property_cp_gate",
            "source_path": rel(SOURCE_PROPERTY / "field_release_contract.csv"),
            "status": "cp_release_ready_false",
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "row-specific cp/source-property provenance and split permission are not released",
        },
        {
            "evidence_family": "postproc_support_counts",
            "source_path": rel(POSTPROC / "summary.json"),
            "status": ";".join(
                f"{case}:mdot={postproc[case]['mdot_rows']},T={postproc[case]['temperature_rows']}" for case in sorted(postproc)
            ),
            "usable_for_preflight": True,
            "usable_for_residual_value": False,
            "reason": "supports drift/error documentation only",
        },
    ]


def build_postprocessing_support_summary(postproc: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case, item in postproc.items():
        rows.append(
            {
                "case_id": case,
                "postprocessing_case_id": CASE_POSTPROC_ID[case],
                "mdot_window_stat_rows": item["mdot_rows"],
                "temperature_window_stat_rows": item["temperature_rows"],
                "max_mdot_rel_std_pct": item["max_mdot_rel_std_pct"],
                "max_temperature_std_K": item["max_temperature_std_K"],
                "admissibility_role": "diagnostic_drift_and_error_support_only",
                "why_not_residual_input": "CFD mdot/probe temperatures are not same-basis throughflow endpoint enthalpy inputs and remain forbidden as predictive runtime inputs",
            }
        )
    return rows


def build_sampling_command_contract(case_budgets: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for budget in case_budgets:
        case = budget["case_id"]
        source_id = CASE_SOURCE_ID[case]
        time_s = budget["target_time_window_s"]
        staged = f"$TASK_STAGED_CASES/{case}_throughflow_endpoint_preflight"
        rows.append(
            {
                "case_id": case,
                "source_id": source_id,
                "target_time_window_s": time_s,
                "step_order": 1,
                "command_label": "stage_read_only_case_copy",
                "command": f"cp -a <trusted_case_root_for_{case}> {staged}",
                "run_now": False,
                "required_environment": "future compute/staging row",
                "output_expected": f"{staged}/system/controlDict",
                "guardrail": "stage first; do not write controlDict into native/source case",
            }
        )
        rows.append(
            {
                "case_id": case,
                "source_id": source_id,
                "target_time_window_s": time_s,
                "step_order": 2,
                "command_label": "write_endpoint_sampling_control_dict",
                "command": (
                    "python3 tools/extract/sample_physical_segment_interface_temperatures.py "
                    f"write-control-dict --case-dir {staged} --time {time_s} "
                    f"--source-id {source_id} --case-id {case}"
                ),
                "run_now": False,
                "required_environment": "future compute/staging row",
                "output_expected": "thermalInterfaceSurfaces point-and-normal planes for upcomer endpoint faces",
                "guardrail": "command mutates staged system/controlDict only",
            }
        )
        rows.append(
            {
                "case_id": case,
                "source_id": source_id,
                "target_time_window_s": time_s,
                "step_order": 3,
                "command_label": "run_openfoam_sampling_on_compute",
                "command": f"postProcess -case {staged} -func thermalInterfaceSurfaces -time {time_s}",
                "run_now": False,
                "required_environment": "compute node with OpenFOAM environment",
                "output_expected": f"{staged}/postProcessing/thermalInterfaceSurfaces/{time_s}/",
                "guardrail": "do not run on login node; no native/source mutation",
            }
        )
        rows.append(
            {
                "case_id": case,
                "source_id": source_id,
                "target_time_window_s": time_s,
                "step_order": 4,
                "command_label": "parse_endpoint_samples",
                "command": (
                    "python3 tools/extract/sample_physical_segment_interface_temperatures.py "
                    f"parse-openfoam-samples --case-dir {staged} --time {time_s} "
                    f"--source-id {source_id} --case-id {case} --output-dir <task_output_dir>/{case}"
                ),
                "run_now": False,
                "required_environment": "login-safe after sampled raw files exist",
                "output_expected": "openfoam_interface_samples.csv with T_bulk, mdot proxies, backflow fractions",
                "guardrail": "parse only; residual value remains blocked until cp/storage/named-loss gates pass",
            }
        )
    return rows


def build_next_compute_contract() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "command_type": "preflight_only",
            "exact_action": "construct endpoint face-mask manifest for the same S13 open CV and target windows",
            "expected_outputs": "endpoint mask IDs, area vectors, normal sign convention, case/time mapping",
            "scheduler": "no_launch_from_this_row",
            "stop_condition": "stop if endpoint masks cannot be tied to the residual-complete open CV",
        },
        {
            "step": 2,
            "command_type": "future_compute_row",
            "exact_action": "sample rho, U, T on inlet/outlet endpoint faces at Salt2/Salt3/Salt4 target windows",
            "expected_outputs": "mdot_in, mdot_out, continuity mismatch, T_in_bulk, T_out_bulk",
            "scheduler": "use_sbatch_if_extract_exceeds_5_minutes",
            "stop_condition": "stop before residual values if cp/source-property release is still false",
        },
        {
            "step": 3,
            "command_type": "future_release_gate",
            "exact_action": "join endpoint enthalpy rows to row-specific cp_J_kg_K/source-property evidence and storage/named-loss owner rows",
            "expected_outputs": "same-basis residual input ledger, not residual-fitted Nu",
            "scheduler": "no_solver_launch",
            "stop_condition": "stop if any row uses protected temperatures, native mass-flow monitor values as predictive inputs, or a hidden residual multiplier",
        },
    ]


def build_residual_gate(required_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(required_rows)
    ready = sum(1 for row in required_rows if row["release_or_harvest_ready"] is True)
    return [
        {
            "gate": "endpoint_contract_defined",
            "status": "pass_preflight_only",
            "pass": True,
            "evidence": "composite_upcomer_open_cv inlet/outlet endpoints defined from existing physical-segment sampler convention",
            "next_action": "turn endpoint contract into staged same-window sampler row",
        },
        {
            "gate": "same_basis_required_inputs",
            "status": "fail_closed",
            "pass": False,
            "evidence": f"ready_required_rows={ready}/{total}",
            "next_action": "generate endpoint masks, normals, T_bulk, mdot_throughflow, cp release, storage, and named-loss rows",
        },
        {
            "gate": "residual_value_release",
            "status": "blocked",
            "pass": False,
            "evidence": "no case has all required same-basis labels",
            "next_action": "do not compute or publish R_E_combined_W",
        },
        {
            "gate": "production_or_admission",
            "status": "closed",
            "pass": False,
            "evidence": "source/property/Qwall/GCI/freeze gates remain closed",
            "next_action": "continue pre-admission evidence harvest only",
        },
    ]


def build_no_mutation_guardrails() -> list[dict[str, Any]]:
    return [
        {"guardrail": "native_solver_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_uq_launched", "status": False},
        {"guardrail": "source_property_or_Qwall_release", "status": False},
        {"guardrail": "residual_value_released", "status": False},
        {"guardrail": "coefficient_admission_or_candidate_freeze", "status": False},
        {"guardrail": "protected_or_final_score", "status": False},
        {"guardrail": "hidden_multiplier_or_internal_Nu_absorption", "status": False},
        {"guardrail": "endpoint_proxy_substitution", "status": False},
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [
        {"role": "residual_contract", "path": rel(RESIDUAL / "throughflow_enthalpy_harvest_contract.csv")},
        {"role": "residual_required_inputs", "path": rel(RESIDUAL / "required_input_matrix.csv")},
        {"role": "residual_case_budget_skeleton", "path": rel(RESIDUAL / "case_budget_skeleton.csv")},
        {"role": "s13_exact_label_terminal_rows", "path": rel(EXACT_LABEL / "aggregated_terminal_window_reductions.csv")},
        {"role": "source_property_cp_gate", "path": rel(SOURCE_PROPERTY / "field_release_contract.csv")},
        {"role": "postprocessing_window_stats", "path": rel(POSTPROC / "salt14_postprocessing_window_stats.csv")},
        {"role": "historical_span_endpoint_temperatures", "path": rel(OLD_SPAN / "span_endpoint_temperatures.csv")},
        {"role": "historical_interface_temperature_samples", "path": rel(OLD_INTERFACES / "interface_temperature_samples.csv")},
        {"role": "endpoint_sampler_helper", "path": "tools/extract/sample_physical_segment_interface_temperatures.py"},
    ]


def build_methodology() -> str:
    return """# Methodology And Assumptions

This package is a preflight/readiness pass for the S13 residual-complete
open-CV equation. It does not sample native solver output, run OpenFOAM,
compute `R_E_combined_W`, release cp/Qwall/source values, fit coefficients, or
score protected rows.

Method:

1. Treat the completed S13 residual contract as authoritative for required
   labels and sign convention.
2. Define the throughflow endpoint pair as the composite upcomer open CV:
   inlet `left_lower_leg:s00`, outlet `left_upper_leg:s04`, positive in the
   nominal main-throughflow direction.
3. Audit completed evidence for exact same-basis labels. Historical coarse
   endpoint temperatures and postProcessing mdot/probe statistics are allowed
   as diagnostic support only.
4. Fail closed unless every case has same-window endpoint masks, normals,
   `T_in_bulk_K`, `T_out_bulk_K`, `mdot_throughflow_kg_s`, released cp,
   storage, named-loss lanes, and same-window heat-flow rows.
5. Emit a command contract for a future staged compute row, but do not launch
   that row here.

Assumptions:

- Historical coarse endpoint samples are useful for geometry/method sanity but
  are not current S13 residual rows.
- Existing postProcessing mdot values describe loop stability and uncertainty
  context, but CFD mdot remains forbidden as a predictive runtime input.
- Existing S13 exact-label rows describe exchange-cell QOIs; they do not
  substitute for throughflow endpoint enthalpy.
- Missing storage or named-loss terms keep the residual incomplete rather than
  being absorbed into internal Nu or a hidden multiplier.
"""


def write_readme(summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(RESIDUAL / 'summary.json')}
  - {rel(RESIDUAL / 'throughflow_enthalpy_harvest_contract.csv')}
  - {rel(EXACT_LABEL / 'aggregated_terminal_window_reductions.csv')}
tags: [work-product, s13, throughflow, enthalpy, open-cv, fail-closed]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/s13-throughflow-enthalpy-endpoint-preflight.md
task: {TASK_ID}
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Throughflow Enthalpy Endpoint Preflight

Decision: `{summary['decision']}`.

The composite upcomer throughflow endpoint contract is now explicit, but no
same-basis residual value can be computed. Existing S13 medium/fine rows cover
exchange-cell QOIs, while historical endpoint temperatures and postProcessing
mdot/T summaries remain diagnostic support only.

Current outcome:

- Case endpoint contracts: `{summary['case_endpoint_contract_rows']}`.
- Required input status rows: `{summary['required_input_status_rows']}`.
- Harvest-ready cases: `{summary['harvest_ready_cases']}`.
- Residual values released: `{summary['residual_value_released_rows']}`.

Next exact row: staged same-window throughflow endpoint sampler for Salt2,
Salt3, and Salt4, followed by cp/source-property release and storage/named-loss
owner evidence before any residual/admission attempt.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def build() -> dict[str, Any]:
    require_inputs()
    case_budgets = read_csv(RESIDUAL / "case_budget_skeleton.csv")
    exact_counts = exact_label_counts()
    postproc = load_postproc_support()
    cp_ready = cp_release_ready()

    endpoint_contract = build_endpoint_definition_contract(case_budgets)
    required_status = build_required_input_status(case_budgets, exact_counts, postproc, cp_ready)
    evidence = build_existing_evidence_disposition(exact_counts, postproc)
    postproc_summary = build_postprocessing_support_summary(postproc)
    command_contract = build_sampling_command_contract(case_budgets)
    next_compute_contract = build_next_compute_contract()
    residual_gate = build_residual_gate(required_status)
    guardrails = build_no_mutation_guardrails()
    source_manifest = build_source_manifest()

    write_csv(
        OUT / "endpoint_definition_contract.csv",
        endpoint_contract,
        [
            "case_id",
            "target_time_window_s",
            "throughflow_cv",
            "inlet_endpoint",
            "outlet_endpoint",
            "positive_mdot_convention",
            "historical_endpoint_rows",
            "historical_endpoint_status",
            "historical_inlet_T_used_K",
            "historical_outlet_T_used_K",
            "historical_max_endpoint_recirculation_ratio",
            "same_basis_harvest_ready",
            "blocking_reason",
        ],
    )
    write_csv(
        OUT / "required_input_status_matrix.csv",
        required_status,
        [
            "case_id",
            "target_time_window_s",
            "required_label",
            "input_kind",
            "current_evidence",
            "release_or_harvest_ready",
            "admissibility_role",
            "next_action",
        ],
    )
    write_csv(
        OUT / "existing_evidence_disposition.csv",
        evidence,
        ["evidence_family", "source_path", "status", "usable_for_preflight", "usable_for_residual_value", "reason"],
    )
    write_csv(
        OUT / "postprocessing_support_summary.csv",
        postproc_summary,
        [
            "case_id",
            "postprocessing_case_id",
            "mdot_window_stat_rows",
            "temperature_window_stat_rows",
            "max_mdot_rel_std_pct",
            "max_temperature_std_K",
            "admissibility_role",
            "why_not_residual_input",
        ],
    )
    write_csv(
        OUT / "sampling_command_contract.csv",
        command_contract,
        [
            "case_id",
            "source_id",
            "target_time_window_s",
            "step_order",
            "command_label",
            "command",
            "run_now",
            "required_environment",
            "output_expected",
            "guardrail",
        ],
    )
    write_csv(
        OUT / "next_compute_contract.csv",
        next_compute_contract,
        ["step", "command_type", "exact_action", "expected_outputs", "scheduler", "stop_condition"],
    )
    write_csv(
        OUT / "residual_readiness_gate.csv",
        residual_gate,
        ["gate", "status", "pass", "evidence", "next_action"],
    )
    write_csv(OUT / "no_mutation_guardrails.csv", guardrails, ["guardrail", "status"])
    write_csv(OUT / "source_manifest.csv", source_manifest, ["role", "path"])
    (OUT / "methodology_and_assumptions.md").write_text(build_methodology(), encoding="utf-8")

    summary = {
        "task_id": TASK_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": "s13_throughflow_endpoint_preflight_complete_fail_closed_no_residual_value",
        "case_endpoint_contract_rows": len(endpoint_contract),
        "required_input_status_rows": len(required_status),
        "existing_evidence_disposition_rows": len(evidence),
        "postprocessing_support_rows": len(postproc_summary),
        "sampling_command_rows": len(command_contract),
        "next_compute_contract_rows": len(next_compute_contract),
        "residual_gate_rows": len(residual_gate),
        "harvest_ready_cases": sum(1 for row in endpoint_contract if row["same_basis_harvest_ready"] is True),
        "same_basis_residual_computable_cases": 0,
        "residual_value_released_rows": 0,
        "source_property_release": False,
        "Qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "validation_holdout_external_scoring": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "native_solver_outputs_mutated": False,
        "registry_or_admission_mutated": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "fluid_or_external_edit": False,
        "thesis_body_or_latex_edit": False,
        "hidden_multiplier_or_internal_Nu_absorption": False,
        "endpoint_proxy_substitution": False,
    }
    write_json(OUT / "summary.json", summary)
    write_readme(summary)
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
