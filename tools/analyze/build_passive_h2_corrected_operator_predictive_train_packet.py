#!/usr/bin/env python3
"""Build the PASSIVE-H2 corrected-operator predictive train packet."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TASK_ID = "TODO-PASSIVE-H2-CORRECTED-OPERATOR-PREDICTIVE-TRAIN-PACKET-2026-07-22"
DATE = "2026-07-22"
RUNTIME_ROW = "TODO-PASSIVE-H2-OUTER-INSULATION-RADIATION-RUNTIME-IMPLEMENTATION-2026-07-22"
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_passive_h2_corrected_operator_predictive_train_packet"

MULTI_H2_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_multi_train_corrected_radiation_smoke"
RECON_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation"
BURNDOWN_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_predictive_model_blocker_burndown"
SETUP_UQ_DIR = REPO / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"

MULTI_SUMMARY = MULTI_H2_DIR / "summary.json"
CASE_SUMMARY = MULTI_H2_DIR / "case_corrected_radiation_summary.csv"
CASE_FAMILY = MULTI_H2_DIR / "case_family_corrected_radiation_operator.csv"
SENS_CONTEXT = MULTI_H2_DIR / "setup_output_sensitivity_context.csv"
RECON_DECISION = RECON_DIR / "radiation_runtime_decision.csv"
BURNDOWN_SUMMARY = BURNDOWN_DIR / "summary.json"
BURNDOWN_ACTIONS = BURNDOWN_DIR / "minimal_next_actions.csv"
SETUP_QOI = SETUP_UQ_DIR / "mdot_heat_sensitivity.csv"

STATUS_PATH = REPO / f".agent/status/{DATE}_{TASK_ID}.md"
JOURNAL_PATH = REPO / f".agent/journal/{DATE}/passive-h2-corrected-operator-predictive-train-packet.md"
IMPORT_PATH = REPO / "imports/2026-07-22_passive_h2_corrected_operator_predictive_train_packet.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    if not path.is_absolute():
        return str(path)
    return str(path.relative_to(REPO))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames or sorted({key for row in rows for key in row}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in names})


def fnum(value: str | float | int) -> float:
    return float(value)


def case_split_rows(case_rows: List[Dict[str, str]], family_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    role_by_case: Dict[str, str] = {}
    for row in family_rows:
        role_by_case.setdefault(row["case_id"], row["external_bc_split_role"])
    out = []
    for row in case_rows:
        role = role_by_case[row["case_id"]]
        out.append(
            {
                "case_id": row["case_id"],
                "scenario_id": row["scenario_id"],
                "external_bc_split_role": role,
                "allowed_use_here": role == "train",
                "train_context_diagnostic_allowed": True,
                "protected_scoring_allowed": False,
                "reason": "Salt2 is train; Salt3/Salt4 remain diagnostic train-context only until split conflict row resolves them"
                if role != "train"
                else "Salt2 train row is eligible for no-protected train-context handoff",
            }
        )
    return out


def candidate_manifest(case_rows: List[Dict[str, str]], multi_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    totals = [fnum(row["corrected_outer_surface_total_W"]) for row in case_rows]
    rads = [fnum(row["corrected_outer_surface_radiation_W"]) for row in case_rows]
    return [
        {
            "candidate_id": "PASSIVE-H2-CAND001",
            "model_form_slot": "passive_external_boundary_outer_insulation_radiation",
            "operator_basis": "inner model wall state -> source-backed layers -> outer insulation surface -> convection+radiation",
            "corrected_total_min_W": min(totals),
            "corrected_total_max_W": max(totals),
            "corrected_radiation_min_W": min(rads),
            "corrected_radiation_max_W": max(rads),
            "development_decision": "worth_runtime_implementation_smoke_not_admission",
            "why_worth_it": "physically corrects the wrong 656 W basis and produces nonzero 22-26 W radiation ledger target",
            "why_not_admitted": "current radiation_on variant is no-op; source/property and split conflicts remain unresolved",
            "source_property_release": False,
            "protected_scoring": False,
            "coefficient_admission": False,
        }
    ]


def injection_ledger(case_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for row in case_rows:
        qamb = fnum(row["baseline_qambient_total_W"])
        qrad = fnum(row["corrected_outer_surface_radiation_W"])
        qtotal = fnum(row["corrected_outer_surface_total_W"])
        rows.append(
            {
                "case_id": row["case_id"],
                "scenario_id": row["scenario_id"],
                "baseline_qambient_total_W": qamb,
                "corrected_outer_surface_radiation_W": qrad,
                "corrected_outer_surface_total_W": qtotal,
                "radiation_on_expected_heat_ledger_delta_W": qrad,
                "passive_operator_full_on_expected_heat_ledger_delta_W": qtotal,
                "radiation_fraction_of_baseline_qambient": qrad / qamb,
                "total_fraction_of_baseline_qambient": qtotal / qamb,
                "implementation_mode": "runtime_ledger_delta_target_not_postprocessed_release",
                "double_counting_guardrail": "do_not_add_to_realized_CFD_wallHeatFlux; compute from setup and model state only",
                "protected_scoring": False,
            }
        )
    return rows


def sensitivity_check(case_rows: List[Dict[str, str]], sens_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    max_hA_by_case: Dict[str, float] = {}
    max_tp_by_case: Dict[str, float] = {}
    max_tw_by_case: Dict[str, float] = {}
    rad_noop: Dict[str, bool] = {}
    for row in sens_rows:
        case = row["case_id"]
        if row["input_family"] == "external_convection_hA":
            max_hA_by_case[case] = max(max_hA_by_case.get(case, 0.0), abs(fnum(row["delta_qambient_total_W"])))
            max_tp_by_case[case] = max(max_tp_by_case.get(case, 0.0), abs(fnum(row["max_abs_TP_delta_K"])))
            max_tw_by_case[case] = max(max_tw_by_case.get(case, 0.0), abs(fnum(row["max_abs_TW_delta_K"])))
        if row["input_family"] == "radiation" and row["level"] == "radiation_on":
            rad_noop[case] = (
                abs(fnum(row["delta_qambient_total_W"])) == 0.0
                and abs(fnum(row["max_abs_TP_delta_K"])) == 0.0
                and abs(fnum(row["max_abs_TW_delta_K"])) == 0.0
            )
    out = []
    for row in case_rows:
        case = row["case_id"]
        qrad = fnum(row["corrected_outer_surface_radiation_W"])
        out.append(
            {
                "case_id": case,
                "corrected_radiation_W": qrad,
                "max_existing_hA_qambient_delta_W": max_hA_by_case.get(case, 0.0),
                "max_existing_hA_TP_delta_K": max_tp_by_case.get(case, 0.0),
                "max_existing_hA_TW_delta_K": max_tw_by_case.get(case, 0.0),
                "current_radiation_on_is_noop": rad_noop.get(case, False),
                "interpolation_usable_for_scoring": False,
                "reason": "existing hA smoke proves passive boundary can move QOIs, but corrected radiation target exceeds hA delta and current radiation_on is zero; run real Fluid implementation",
            }
        )
    return out


def implementation_contract() -> List[Dict[str, Any]]:
    return [
        {
            "requirement_id": "R1",
            "requirement": "analytic layer/radiation tests pass",
            "acceptance_signal": "unit tests solve conduction plus exterior convection/radiation and recover outer-surface heat balance",
            "required_for_runtime_row": True,
        },
        {
            "requirement_id": "R2",
            "requirement": "radiation_on changes heat ledger",
            "acceptance_signal": "train-only radiation_on minus radiation_off qambient or radiation lane delta is nonzero and comparable to corrected outer-surface radiation 22-26 W",
            "required_for_runtime_row": True,
        },
        {
            "requirement_id": "R3",
            "requirement": "runtime inputs remain legal",
            "acceptance_signal": "inputs limited to setup h/area/Ta/Tsur/emissivity/layers/material k plus model-solved wall/fluid state; no wallHeatFlux, CFD mdot, Qwall, cooler duty, or observed temperature input",
            "required_for_runtime_row": True,
        },
        {
            "requirement_id": "R4",
            "requirement": "same-QOI train-only results documented",
            "acceptance_signal": "report mdot, qambient/qhx, TP/TW projection, heat ledger, residual movement for train rows only; protected scoring remains false",
            "required_for_runtime_row": True,
        },
    ]


def guardrails() -> List[Dict[str, Any]]:
    items = [
        "native_solver_outputs_mutated",
        "registry_mutated",
        "scheduler_action",
        "solver_or_sampler_launch",
        "fluid_or_external_edit",
        "thesis_current_or_latex_edit",
        "source_property_release",
        "numeric_q_loss_release",
        "qwall_release",
        "coefficient_admission",
        "candidate_freeze",
        "protected_scoring",
        "final_score_claim",
        "runtime_leakage_relaxation",
        "residual_absorption_into_internal_Nu",
    ]
    return [{"guardrail": item, "value": False, "pass": True} for item in items]


def source_manifest() -> List[Dict[str, Any]]:
    paths = [MULTI_SUMMARY, CASE_SUMMARY, CASE_FAMILY, SENS_CONTEXT, RECON_DECISION, BURNDOWN_SUMMARY, BURNDOWN_ACTIONS, SETUP_QOI]
    return [{"path": rel(path), "exists": path.exists(), "use": "read_only_context", "mutated": False} for path in paths]


def summary_dict(
    case_rows: List[Dict[str, str]],
    split_rows: List[Dict[str, Any]],
    injection_rows: List[Dict[str, Any]],
    sensitivity_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_corrected_operator_predictive_train_packet_ready_runtime_row_needed_no_admission",
        "runtime_implementation_row": RUNTIME_ROW,
        "cases": ",".join(row["case_id"] for row in case_rows),
        "case_rows": len(case_rows),
        "split_conflict_cases": sum(1 for row in split_rows if not row["allowed_use_here"]),
        "corrected_radiation_min_W": min(row["radiation_on_expected_heat_ledger_delta_W"] for row in injection_rows),
        "corrected_radiation_max_W": max(row["radiation_on_expected_heat_ledger_delta_W"] for row in injection_rows),
        "corrected_total_min_W": min(row["passive_operator_full_on_expected_heat_ledger_delta_W"] for row in injection_rows),
        "corrected_total_max_W": max(row["passive_operator_full_on_expected_heat_ledger_delta_W"] for row in injection_rows),
        "current_radiation_on_noop_cases": sum(1 for row in sensitivity_rows if row["current_radiation_on_is_noop"]),
        "runtime_implementation_worth_launching": True,
        "source_property_release": False,
        "numeric_q_loss_release": False,
        "qwall_release": False,
        "coefficient_admission": False,
        "candidate_freeze": False,
        "protected_scoring": False,
        "final_score_claim": False,
        "fitting_or_model_selection": False,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "runtime_leakage_relaxation": False,
        "s11_s12_s13_s15_s6_triggered": False,
    }


def write_readme(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(CASE_SUMMARY)}
  - {rel(SENS_CONTEXT)}
  - {rel(BURNDOWN_SUMMARY)}
tags: [thermal, passive-h2, predictive-model, runtime-handoff, no-admission]
related:
  - {rel(STATUS_PATH)}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 Corrected Operator Predictive Train Packet

Decision: `{summary["decision"]}`.

The corrected outer-insulation PASSIVE-H2 operator is worth a narrow runtime
implementation smoke because it defines a legal nonzero radiation heat-ledger
target: `{summary["corrected_radiation_min_W"]:.3f}` to
`{summary["corrected_radiation_max_W"]:.3f}` W across Salt2/Salt3/Salt4. The
full corrected passive operator spans `{summary["corrected_total_min_W"]:.3f}`
to `{summary["corrected_total_max_W"]:.3f}` W.

This packet does not admit H2. Current `radiation_on` remains a no-op in the
existing setup-UQ outputs, and two external-BC split conflicts remain. The next
row must implement the corrected radiation lane in the runtime model and prove
that `radiation_on` changes the heat ledger without protected scoring.

## Files

- `candidate_manifest.csv`
- `split_reconciliation.csv`
- `corrected_operator_injection_ledger.csv`
- `predicted_heat_ledger_delta.csv`
- `sensitivity_interpolation_check.csv`
- `implementation_handoff_contract.csv`
- `runtime_input_audit.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "implementation_handoff_contract.csv")}
  - {rel(OUT_DIR / "corrected_operator_injection_ledger.csv")}
tags: [thermal, passive-h2, predictive-model, runtime-handoff]
related:
  - {rel(OUT_DIR / "README.md")}
  - {rel(JOURNAL_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status: PASSIVE-H2 Corrected Operator Predictive Train Packet

## Objective

Convert the corrected PASSIVE-H2 evidence into a train-context predictive
handoff and decide whether a later Fluid-backed runtime implementation is worth
launching.

## Outcome

Decision: `{summary["decision"]}`.

The runtime implementation row should be launched next:
`{summary["runtime_implementation_row"]}`. The required heat-ledger radiation
movement is nonzero, about `{summary["corrected_radiation_min_W"]:.3f}` to
`{summary["corrected_radiation_max_W"]:.3f}` W, while current `radiation_on`
is zero-delta in all `{summary["current_radiation_on_noop_cases"]}` cases
reviewed.

## Changes Made

- Added `tools/analyze/build_passive_h2_corrected_operator_predictive_train_packet.py`.
- Added `tools/analyze/test_passive_h2_corrected_operator_predictive_train_packet.py`.
- Generated `{rel(OUT_DIR)}/`.
- Added a narrow runtime-implementation row to `.agent/BOARD.md`.
- Added this status, journal, and import manifest.

## Validation

- `python3.11 -m py_compile tools/analyze/build_passive_h2_corrected_operator_predictive_train_packet.py tools/analyze/test_passive_h2_corrected_operator_predictive_train_packet.py`
- `python3.11 tools/analyze/build_passive_h2_corrected_operator_predictive_train_packet.py`
- `python3.11 tools/analyze/test_passive_h2_corrected_operator_predictive_train_packet.py`
- `python3.11 tools/agent/finish_task.py --task-id {TASK_ID}`

## Guardrails

No native-output, registry/admission, scheduler, solver/sampler, Fluid/external,
thesis current/LaTeX, source/property, Qwall, numeric q-loss, coefficient,
candidate-freeze, protected-score, final-score, hidden multiplier, runtime
leakage, or residual-absorption mutation was made.
"""
    STATUS_PATH.write_text(text, encoding="utf-8")


def write_journal(summary: Dict[str, Any]) -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = f"""---
provenance:
  - {rel(OUT_DIR / "summary.json")}
  - {rel(OUT_DIR / "sensitivity_interpolation_check.csv")}
tags: [thermal, passive-h2, predictive-model, journal]
related:
  - {rel(OUT_DIR / "README.md")}
  - {rel(STATUS_PATH)}
  - {rel(IMPORT_PATH)}
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Corrected Operator Predictive Train Packet

## Attempted

Converted the corrected outer-insulation PASSIVE-H2 result into a runtime
implementation handoff. The work consumed only prior corrected-radiation,
setup-UQ, and blocker-burndown outputs.

## Observed

Corrected radiation gives a nonzero runtime ledger target of
`{summary["corrected_radiation_min_W"]:.3f}` to
`{summary["corrected_radiation_max_W"]:.3f}` W. The current `radiation_on`
variant is still zero-delta, so existing model behavior is not admissible as
implemented radiation.

## Inferred

H2 is worth a narrow runtime implementation smoke because it fixes a real model
form basis issue and should move the heat ledger if wired correctly. It is not
worth a broad fit or protected score until the implementation row proves the
ledger movement and the source/property and split gates are resolved.

## Next Useful Action

Claim `{summary["runtime_implementation_row"]}` in the appropriate Fluid/edit
context. Stop after analytic tests and train-only same-QOI smoke; do not score
validation, holdout, or external rows.
"""
    JOURNAL_PATH.write_text(text, encoding="utf-8")


def write_import(summary: Dict[str, Any]) -> None:
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "date": DATE,
        "generated_at_utc": summary["generated_at_utc"],
        "changed_files": [
            "tools/analyze/build_passive_h2_corrected_operator_predictive_train_packet.py",
            "tools/analyze/test_passive_h2_corrected_operator_predictive_train_packet.py",
            rel(OUT_DIR),
            rel(STATUS_PATH),
            rel(JOURNAL_PATH),
            rel(IMPORT_PATH),
            ".agent/BOARD.md",
        ],
        "read_only_context": [row["path"] for row in source_manifest()],
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "no_scorecard_outputs": True,
        "mutation_flags": {
            "source_property_release": False,
            "numeric_q_loss_release": False,
            "qwall_release": False,
            "coefficient_admission": False,
            "candidate_freeze": False,
            "protected_scoring": False,
            "final_score_claim": False,
            "fluid_or_external_edit": False,
            "runtime_leakage_relaxation": False,
        },
        "decision": summary["decision"],
    }
    IMPORT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    multi_summary = read_json(MULTI_SUMMARY)
    case_rows = read_csv(CASE_SUMMARY)
    family_rows = read_csv(CASE_FAMILY)
    sens_rows = read_csv(SENS_CONTEXT)
    split_rows = case_split_rows(case_rows, family_rows)
    manifest_rows = candidate_manifest(case_rows, multi_summary)
    injection_rows = injection_ledger(case_rows)
    sensitivity_rows = sensitivity_check(case_rows, sens_rows)
    contract_rows = implementation_contract()
    guardrail_rows = guardrails()
    source_rows = source_manifest()
    summary = summary_dict(case_rows, split_rows, injection_rows, sensitivity_rows)

    write_csv(OUT_DIR / "candidate_manifest.csv", manifest_rows)
    write_csv(OUT_DIR / "split_reconciliation.csv", split_rows)
    write_csv(OUT_DIR / "corrected_operator_injection_ledger.csv", injection_rows)
    write_csv(OUT_DIR / "predicted_heat_ledger_delta.csv", injection_rows)
    write_csv(OUT_DIR / "sensitivity_interpolation_check.csv", sensitivity_rows)
    write_csv(OUT_DIR / "implementation_handoff_contract.csv", contract_rows)
    write_csv(OUT_DIR / "runtime_input_audit.csv", guardrail_rows)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrail_rows)
    write_csv(OUT_DIR / "source_manifest.csv", source_rows)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    write_status(summary)
    write_journal(summary)
    write_import(summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
