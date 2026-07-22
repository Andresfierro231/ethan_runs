#!/usr/bin/env python3
"""Build the S13 residual-complete open-CV energy-balance contract."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATE = "2026-07-22"
TASK_ID = "TODO-S13-RESIDUAL-COMPLETE-OPEN-CV-ENERGY-BALANCE-CONTRACT-2026-07-22"
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract"

BULK_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility"
OPEN_CV_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract"
SOURCE_PROP_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight"
RECON_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def fnum(value: str) -> float:
    return float(value)


def readme_text(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract/residual_equation_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract/case_budget_skeleton.csv
tags: [s13, open-cv, energy-balance, fail-closed, no-admission]
related:
  - .agent/status/2026-07-22_TODO-S13-RESIDUAL-COMPLETE-OPEN-CV-ENERGY-BALANCE-CONTRACT-2026-07-22.md
  - .agent/journal/2026-07-22/s13-residual-complete-open-cv-energy-balance-contract.md
  - imports/2026-07-22_s13_residual_complete_open_cv_energy_balance_contract.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product_readme
status: complete
---
# S13 Residual-Complete Open-CV Energy-Balance Contract

Decision: `{summary["decision"]}`.

This package converts the stable S13 bulk-integral heat-partition diagnostic
into an explicit residual-complete open-CV contract. The residual equation is
defined, but no residual value is released because same-basis cp/property,
throughflow enthalpy endpoints, storage/named-loss terms, source/property
release, and mesh/GCI gates remain incomplete.

## Key Counts

- Case budget skeleton rows: `{summary["case_budget_rows"]}`.
- Missing input/gate rows: `{summary["missing_input_gate_rows"]}`.
- Harvest lane requirement rows: `{summary["harvest_lane_rows"]}`.
- Required input rows: `{summary["required_input_rows"]}`.
- Same-basis residual-computable rows: `0`.
- Residual values released: `0`.
- Formal GCI-ready rows: `0`.

## Outputs

- `residual_equation_contract.csv`: equation, signs, and open-CV policy.
- `case_budget_skeleton.csv`: S13 case-level source-side, wall, remaining heat, and implied cp scales.
- `missing_input_gate.csv`: exact blockers before residual values can be used.
- `harvest_lane_requirements.csv`: next sampler/harvest lanes needed.
- `required_input_matrix.csv`: exact residual input labels and release status.
- `storage_and_named_loss_policy.csv`: storage/loss fail-closed policy.
- `predictive_1d_progression_ladder.csv`: next phases toward a predictive 1D model.
- `progression_gate.csv`: current pass/fail gates.
- `admission_guardrails.csv`: no-release/no-admission rules.
- `source_manifest.csv`: exact source tables consumed.
- `summary.json`: machine-readable decision.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
solver/sampler/UQ, Fluid/external repo, thesis body, source/property value,
Qwall value, coefficient, candidate freeze, protected score, or final score was
changed or released.
"""


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    bulk_rows = read_csv(BULK_DIR / "bulk_integral_heat_partition_rows.csv")
    residual_rows = read_csv(BULK_DIR / "energy_residual_feasibility.csv")
    open_cv_policy = read_csv(OPEN_CV_DIR / "open_cv_use_policy.csv")
    source_rows = read_csv(SOURCE_PROP_DIR / "case_qoi_preflight_matrix.csv")
    qoi_summary = read_csv(RECON_DIR / "qoi_reconciliation_summary.csv")

    source_by_slot = {row["qoi_or_model_slot"]: row for row in source_rows}
    s13_source = source_by_slot.get("Q_wall_W_and_exchange_QOIs", {})
    qwall_summary = next(row for row in qoi_summary if row["qoi_label"] == "Q_wall_W")

    residual_equation_rows = [
        {
            "equation_id": "S13_OPEN_CV_RESIDUAL",
            "formula": "R_E = Q_source_side_net_static_bc_W - Q_wall_W - mdot_throughflow*cp*DeltaT_throughflow - storage - other_named_losses",
            "positive_sign_convention": "positive residual means source-side heat not owned by wall heat, throughflow enthalpy, storage, or other named loss lanes",
            "open_cv_allowed": "true",
            "coefficient_admission_allowed": "false",
            "reason": "open CV is diagnostic only until every boundary flux term is named, same-basis cp/property evidence is released, and uncertainty is bounded",
        }
    ]

    case_budget_rows = [
        {
            "case_id": row["case_id"],
            "target_time_window_s": row["target_time_window_s"],
            "Q_source_side_net_static_bc_W": row["Q_source_side_net_static_bc_W"],
            "Q_wall_W": row["Q_wall_W"],
            "Q_remaining_after_wall_W": row["Q_remaining_after_wall_W"],
            "F_wall_Qwall_over_source": row["F_wall_Qwall_over_source"],
            "throughflow_enthalpy_driver_abs_mdot_deltaT_kgK_s": row["abs_mdot_times_deltaT_kgK_s"],
            "cp_required_to_match_Q_wall_J_kg_K": row["cp_required_to_match_Q_wall_J_kg_K"],
            "cp_required_to_match_source_side_J_kg_K": row["cp_required_to_match_source_side_J_kg_K"],
            "residual_value_released": "false",
            "can_compute_same_basis_residual_now": "false",
            "disposition": "budget_skeleton_only_fail_closed",
        }
        for row in bulk_rows
    ]

    missing_input_rows = [
        {
            "missing_input_or_gate": "row_specific_cp_property_release",
            "current_status": s13_source.get("cp_basis", "required_not_released"),
            "needed_for": "same-basis throughflow enthalpy term",
            "pass_now": "false",
            "next_artifact": "source/property exact-field recovery or candidate-specific release row",
        },
        {
            "missing_input_or_gate": "throughflow_enthalpy_endpoints",
            "current_status": "not_released_for_same_basis_open_cv_residual",
            "needed_for": "mdot_throughflow*cp*DeltaT_throughflow",
            "pass_now": "false",
            "next_artifact": "same-window endpoint sampler/harvest manifest",
        },
        {
            "missing_input_or_gate": "storage_and_other_named_losses",
            "current_status": "named_in_equation_but_not_bounded",
            "needed_for": "residual-complete open CV",
            "pass_now": "false",
            "next_artifact": "storage/source/loss lane inventory with uncertainty",
        },
        {
            "missing_input_or_gate": "same_label_mesh_GCI_or_admitted_equivalence",
            "current_status": "formal_gci_ready_rows_zero",
            "needed_for": "candidate-grade S13 exchange evidence",
            "pass_now": "false",
            "next_artifact": "same-label coarse/GCI unlock or terminal no-GCI routing",
        },
        {
            "missing_input_or_gate": "source_property_Qwall_release",
            "current_status": s13_source.get("release_status", "no_release"),
            "needed_for": "source-bounded residual/candidate use",
            "pass_now": "false",
            "next_artifact": "candidate-specific source/property release review",
        },
    ]

    harvest_lane_rows = [
        {
            "lane": "throughflow_enthalpy_endpoint_pair",
            "required_fields": "T_in,T_out,mdot_throughflow,cp_basis,time_window,endpoint_labels",
            "basis_requirement": "same time window and same control-volume cut surfaces",
            "admission_use_now": "false",
            "notes": "needed before residual value can be computed",
        },
        {
            "lane": "wall_heat_Q_wall_W",
            "required_fields": "Q_wall_W,wall_face_set,normal_sign,time_window,mesh_label",
            "basis_requirement": "same S13 wall faces and no source-side relabel",
            "admission_use_now": "false",
            "notes": "diagnostic only until Qwall/source-property release and mesh/GCI pass",
        },
        {
            "lane": "source_side_static_bc_heat",
            "required_fields": "Q_source_side_net_static_bc_W,source_face_set,sign,time_window",
            "basis_requirement": "source-side lane must remain separate from wall heat",
            "admission_use_now": "false",
            "notes": "stable partition supports model design but not coefficient fit",
        },
        {
            "lane": "storage_and_named_losses",
            "required_fields": "storage_W,other_named_losses_W,uncertainty,source_path",
            "basis_requirement": "all non-throughflow terms explicit or residual labeled incomplete",
            "admission_use_now": "false",
            "notes": "prevents hidden residual absorption into internal Nu",
        },
    ]

    required_input_rows = [
        ["Q_source_side_net_static_bc_W", "W", "source-side heat-flow QOI kept distinct from Q_wall_W", "diagnostic_equivalence_exists_release_not_admitted", "same-window source/property release review"],
        ["Q_wall_W", "W", "wall heat-flow integral on trusted wall/core band", s13_source.get("release_status", "diagnostic_only_no_release"), "same-label mesh/GCI or admitted equivalence plus source/property release"],
        ["H_throughflow_net_W", "W", "mdot_throughflow_kg_s * cp_J_kg_K * (T_out_bulk_K - T_in_bulk_K)", "missing_same_basis_endpoint_harvest", "derive endpoint masks and harvest mdot/T_bulk on the same window"],
        ["cp_J_kg_K", "J/kg/K", "row-specific cp basis used in throughflow and exchange enthalpy terms", s13_source.get("cp_basis", "required_not_released"), "row-specific source/property provenance and split-permission release"],
        ["Q_storage_W", "W", "time-window storage term for the open CV", "missing_not_zero", "prove negligible storage by drift/UQ or keep explicit missing lane"],
        ["Q_other_named_losses_W", "W", "all named non-wall source/sink/loss owner lanes in the open CV", "missing_owner_manifest", "inventory named loss/source lanes; do not hide residual in internal Nu"],
    ]
    required_input_dicts = [
        {
            "input_label": label,
            "unit": unit,
            "formula_or_definition": definition,
            "current_status": status,
            "release_ready": "false",
            "next_required_action": action,
        }
        for label, unit, definition, status, action in required_input_rows
    ]

    storage_policy_rows = [
        {
            "term": "Q_storage_W",
            "default_status": "missing_not_zero",
            "zero_allowed_if": "time-window drift and same-window UQ prove storage is negligible",
            "forbidden_use": "tuning steady residuals or hiding heat in internal Nu",
        },
        {
            "term": "Q_other_named_losses_W",
            "default_status": "missing_not_zero",
            "zero_allowed_if": "owner-lane manifest proves no additional loss/source path exists",
            "forbidden_use": "collapsing wall, radiation, cooler, contact, storage, or residual into internal Nu",
        },
        {
            "term": "R_E",
            "default_status": "not_computed_until_complete",
            "zero_allowed_if": "all same-basis terms exist and residual is within same-QOI UQ",
            "forbidden_use": "declaring closure from Q_wall/source partition alone",
        },
    ]

    progression_rows = [
        {"phase": "1", "name": "bulk_integral_heat_partition", "status": "complete_diagnostic", "next_unlock": "use Q_remaining_after_wall_W as conservation target"},
        {"phase": "2", "name": "residual_complete_open_cv_contract", "status": "complete_fail_closed", "next_unlock": "throughflow endpoint/cp/storage harvest lanes"},
        {"phase": "3", "name": "same_window_throughflow_enthalpy_and_cp_harvest", "status": "next_best_action", "next_unlock": "compute R_E and decide whether exchange-cell detail is required"},
        {"phase": "4", "name": "exchange_cell_or_bulk_closure_choice", "status": "deferred_no_fit", "next_unlock": "only after same-QOI UQ and mesh/GCI support residual QOIs"},
    ]
    progression_gate_rows = [
        {"gate": "stable_heat_partition_evidence", "status": "diagnostic_pass", "evidence": "F_wall is stable across Salt2/Salt3/Salt4"},
        {"gate": "same_basis_throughflow_enthalpy", "status": "fail_closed", "evidence": "endpoint masks, mdot_throughflow, T_in, and T_out are not released"},
        {"gate": "cp_property_release", "status": "fail_closed", "evidence": "row-specific cp/property release remains absent"},
        {"gate": "storage_and_named_loss_owner_lanes", "status": "fail_closed", "evidence": "storage and named loss/source lanes are not complete for the open CV"},
        {"gate": "predictive_1d_next_step", "status": "open_next_harvest_only", "evidence": "harvest same-window throughflow enthalpy endpoints and cp before residual/admission"},
    ]

    guardrail_rows = [
        {
            "guardrail": "open_cv_diagnostic_allowed",
            "status": "true",
            "evidence": next(row["allowed_outputs"] for row in open_cv_policy if row["use_case"] == "formal_energy_or_pressure_residual"),
        },
        {"guardrail": "coefficient_admission_allowed", "status": "false", "evidence": "closed or residual-complete CV plus source/property and UQ gates required"},
        {"guardrail": "formal_gci_ready", "status": "false", "evidence": qwall_summary["formal_gci_status"]},
        {"guardrail": "Qwall_source_property_release", "status": "false", "evidence": s13_source.get("release_status", "no_release")},
        {"guardrail": "residual_absorption_into_internal_Nu", "status": "false", "evidence": "residual remains explicit missing lane, not a fitted Nu multiplier"},
    ]

    source_manifest_rows = [
        {"source_path": rel(BULK_DIR / "bulk_integral_heat_partition_rows.csv"), "use": "case budget skeleton and stable heat partition rows"},
        {"source_path": rel(BULK_DIR / "energy_residual_feasibility.csv"), "use": "residual equation and missing same-basis inputs"},
        {"source_path": rel(OPEN_CV_DIR / "open_cv_use_policy.csv"), "use": "open-CV diagnostic/admission policy"},
        {"source_path": rel(SOURCE_PROP_DIR / "case_qoi_preflight_matrix.csv"), "use": "cp/property/source release blocker status"},
        {"source_path": rel(RECON_DIR / "qoi_reconciliation_summary.csv"), "use": "S13 Qwall/proxy mesh/GCI disposition"},
    ]

    write_csv(OUT_DIR / "residual_equation_contract.csv", residual_equation_rows, ["equation_id", "formula", "positive_sign_convention", "open_cv_allowed", "coefficient_admission_allowed", "reason"])
    write_csv(OUT_DIR / "case_budget_skeleton.csv", case_budget_rows, ["case_id", "target_time_window_s", "Q_source_side_net_static_bc_W", "Q_wall_W", "Q_remaining_after_wall_W", "F_wall_Qwall_over_source", "throughflow_enthalpy_driver_abs_mdot_deltaT_kgK_s", "cp_required_to_match_Q_wall_J_kg_K", "cp_required_to_match_source_side_J_kg_K", "residual_value_released", "can_compute_same_basis_residual_now", "disposition"])
    write_csv(OUT_DIR / "missing_input_gate.csv", missing_input_rows, ["missing_input_or_gate", "current_status", "needed_for", "pass_now", "next_artifact"])
    write_csv(OUT_DIR / "harvest_lane_requirements.csv", harvest_lane_rows, ["lane", "required_fields", "basis_requirement", "admission_use_now", "notes"])
    write_csv(OUT_DIR / "required_input_matrix.csv", required_input_dicts, ["input_label", "unit", "formula_or_definition", "current_status", "release_ready", "next_required_action"])
    write_csv(OUT_DIR / "storage_and_named_loss_policy.csv", storage_policy_rows, ["term", "default_status", "zero_allowed_if", "forbidden_use"])
    write_csv(OUT_DIR / "predictive_1d_progression_ladder.csv", progression_rows, ["phase", "name", "status", "next_unlock"])
    write_csv(OUT_DIR / "progression_gate.csv", progression_gate_rows, ["gate", "status", "evidence"])
    write_csv(OUT_DIR / "admission_guardrails.csv", guardrail_rows, ["guardrail", "status", "evidence"])
    write_csv(OUT_DIR / "source_manifest.csv", source_manifest_rows, ["source_path", "use"])

    f_wall_values = [fnum(row["F_wall_Qwall_over_source"]) for row in bulk_rows]
    remainder_fractions = [fnum(row["Q_remaining_after_wall_W"]) / fnum(row["Q_source_side_net_static_bc_W"]) for row in bulk_rows]
    summary = {
        "task_id": TASK_ID,
        "date": DATE,
        "decision": "residual_complete_open_cv_contract_defined_fail_closed_no_residual_value_no_admission",
        "case_budget_rows": len(case_budget_rows),
        "missing_input_gate_rows": len(missing_input_rows),
        "harvest_lane_rows": len(harvest_lane_rows),
        "required_input_rows": len(required_input_dicts),
        "progression_gate_rows": len(progression_gate_rows),
        "mean_F_wall_Qwall_over_source": mean(f_wall_values),
        "range_F_wall_Qwall_over_source": max(f_wall_values) - min(f_wall_values),
        "mean_known_remainder_fraction_of_source": mean(remainder_fractions),
        "open_cv_diagnostic_allowed": True,
        "same_basis_residual_computable_rows": 0,
        "residual_value_released_rows": 0,
        "coefficient_admission": False,
        "source_property_release": False,
        "Qwall_release": False,
        "formal_gci_ready_rows": 0,
        "production_harvest_allowed": False,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "scheduler_action": False,
        "solver_postprocessing_sampler_harvest_uq_launched": False,
        "fluid_or_external_edit": False,
        "thesis_body_or_latex_edit": False,
        "s11_s12_s13_s15_s6_trigger": False,
        "runtime_leakage_relaxation": False,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / "README.md").write_text(readme_text(summary), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    summary = build()
    if args.summary_only:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"wrote {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
