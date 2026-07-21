#!/usr/bin/env python3
"""Build the heat-loss upcomer exchange evidence-extraction contract.

This builder consumes existing work products only. It does not read native
solver fields, write case directories, launch OpenFOAM/postprocessing, fit
coefficients, or change admission state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "TODO-HEATLOSS-UPCOMER-EXCHANGE-EVIDENCE-EXTRACTION"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path(
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_upcomer_exchange_evidence_extraction"
)
OUT = ROOT / OUT_REL

PHASE4 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate"
)
PHASE5 = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_heatloss_phase_5_frozen_scorecard_and_thesis_handoff"
)
RECIRC = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_matched_plane_recirc_field_harvest"
)
EXCHANGE_CELL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_litrev_throughflow_recirc_exchange_cell"
)
PREFLIGHT = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_evidence_preflight"
)
TERMINAL = ROOT / (
    "work_products/2026-07/2026-07-21/"
    "2026-07-21_upcomer_exchange_terminal_source_readiness"
)
SAMPLER = ROOT / "tools/extract/sample_upcomer_convection_cell.py"

AGGREGATE_READINESS = PHASE4 / "exchange_cell_readiness.csv"
DETAILED_READINESS = PHASE4 / "upcomer_exchange_cell_readiness.csv"
MISSING_QUEUE = PHASE4 / "missing_exchange_nu_evidence_queue.csv"
PHASE4_DECISION = PHASE4 / "phase4_decision_gate.csv"
PHASE4_RUNTIME = PHASE4 / "runtime_internal_nu_audit.csv"
PHASE5_NEXT = PHASE5 / "blocker_delta_next_actions.csv"
RECIRC_ROWS = RECIRC / "matched_plane_recirc_field_harvest.csv"
RECIRC_READINESS = RECIRC / "recirc_harvest_readiness.csv"
EVIDENCE_REQS = EXCHANGE_CELL / "cfd_evidence_requirements.csv"
PREFLIGHT_VARIABLES = PREFLIGHT / "exchange_variable_availability.csv"
TERMINAL_QOI_COVERAGE = TERMINAL / "required_exchange_qoi_coverage.csv"


REQUIRED_GROUPS: list[dict[str, str]] = [
    {
        "field_group": "local_reverse_flow",
        "required_fields": "reverse_area_fraction;reverse_mass_fraction;secondary_flow_intensity",
        "needed_for": "ordinary_Nu_rejection_and_exchange_cell_trigger",
        "same_window_requirement": "same case/time planes as exchange-state fields",
        "output_units_or_basis": "dimensionless plane metrics",
    },
    {
        "field_group": "recirculation_volume",
        "required_fields": "V_recirc",
        "needed_for": "exchange_cell_state",
        "same_window_requirement": "same case/time window as mdot_exchange and thermal state",
        "output_units_or_basis": "m3 coherent recirculation-cell mask",
    },
    {
        "field_group": "exchange_rate",
        "required_fields": "mdot_exchange;tau_recirc",
        "needed_for": "exchange_cell_state_and_residence_time",
        "same_window_requirement": "same case/time window as V_recirc",
        "output_units_or_basis": "kg/s exchange estimator; s residence time",
    },
    {
        "field_group": "thermal_state",
        "required_fields": "T_main;T_recirc;wall_core_delta_T",
        "needed_for": "exchange_energy_state",
        "same_window_requirement": "same case/time window as exchange rate and wall source terms",
        "output_units_or_basis": "K or K difference with enthalpy/property basis recorded",
    },
    {
        "field_group": "pressure_basis",
        "required_fields": "static_p;p_rgh;Delta_p_straight;Delta_p_dev;pressure_residual",
        "needed_for": "pressure_residual_attribution",
        "same_window_requirement": "same case/time window and sign convention as exchange-state rows",
        "output_units_or_basis": "Pa residual after hydrostatic and straight-development accounting",
    },
    {
        "field_group": "wall_source_terms",
        "required_fields": "Q_wall;Q_source;Q_sink;energy_residual",
        "needed_for": "thermal_residual_attribution",
        "same_window_requirement": "same case/time window as thermal_state",
        "output_units_or_basis": "W, separated source/sink/residual lanes",
    },
    {
        "field_group": "same_qoi_uq",
        "required_fields": "same_label_mesh_uq;same_formula_time_uq;same_window_sign_basis",
        "needed_for": "admission_and_uncertainty",
        "same_window_requirement": "same labels/formula/sign/window as the candidate exchange QOIs",
        "output_units_or_basis": "QOI-native uncertainty values and eligibility flags",
    },
]


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


def first_by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        out.setdefault(row[key], row)
    return out


def phase4_status_for(group: str, aggregate_row: dict[str, str], missing_by_group: dict[str, dict[str, str]]) -> str:
    if group == "local_reverse_flow":
        return "available_existing_diagnostic_not_admission"
    if group == "recirculation_volume":
        return aggregate_row["recirculation_volume_status"]
    if group == "exchange_rate":
        return ";".join([aggregate_row["exchange_rate_status"], aggregate_row["residence_time_status"]])
    if group == "thermal_state":
        return "missing_T_recirc_or_same_window_enthalpy_state;missing_wall_core_delta_T"
    if group == "pressure_basis":
        return aggregate_row["pressure_residual_status"]
    if group == "wall_source_terms":
        return aggregate_row["energy_residual_status"]
    if group == "same_qoi_uq":
        return aggregate_row["same_qoi_uq_status"]
    return missing_by_group.get(group, {}).get("phase4_status", "not_cleared_for_admission")


def sampler_gap_for(group: str) -> str:
    gaps = {
        "local_reverse_flow": (
            "current sampler can compute RAF/RMF/SVF after a claimed compute-node run; "
            "existing rows are proxy/diagnostic and not admission-grade"
        ),
        "recirculation_volume": "missing coherent region/volume mask and V_recirc integration",
        "exchange_rate": "missing conservative interface flux and residence-time calculation",
        "thermal_state": "missing paired main/recirculation thermal-state extractor and wall-core difference",
        "pressure_basis": "missing same-window pressure residual with hydrostatic and straight-development basis",
        "wall_source_terms": "existing energy residual is diagnostic/partial; source/sink ledger still needs same-window alignment",
        "same_qoi_uq": "missing same-label same-formula mesh/time uncertainty for exchange QOIs",
    }
    return gaps[group]


def existing_tool_support_for(group: str) -> str:
    support = {
        "local_reverse_flow": "partial_existing_tool_support_sample_upcomer_convection_cell",
        "recirculation_volume": "not_implemented_in_current_sampler",
        "exchange_rate": "not_implemented_in_current_sampler",
        "thermal_state": "not_implemented_in_current_sampler",
        "pressure_basis": "not_implemented_in_current_sampler",
        "wall_source_terms": "diagnostic_inputs_exist_but_not_same_window_contract",
        "same_qoi_uq": "not_implemented_in_current_sampler",
    }
    return support[group]


def blocked_behavior_for(group: str) -> str:
    if group == "local_reverse_flow":
        return "may block ordinary single-stream Nu but cannot open exchange fit by itself"
    if group == "wall_source_terms":
        return "use diagnostic residual for attribution only; do not absorb residual into internal Nu"
    return "keep exchange-cell and internal-Nu rows diagnostic-only; do not fit or admit"


def case_label(case_id: str) -> str:
    return {
        "salt_2": "salt2_jin_nominal_continuation",
        "salt_3": "salt3_jin_nominal_continuation",
        "salt_4": "salt4_jin_nominal_continuation",
    }[case_id]


def time_window_by_case() -> dict[str, dict[str, str]]:
    rows = read_csv(RECIRC_ROWS)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["source_family"] != "upcomer_matched_plane_diagnostic_proxy":
            continue
        if row["feature_or_plane"] != "upcomer_outlet":
            continue
        for case_id, key in {
            "salt_2": "salt2_jin_nominal_continuation",
            "salt_3": "salt3_jin_nominal_continuation",
            "salt_4": "salt4_jin_nominal_continuation",
        }.items():
            if row["case_key"] == key:
                out[case_id] = row
    return out


def sampler_field_map() -> list[dict[str, Any]]:
    requirement_by_id = first_by(read_csv(EVIDENCE_REQS), "requirement_id")
    preflight_by_var = first_by(read_csv(PREFLIGHT_VARIABLES), "variable_id")
    rows: list[dict[str, Any]] = []
    for spec in REQUIRED_GROUPS:
        group = spec["field_group"]
        req = requirement_by_id.get(group, {})
        preflight = preflight_by_var.get(group, {})
        rows.append(
            {
                "field_group": group,
                "fields": spec["required_fields"],
                "existing_tool_support": existing_tool_support_for(group),
                "sampler_gap": sampler_gap_for(group),
                "needed_for": spec["needed_for"],
                "same_window_requirement": spec["same_window_requirement"],
                "output_units_or_basis": spec["output_units_or_basis"],
                "phase4_requirement_status": req.get("minimum_evidence", preflight.get("current_status", "")),
                "blocked_behavior": blocked_behavior_for(group),
                "source_paths": ";".join([rel(EVIDENCE_REQS), rel(PREFLIGHT_VARIABLES), rel(SAMPLER)]),
            }
        )
    return rows


def extraction_contract() -> list[dict[str, Any]]:
    aggregate = read_csv(AGGREGATE_READINESS)
    missing_by_group = first_by(read_csv(MISSING_QUEUE), "field_or_group")
    windows = time_window_by_case()
    rows: list[dict[str, Any]] = []
    for case in aggregate:
        for spec in REQUIRED_GROUPS:
            group = spec["field_group"]
            window = windows.get(case["case_id"], {})
            rows.append(
                {
                    "case_id": case["case_id"],
                    "case_key": case_label(case["case_id"]),
                    "region": case["region"],
                    "time_window_s": window.get("time_or_window_s", "missing"),
                    "time_window_status": "known_from_matched_proxy_not_admission_grade",
                    "required_field_group": group,
                    "required_fields": spec["required_fields"],
                    "phase4_status": phase4_status_for(group, case, missing_by_group),
                    "sampler_requirement": sampler_gap_for(group),
                    "existing_evidence_status": existing_tool_support_for(group),
                    "admission_use": "diagnostic_only",
                    "fit_allowed_now": "false",
                    "score_allowed_now": "false",
                    "runtime_policy": "forbidden_as_runtime_predictive_input_until_training_only_contract_and_uq_exist",
                    "residual_policy": "do_not_hide_heat_residual_in_internal_Nu",
                    "source_paths": ";".join([rel(AGGREGATE_READINESS), rel(MISSING_QUEUE), rel(RECIRC_ROWS)]),
                }
            )
    return rows


def case_time_window_queue() -> list[dict[str, Any]]:
    aggregate_by_case = {row["case_id"]: row for row in read_csv(AGGREGATE_READINESS)}
    windows = time_window_by_case()
    rows: list[dict[str, Any]] = []
    for case_id in ("salt_2", "salt_3", "salt_4"):
        agg = aggregate_by_case[case_id]
        window = windows.get(case_id, {})
        rows.append(
            {
                "case_id": case_id,
                "case_key": case_label(case_id),
                "region": agg["region"],
                "time_window_s": window.get("time_or_window_s", "missing"),
                "representative_plane": window.get("feature_or_plane", "upcomer_outlet"),
                "existing_proxy_RAF": agg["max_reverse_area_fraction"],
                "existing_proxy_RMF": agg["max_reverse_mass_fraction"],
                "existing_proxy_SVF": agg["max_secondary_flow_intensity"],
                "required_action": "compute_node_sampler_implementation_then_execution_required",
                "minimum_extract_groups": (
                    "V_recirc;mdot_exchange;tau_recirc;T_main;T_recirc;"
                    "wall_core_delta_T;pressure_residual;energy_residual;same_qoi_uq"
                ),
                "scheduler_policy": "claim_separate_board_row_and_use_sbatch_or_srun_only",
                "launch_allowed_from_this_package": "false",
                "source_paths": ";".join([rel(AGGREGATE_READINESS), rel(RECIRC_ROWS)]),
            }
        )
    return rows


def no_admission_guardrail() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "native_case_outputs",
            "status": "unchanged",
            "policy": "no native CFD/OpenFOAM output mutation or case-directory write",
            "source_paths": rel(SAMPLER),
        },
        {
            "guard_id": "runtime_leakage",
            "status": "blocked",
            "policy": "do not use realized CFD residuals or observed exchange state as predictive runtime inputs",
            "source_paths": rel(PHASE4_RUNTIME),
        },
        {
            "guard_id": "internal_Nu_residual",
            "status": "blocked",
            "policy": "do not hide heat residual in internal Nu; residual must remain a separate attribution lane",
            "source_paths": rel(MISSING_QUEUE),
        },
        {
            "guard_id": "exchange_fit",
            "status": "blocked",
            "policy": "no exchange coefficient fit, no internal-Nu reopening, no model selection, no admission",
            "source_paths": rel(PHASE4_DECISION),
        },
        {
            "guard_id": "sampler_execution",
            "status": "not_launched",
            "policy": "this package defines fields/windows only; implementation and execution need a new row",
            "source_paths": rel(RECIRC_READINESS),
        },
    ]


def next_agent_handoff() -> list[dict[str, Any]]:
    return [
        {
            "sequence": 1,
            "work_package": "extend_upcomer_sampler_contract",
            "objective": "add extraction design for V_recirc, mdot_exchange, tau_recirc, paired thermal states, pressure residual, energy residual, and same-QOI UQ",
            "allowed_start": "after claiming a new sampler-design board row",
            "release_condition": "dry-run schema and unit tests prove every required field is either emitted or explicitly blocked",
            "forbidden_action": "no solver launch or case mutation during design-only row",
        },
        {
            "sequence": 2,
            "work_package": "compute_node_sampler_execution",
            "objective": "run the admitted sampler on salt_2/salt_3/salt_4 mainline windows through sbatch or srun",
            "allowed_start": "after sampler code review and source-case availability check",
            "release_condition": "source manifest records case paths, time windows, command, job id, logs, and output checks",
            "forbidden_action": "no login-node OpenFOAM or duplicate sampling against live terminal jobs",
        },
        {
            "sequence": 3,
            "work_package": "same_qoi_uq_pairing",
            "objective": "attach mesh/time uncertainty rows to the exact exchange-state and residual QOIs",
            "allowed_start": "after extracted QOI rows exist",
            "release_condition": "same-label same-formula same-window UQ rows exist for each candidate metric",
            "forbidden_action": "no holdout score or coefficient admission without UQ",
        },
        {
            "sequence": 4,
            "work_package": "phase4b_exchange_readiness_rescore",
            "objective": "decide whether exchange cells are scoreable and whether ordinary single-stream Nu remains closed",
            "allowed_start": "after sampler and UQ artifacts pass source/property and split guards",
            "release_condition": "explicit scoreable/not-scoreable decision with residual lane still separate from internal Nu",
            "forbidden_action": "no residual absorption into internal Nu",
        },
    ]


def source_manifest() -> list[dict[str, Any]]:
    paths = [
        AGGREGATE_READINESS,
        DETAILED_READINESS,
        MISSING_QUEUE,
        PHASE4_DECISION,
        PHASE4_RUNTIME,
        PHASE5_NEXT,
        RECIRC_ROWS,
        RECIRC_READINESS,
        EVIDENCE_REQS,
        PREFLIGHT_VARIABLES,
        TERMINAL_QOI_COVERAGE,
        SAMPLER,
    ]
    return [
        {
            "path": rel(path),
            "role": "read_only_input",
            "exists": str(path.exists()).lower(),
            "native_solver_output": "false",
            "mutated": "false",
        }
        for path in paths
    ]


def readme(summary: dict[str, Any]) -> str:
    return f"""---
task: {TASK}
date: 2026-07-21
role: Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, recirculation, exchange-cell, evidence-contract]
related:
  - {rel(PHASE4)}
  - {rel(PHASE5)}
  - {rel(RECIRC)}
  - {rel(EXCHANGE_CELL)}
---
# Heat-Loss Upcomer Exchange Evidence Extraction Contract

This package converts the Phase 4/5 heat-loss blockers into a concrete
pre-extraction contract for the upcomer exchange path. It is intentionally
no-solver and no-admission.

## Decision

- Mainline case/time queues: `{summary["case_time_window_rows"]}`
- Contract rows: `{summary["extraction_contract_rows"]}`
- Required field groups: `{summary["sampler_field_group_rows"]}`
- Sampler launched: `{str(summary["solver_or_postprocessing_or_sampler_launched"]).lower()}`
- Exchange fit allowed now: `{str(summary["any_fit_allowed_now"]).lower()}`
- Scoring allowed now: `{str(summary["any_score_allowed_now"]).lower()}`

The current proxy evidence supports a recirculation guard, but it does not yet
support exchange-cell calibration, internal-Nu reopening, or final scorecard
use. `V_recirc`, `mdot_exchange`, `tau_recirc`, paired main/cell thermal state,
same-window pressure residual, and same-QOI UQ remain blockers.

## Outputs

- `upcomer_exchange_extraction_contract.csv`: case-by-field-group runtime and
  admission contract.
- `sampler_field_map.csv`: required fields, current tool support, sampler gaps,
  and blocked behavior.
- `case_time_window_queue.csv`: salt 2/3/4 mainline windows for the later
  compute-node sampler row.
- `no_admission_guardrail.csv`: guardrails preserving residual and runtime
  split lanes.
- `next_agent_handoff.csv`: ordered next work packages.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, generated indexes, or blocker register were
mutated. No solver, postprocessor, sampler, fitting, model selection, closure
admission, or scorecard trigger was run. Heat residual remains separate from
internal Nu.
"""


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)

    contract_rows = extraction_contract()
    field_rows = sampler_field_map()
    queue_rows = case_time_window_queue()
    guard_rows = no_admission_guardrail()
    handoff_rows = next_agent_handoff()
    manifest_rows = source_manifest()

    write_csv(OUT / "upcomer_exchange_extraction_contract.csv", contract_rows)
    write_csv(OUT / "sampler_field_map.csv", field_rows)
    write_csv(OUT / "case_time_window_queue.csv", queue_rows)
    write_csv(OUT / "no_admission_guardrail.csv", guard_rows)
    write_csv(OUT / "next_agent_handoff.csv", handoff_rows)
    write_csv(OUT / "source_manifest.csv", manifest_rows)

    summary = {
        "task": TASK,
        "built_at_utc": utc_now(),
        "extraction_contract_rows": len(contract_rows),
        "sampler_field_group_rows": len(field_rows),
        "case_time_window_rows": len(queue_rows),
        "guardrail_rows": len(guard_rows),
        "handoff_rows": len(handoff_rows),
        "mainline_cases": sorted({row["case_id"] for row in queue_rows}),
        "required_field_groups": [row["field_group"] for row in field_rows],
        "any_fit_allowed_now": any(row["fit_allowed_now"] == "true" for row in contract_rows),
        "any_score_allowed_now": any(row["score_allowed_now"] == "true" for row in contract_rows),
        "residual_absorbed_into_internal_Nu": False,
        "native_output_mutation": False,
        "registry_mutation": False,
        "scheduler_mutation": False,
        "solver_or_postprocessing_or_sampler_launched": False,
        "fluid_edit": False,
        "external_repo_edit": False,
        "fitting_or_model_selection": False,
        "closure_admission_change": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "no_scorecard_outputs": True,
    }
    write_json(OUT / "summary.json", summary)
    (OUT / "README.md").write_text(readme(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
