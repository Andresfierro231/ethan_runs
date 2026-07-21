#!/usr/bin/env python3
"""Build Phase 4 upcomer exchange/internal-Nu gate artifacts.

This builder consumes existing repo evidence only. It does not read or mutate
native solver outputs, launch extraction, fit coefficients, select models, or
change admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-PHASE-4-UPCOMER-EXCHANGE-AND-INTERNAL-NU-GATE"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
OUT = ROOT / OUT_REL

PHASE2 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_2_split_heat_loss_evidence"
)
PHASE3 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_3_wall_test_section_model_score"
)
MATCHED = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_matched_plane_recirc_field_harvest"
)
EXCHANGE = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_throughflow_recirc_exchange_cell"
)
SINGLE_STREAM = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_gated_single_stream_developing_branch"
)
HYBRID = ROOT / (
    "work_products/2026-07/2026-07-17/"
    "2026-07-17_upcomer_pipe_cell_hybrid_model"
)
ANCHOR = ROOT / (
    "work_products/2026-07/2026-07-20/"
    "2026-07-20_upcomer_onset_anchor_design"
)
SAME_QOI = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_same_qoi_uq_execution"
)

PHASE2_RESIDUALS = PHASE2 / "energy_residual_owner_matrix.csv"
PHASE3_RELEASE = PHASE3 / "phase3_release_gate.csv"
PHASE3_HANDOFF = PHASE3 / "phase4_handoff_queue.csv"
MATCHED_HARVEST = MATCHED / "matched_plane_recirc_field_harvest.csv"
MATCHED_READINESS = MATCHED / "recirc_harvest_readiness.csv"
EXCHANGE_REQUIREMENTS = EXCHANGE / "cfd_evidence_requirements.csv"
SINGLE_STREAM_GATE = SINGLE_STREAM / "single_stream_developing_branch_gate.csv"
HYBRID_FEATURES = HYBRID / "recirculation_feature_scorecard.csv"
HYBRID_DECISION = HYBRID / "upcomer_admission_decision.csv"
ANCHOR_GATE = ANCHOR / "admission_gate_contract.csv"
SAME_QOI_TABLE = SAME_QOI / "same_qoi_uq_admission_table.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def case_id_from_key(case_key: str) -> str:
    lower = case_key.lower()
    for salt in ("salt1", "salt2", "salt3", "salt4"):
        if salt in lower:
            return f"salt_{salt[-1]}"
    return case_key


def residual_lookup() -> dict[str, dict[str, str]]:
    rows = read_csv(PHASE2_RESIDUALS)
    return {
        row["case_id"]: row
        for row in rows
        if row.get("physical_segment") == "upcomer"
    }


def exchange_readiness_rows() -> list[dict[str, Any]]:
    residual_by_case = residual_lookup()
    rows: list[dict[str, Any]] = []

    for row in read_csv(MATCHED_HARVEST):
        if row.get("source_family") != "upcomer_matched_plane_diagnostic_proxy":
            continue
        case_id = case_id_from_key(row["case_key"])
        residual = residual_by_case.get(case_id, {})
        blocking_reasons = [
            row.get("blocked_reason", "missing_recirc_admission_grade_fields"),
            "missing_V_recirc",
            "missing_mdot_exchange",
            "missing_same_qoi_UQ",
            "ordinary_internal_Nu_absorption_forbidden",
        ]
        rows.append(
            {
                "readiness_id": row["harvest_id"],
                "source_family": "matched_plane_upcomer",
                "case_key": row["case_key"],
                "case_id": case_id,
                "feature_or_span": row["feature_or_plane"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_flow_intensity": row["secondary_flow_intensity"],
                "recirculation_metric_status": row["field_status"],
                "wall_core_delta_T_status": row["wall_core_delta_T_status"],
                "V_recirc_status": "missing",
                "mdot_exchange_status": "missing",
                "tau_recirc_status": "missing",
                "energy_residual_W": residual.get("energy_residual_W", ""),
                "energy_residual_status": "present_diagnostic" if residual.get("energy_residual_W") else "missing",
                "pressure_residual_status": "missing_or_partial_no_same_window_pressure_residual",
                "same_qoi_uq_status": "blocked_missing_same_qoi_UQ",
                "runtime_legality": "diagnostic_only_no_exchange_coefficient_or_internal_Nu_fit",
                "exchange_cell_readiness": "blocked_missing_exchange_state_or_admission_grade_fields",
                "ordinary_internal_Nu_allowed": "false",
                "blocking_reasons": ";".join(reason for reason in blocking_reasons if reason),
                "source_paths": row["source_paths"],
            }
        )

    for index, row in enumerate(read_csv(HYBRID_FEATURES), start=1):
        rows.append(
            {
                "readiness_id": f"HYBRID-FEATURE-{index:03d}",
                "source_family": "hybrid_feature_scorecard",
                "case_key": row["case_key"],
                "case_id": case_id_from_key(row["case_key"]),
                "feature_or_span": row["span"],
                "reverse_area_fraction": row["reverse_area_fraction"],
                "reverse_mass_fraction": row["reverse_mass_fraction"],
                "secondary_flow_intensity": row["secondary_velocity_fraction"],
                "recirculation_metric_status": "present_diagnostic",
                "wall_core_delta_T_status": "present_proxy_delta_T_wall_bulk",
                "V_recirc_status": "missing",
                "mdot_exchange_status": "missing",
                "tau_recirc_status": "missing",
                "energy_residual_W": "",
                "energy_residual_status": "missing_same_window_exchange_energy_residual",
                "pressure_residual_status": "missing_same_window_pressure_residual",
                "same_qoi_uq_status": "blocked_missing_same_qoi_UQ",
                "runtime_legality": "diagnostic_only_no_exchange_coefficient_or_internal_Nu_fit",
                "exchange_cell_readiness": "diagnostic_feature_present_but_not_calibrated",
                "ordinary_internal_Nu_allowed": "false",
                "blocking_reasons": (
                    f"{row['blocked_labels']};missing_V_recirc;missing_mdot_exchange;"
                    "missing_same_qoi_UQ;hybrid_not_calibrated"
                ),
                "source_paths": row["source_path"],
            }
        )

    return rows


def ordinary_reopening_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(SINGLE_STREAM_GATE):
        rows.append(
            {
                "candidate_id": row["gate_id"],
                "case_id": row["case_id"],
                "span": row["span"],
                "property_mode": row["property_mode"],
                "Re": row["Re"],
                "Pr": row["Pr"],
                "Ri": row["Ri"],
                "Gz": row["Gz"],
                "source_envelope_gate": row["source_envelope_status"],
                "sign_heat_balance_gate": row["thermal_reset_status"],
                "recirculation_gate": row["reverse_flow_metric_status"],
                "pressure_residual_gate": row["pressure_residual_gate"],
                "same_qoi_uq_gate": row["same_qoi_uq_gate"],
                "single_stream_developing_allowed": row["single_stream_developing_allowed"],
                "ordinary_internal_Nu_fit_allowed": "false",
                "coefficient_admission_status": "no_coefficient_admission",
                "blocking_reasons": row["blocking_reasons"],
                "source_paths": row["source_paths"],
            }
        )
    return rows


def missing_evidence_rows() -> list[dict[str, str]]:
    status_by_requirement = {
        "topology_signed_paths": "not_cleared_for_admission",
        "local_reverse_flow": "not_cleared_for_admission",
        "pressure_basis": "partial_or_missing_same_window_pressure_basis_for_exchange",
        "kinetic_basis": "not_cleared_for_admission",
        "straight_development_subtraction": "not_cleared_for_admission",
        "recirculation_volume": "missing_V_recirc",
        "exchange_rate": "missing_mdot_exchange_and_tau_recirc",
        "thermal_state": "missing_T_recirc_or_same_window_enthalpy_state",
        "wall_source_terms": "not_cleared_for_admission",
        "split_safe_score": "not_cleared_for_admission",
        "same_qoi_uq": "blocked_missing_same_qoi_UQ",
    }
    rows = []
    for row in read_csv(EXCHANGE_REQUIREMENTS):
        rows.append(
            {
                "requirement_id": row["requirement_id"],
                "field_or_group": row["field_or_group"],
                "needed_for": row["needed_for"],
                "phase4_status": status_by_requirement[row["requirement_id"]],
                "next_extraction_task": row["missing_behavior"],
                "source_paths": row["source_path"],
            }
        )
    return rows


def decision_rows(exchange_rows: list[dict[str, Any]], ordinary_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    readiness = read_csv(MATCHED_READINESS)
    readiness_text = "; ".join(
        f"{row['source_family']}={row['admission_readiness']}" for row in readiness
    )
    return [
        {
            "decision_id": "exchange_cell_admission",
            "status": "blocked_diagnostic_only",
            "decision_status": "blocked_diagnostic_only",
            "evidence": f"{len(exchange_rows)} exchange-readiness rows reviewed; 0 ready",
            "admission_change": "none",
            "next_action": (
                "extract V_recirc, mdot_exchange, same-window thermal/pressure residuals, "
                "and same-QOI UQ before calibration"
            ),
            "source_paths": rel(OUT / "upcomer_exchange_cell_readiness.csv"),
        },
        {
            "decision_id": "ordinary_internal_Nu_reopening",
            "status": "blocked_zero_fit_rows",
            "decision_status": "blocked_zero_fit_rows",
            "evidence": f"{len(ordinary_rows)} single-stream rows reviewed; 0 fit-ready",
            "admission_change": "none",
            "next_action": (
                "keep ordinary internal Nu closed until source, sign/heat, recirculation, "
                "and same-QOI UQ gates pass"
            ),
            "source_paths": rel(OUT / "ordinary_single_stream_nu_reopening_candidates.csv"),
        },
        {
            "decision_id": "terminal_or_sampling_dependency",
            "status": "blocked_or_terminal_gated",
            "decision_status": "blocked_or_terminal_gated",
            "evidence": readiness_text,
            "admission_change": "none",
            "next_action": "do not duplicate terminal-gated samplers; wait for claimed latest-CFD or anchor harvest rows",
            "source_paths": rel(MATCHED_READINESS),
        },
        {
            "decision_id": "phase5_release_gate",
            "status": "not_triggered",
            "decision_status": "not_triggered",
            "evidence": "no runtime-legal heat-loss candidate and no internal-Nu reopening candidate passed Phase 4",
            "admission_change": "none",
            "next_action": "publish negative Phase 4 result; Phase 5 remains trigger-gated",
            "source_paths": rel(OUT / "phase4_decision_gate.csv"),
        },
    ]


def _float_or_none(value: str) -> float | None:
    if value in ("", "missing", "not_sampled_or_not_admission_grade", "nan"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def aggregate_exchange_cell_readiness(
    detailed_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_case: dict[str, dict[str, Any]] = {}
    for row in detailed_rows:
        if row["source_family"] != "matched_plane_upcomer":
            continue
        case_id = row["case_id"]
        if case_id not in {"salt_2", "salt_3", "salt_4"}:
            continue
        bucket = by_case.setdefault(
            case_id,
            {
                "case_id": case_id,
                "region": "upcomer",
                "max_reverse_area_fraction": 0.0,
                "max_reverse_mass_fraction": 0.0,
                "max_secondary_flow_intensity": 0.0,
                "recirculation_volume_status": "missing_V_recirc",
                "exchange_rate_status": "missing_mdot_exchange",
                "residence_time_status": "missing_tau_recirc",
                "pressure_residual_status": "missing_or_partial_no_same_window_pressure_residual",
                "energy_residual_status": "present_diagnostic_or_partial",
                "same_qoi_uq_status": "blocked_missing_same_qoi_UQ",
                "fit_allowed_now": "false",
                "residual_assignment": "do_not_absorb_into_internal_Nu",
                "model_mode": "throughflow_recirc_exchange_cell_diagnostic",
                "source_paths": "",
            },
        )
        for source_key, target_key in (
            ("reverse_area_fraction", "max_reverse_area_fraction"),
            ("reverse_mass_fraction", "max_reverse_mass_fraction"),
            ("secondary_flow_intensity", "max_secondary_flow_intensity"),
        ):
            value = _float_or_none(str(row[source_key]))
            if value is not None:
                bucket[target_key] = max(float(bucket[target_key]), value)
        if row.get("source_paths"):
            paths = [path for path in bucket["source_paths"].split(";") if path]
            paths.append(str(row["source_paths"]))
            bucket["source_paths"] = ";".join(dict.fromkeys(paths))

    rows = []
    for case_id in sorted(by_case):
        row = by_case[case_id]
        for key in (
            "max_reverse_area_fraction",
            "max_reverse_mass_fraction",
            "max_secondary_flow_intensity",
        ):
            row[key] = f"{float(row[key]):.10g}"
        rows.append(row)
    return rows


def ordinary_reopening_gate_rows(detailed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "upcomer_left_vertical": [
            row
            for row in detailed_rows
            if row["span"] in {"left_lower_leg", "left_upper_leg", "test_section_span"}
            or row["span"].startswith("upcomer")
        ],
        "downcomer_right_vertical": [row for row in detailed_rows if row["span"] == "right_leg"],
        "heater_lower_leg": [row for row in detailed_rows if row["span"] == "lower_leg"],
        "cooling_upper_leg": [row for row in detailed_rows if row["span"] == "upper_leg"],
    }
    rows = []
    for branch_id, candidates in grouped.items():
        if not candidates:
            continue
        recirc_fail = any(
            row["recirculation_gate"] in {"fail", "blocked_recirc_evidence_present"}
            or "recirculation_invalid_single_stream" in row["blocking_reasons"]
            for row in candidates
        )
        rows.append(
            {
                "branch_id": branch_id,
                "candidate_rows_reviewed": len(candidates),
                "recirculation_gate": "fail" if recirc_fail else "precheck_only_not_admitted",
                "source_envelope_gate": "blocked_or_precheck_only",
                "sign_heat_balance_gate": "not_cleared_for_admission",
                "same_qoi_uq_gate": "blocked_missing_same_qoi_UQ",
                "reopen_internal_Nu": "false",
                "ordinary_nu_fit_admitted_rows": "0",
                "ordinary_fD_fit_admitted_rows": "0",
                "ordinary_K_fit_admitted_rows": "0",
                "residual_assignment": "do_not_absorb_into_internal_Nu",
                "source_paths": ";".join(
                    dict.fromkeys(
                        path
                        for row in candidates
                        for path in row["source_paths"].split(";")
                        if path
                    )
                ),
            }
        )
    return rows


def heat_path_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "heat_path": "internal_Nu_single_stream",
            "allowed_use": "baseline_or_diagnostic_only",
            "current_gate": "closed_zero_fit_rows",
            "forbidden_runtime_inputs": "heat residual absorbed into internal Nu; CFD wallHeatFlux; validation temperatures",
            "residual_policy": "ordinary Nu cannot absorb wall/source/storage/exchange residuals",
            "next_action": "reopen only after source, sign/heat, low-recirculation, and same-QOI UQ gates pass",
        },
        {
            "heat_path": "upcomer_exchange_cell",
            "allowed_use": "dry_interface_and_diagnostic_residual_target",
            "current_gate": "blocked_missing_V_recirc_mdot_exchange_T_recirc_UQ",
            "forbidden_runtime_inputs": "CFD mdot; held-out pressure residual; validation temperatures",
            "residual_policy": "pressure and energy residuals stay named exchange-cell targets",
            "next_action": "extract V_recirc, mdot_exchange, T_recirc, pressure residual, energy residual, and UQ",
        },
        {
            "heat_path": "residual",
            "allowed_use": "blocker_accounting_only",
            "current_gate": "not_a_model_input",
            "forbidden_runtime_inputs": "energy or heat residual used as setup field; heat residual absorbed into internal Nu",
            "residual_policy": "residual remains separate until a physical owner is evidenced",
            "next_action": "keep residual attribution explicit in any Phase 5 handoff",
        },
    ]


def phase4_release_gate_rows() -> list[dict[str, str]]:
    return [
        {
            "gate_id": "ordinary_internal_nu_reopening_gate",
            "status": "fail_zero_reopened_internal_Nu_rows",
            "evidence": "ordinary reopening gate emits 0 admitted Nu rows",
            "next_action": "keep ordinary internal Nu closed",
        },
        {
            "gate_id": "exchange_cell_readiness_gate",
            "status": "fail_no_fit_ready_exchange_cell",
            "evidence": "missing V_recirc, mdot_exchange, T_recirc, pressure residual basis, energy closure, and UQ",
            "next_action": "run separate evidence extraction before calibration",
        },
        {
            "gate_id": "residual_attribution_gate",
            "status": "pass_residual_not_hidden_in_internal_Nu",
            "evidence": "runtime and heat-path contracts forbid residual absorption",
            "next_action": "carry residual as named unresolved/exchange target",
        },
        {
            "gate_id": "phase5_trigger_gate",
            "status": "not_triggered",
            "evidence": "no runtime-legal heat-loss candidate or internal-Nu reopening candidate passed",
            "next_action": "Phase 5 remains trigger-gated",
        },
    ]


def runtime_legality_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_id": "forbidden_residual_runtime_input",
            "runtime_input": "energy or heat residual",
            "status": "forbidden",
            "policy": "residual is a target/diagnostic, not a setup input",
        },
        {
            "audit_id": "forbidden_wallheatflux_runtime_input",
            "runtime_input": "CFD wallHeatFlux",
            "status": "forbidden",
            "policy": "realized wall heat flux is diagnostic/scoring evidence only",
        },
        {
            "audit_id": "forbidden_cfd_mdot_runtime_input",
            "runtime_input": "CFD mdot",
            "status": "forbidden",
            "policy": "mass flow is solved in predictive mode",
        },
        {
            "audit_id": "no_execution",
            "runtime_input": "Fluid/OpenFOAM execution",
            "status": "not_performed",
            "policy": "Phase 4 consumed existing artifacts only",
        },
    ]


def runtime_rows() -> list[dict[str, str]]:
    return [
        {
            "audit_id": "no_runtime_residual_absorption",
            "status": "pass_guardrail",
            "policy": "forbidden: heat residuals are not hidden in internal Nu or exchange coefficients",
            "evidence": "ordinary_internal_Nu_fit_allowed=false for every row",
            "source_paths": rel(OUT / "ordinary_single_stream_nu_reopening_candidates.csv"),
        },
        {
            "audit_id": "no_new_execution",
            "status": "pass",
            "policy": "no Fluid, OpenFOAM, scheduler, solver, or postprocessing launch",
            "evidence": "existing artifacts only",
            "source_paths": rel(OUT / "source_manifest.csv"),
        },
        {
            "audit_id": "admission_state",
            "status": "pass_no_mutation",
            "policy": "no registry, admission, blocker-register, or generated-index mutation",
            "evidence": "Phase 4 emits package-local gate status only",
            "source_paths": rel(OUT / "phase4_decision_gate.csv"),
        },
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "source_path": rel(PHASE2_RESIDUALS),
            "use": "Read heat-loss residual ownership and upcomer residuals.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PHASE3_RELEASE),
            "use": "Read negative wall/test-section score-gate result.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(PHASE3_HANDOFF),
            "use": "Read Phase 4 handoff queue.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(MATCHED_HARVEST),
            "use": "Read matched-plane RAF/RMF/SVF and missing-field state.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(MATCHED_READINESS),
            "use": "Read terminal/sampling readiness by source family.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(EXCHANGE_REQUIREMENTS),
            "use": "Read exchange-cell evidence requirements.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SINGLE_STREAM_GATE),
            "use": "Read ordinary single-stream reopening candidates.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(HYBRID_FEATURES),
            "use": "Read recirculation feature and wall/bulk drive diagnostics.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(HYBRID_DECISION),
            "use": "Read upcomer ordinary/hybrid admission decisions.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(ANCHOR_GATE),
            "use": "Read anchor/onset gate status.",
            "mutation_status": "read_only",
        },
        {
            "source_path": rel(SAME_QOI_TABLE),
            "use": "Read same-QOI UQ admission status.",
            "mutation_status": "read_only",
        },
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
provenance:
  - {rel(PHASE3 / "README.md")}
  - {rel(MATCHED / "README.md")}
  - {rel(EXCHANGE / "README.md")}
  - {rel(SINGLE_STREAM / "README.md")}
tags: [thermal-modeling, heat-loss, upcomer, recirculation, internal-nu]
related:
  - .agent/status/2026-07-21_{TASK}.md
  - .agent/journal/2026-07-21/heatloss-phase-4-upcomer-exchange-and-internal-nu-gate.md
  - {rel(PHASE3 / "README.md")}
task: {TASK}
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 4 Upcomer Exchange And Internal-Nu Gate

## Decision

Phase 4 keeps both exchange-cell calibration and ordinary internal-`Nu` fitting
closed. The current evidence supports diagnostic recirculation/exchange
classification, but it lacks recirculation volume, exchange mass flow,
same-window pressure/thermal residual closure, and same-QOI uncertainty.

## Results

- Exchange-readiness rows: `{summary["exchange_readiness_rows"]}`.
- Ordinary single-stream reopening rows: `{summary["ordinary_reopening_rows"]}`.
- Ordinary internal-`Nu` fit rows admitted: `{summary["ordinary_internal_nu_fit_rows"]}`.
- Exchange-cell calibration rows admitted: `{summary["exchange_cell_calibration_rows"]}`.
- Missing-evidence rows: `{summary["missing_evidence_rows"]}`.
- Phase 5 trigger: `{summary["phase5_trigger"]}`.

## Outputs

- `upcomer_exchange_cell_readiness.csv`
- `ordinary_single_stream_nu_reopening_candidates.csv`
- `missing_exchange_nu_evidence_queue.csv`
- `phase4_decision_gate.csv`
- `runtime_internal_nu_audit.csv`
- `exchange_cell_readiness.csv`
- `ordinary_single_stream_nu_reopening_gate.csv`
- `heat_path_modeling_contract.csv`
- `phase4_release_gate.csv`
- `runtime_legality_audit.csv`
- `source_manifest.csv`
- `summary.json`
- `README.md`

## Guardrails

- Residual heat was not absorbed into internal `Nu`.
- No exchange coefficient, threshold, ordinary `Nu`, `f_D`, `K`, F6, or global
  multiplier was fit or admitted.
- Package generation performed no native output, registry, scheduler,
  solver/postprocessing, Fluid, blocker, or external repo mutation.

## Next Action

The shortest useful next evidence task is a terminal/scoped sampler that emits
`V_recirc`, `mdot_exchange`, same-window wall/core temperatures, pressure
residual, energy residual, and same-QOI UQ for the upcomer/test-section
exchange lane. Phase 5 remains trigger-gated.
"""


def build() -> dict[str, Any]:
    exchange_rows = exchange_readiness_rows()
    ordinary_rows = ordinary_reopening_rows()
    missing_rows = missing_evidence_rows()
    decisions = decision_rows(exchange_rows, ordinary_rows)
    runtime = runtime_rows()
    aggregate_exchange_rows = aggregate_exchange_cell_readiness(exchange_rows)
    ordinary_gate_rows = ordinary_reopening_gate_rows(ordinary_rows)
    heat_contract_rows = heat_path_contract_rows()
    release_gate_rows = phase4_release_gate_rows()
    runtime_legality = runtime_legality_rows()
    manifest = source_manifest_rows()

    summary = {
        "task": TASK,
        "created_utc": utc_now(),
        "output_dir": rel(OUT),
        "exchange_readiness_rows": len(exchange_rows),
        "ordinary_reopening_rows": len(ordinary_rows),
        "ordinary_internal_nu_fit_rows": sum(
            row["ordinary_internal_Nu_fit_allowed"] == "true" for row in ordinary_rows
        ),
        "exchange_cell_calibration_rows": sum(
            row["exchange_cell_readiness"] == "ready_for_calibration" for row in exchange_rows
        ),
        "exchange_cell_fit_ready_rows": 0,
        "reopened_internal_Nu_rows": 0,
        "missing_evidence_rows": len(missing_rows),
        "phase5_trigger": "not_triggered",
        "residual_absorbed_into_internal_nu": False,
        "residual_hidden_in_internal_Nu": False,
        "fitting_or_model_selection": False,
        "native_solver_outputs_mutated": False,
        "scheduler_action": False,
        "solver_or_postprocessing_launched": False,
        "fluid_or_openfoam_execution": False,
        "external_fluid_edit": False,
        "registry_mutated": False,
        "admission_state_mutated": False,
        "registry_or_admission_mutated": False,
        "generated_index_refreshed": False,
    }

    write_csv(OUT / "upcomer_exchange_cell_readiness.csv", exchange_rows)
    write_csv(OUT / "ordinary_single_stream_nu_reopening_candidates.csv", ordinary_rows)
    write_csv(OUT / "missing_exchange_nu_evidence_queue.csv", missing_rows)
    write_csv(OUT / "phase4_decision_gate.csv", decisions)
    write_csv(OUT / "runtime_internal_nu_audit.csv", runtime)
    write_csv(OUT / "exchange_cell_readiness.csv", aggregate_exchange_rows)
    write_csv(OUT / "ordinary_single_stream_nu_reopening_gate.csv", ordinary_gate_rows)
    write_csv(OUT / "heat_path_modeling_contract.csv", heat_contract_rows)
    write_csv(OUT / "phase4_release_gate.csv", release_gate_rows)
    write_csv(OUT / "runtime_legality_audit.csv", runtime_legality)
    write_csv(OUT / "source_manifest.csv", manifest)
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
