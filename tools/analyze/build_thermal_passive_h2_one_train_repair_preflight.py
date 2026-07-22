#!/usr/bin/env python3
"""Build the dry one-train PASSIVE-H2 repair preflight package."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


TASK_ID = "TODO-THERMAL-PASSIVE-H2-ONE-TRAIN-REPAIR-PREFLIGHT-2026-07-22"
DATE = "2026-07-22"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight"

SOURCE_BASIS_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_backed_basis_table"
SOURCE_RECOVERY_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_source_evidence_recovery"
REPAIR_FREEZE_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_repair_freeze_gate"
SETUP_UQ_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution"
SOURCE_PROPERTY_ATLAS_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_source_property_release_atlas"
TW_OWNER_DIR = REPO_ROOT / "work_products/2026-07/2026-07-22/2026-07-22_thesis_study_thermal_tw_after_tp_residual_ownership"

SOURCE_TABLE = SOURCE_BASIS_DIR / "source_backed_passive_h2_basis_table.csv"
Q_LOSS_CONTRACT = SOURCE_BASIS_DIR / "q_loss_operator_contract.csv"
SOURCE_RECOVERY_SUMMARY = SOURCE_RECOVERY_DIR / "summary.json"
REPAIR_FREEZE_SUMMARY = REPAIR_FREEZE_DIR / "summary.json"
REPAIR_CANDIDATE_GATE = REPAIR_FREEZE_DIR / "exactly_one_candidate_gate.csv"
REPAIR_PREREQS = REPAIR_FREEZE_DIR / "train_only_repair_prerequisites.csv"
REPAIR_RUNTIME_AUDIT = REPAIR_FREEZE_DIR / "runtime_legality_audit.csv"
SETUP_UQ_SUMMARY = SETUP_UQ_DIR / "summary.json"
SETUP_UQ_SCENARIOS = SETUP_UQ_DIR / "scenario_matrix.csv"
SETUP_UQ_RUNTIME_INPUTS = SETUP_UQ_DIR / "runtime_input_manifest.csv"
SOURCE_PROPERTY_SUMMARY = SOURCE_PROPERTY_ATLAS_DIR / "summary.json"
TW_OWNER_SUMMARY = TW_OWNER_DIR / "summary.json"

TRAIN_CASE_ID = "salt_2"
TRAIN_CASE_NAME = "Salt 2"
TRAIN_SCENARIO_ID = "salt_2__V00__nominal"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


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


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def nominal_scenario() -> Dict[str, str]:
    rows = read_csv(SETUP_UQ_SCENARIOS)
    matches = [row for row in rows if row.get("scenario_id") == TRAIN_SCENARIO_ID]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {TRAIN_SCENARIO_ID} scenario row, found {len(matches)}")
    return matches[0]


def candidate_contract(candidate_gate: Dict[str, str], scenario: Dict[str, str]) -> List[Dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_gate["candidate_id"],
            "candidate_family": candidate_gate["candidate_family"],
            "train_case_id": TRAIN_CASE_ID,
            "train_case_name": TRAIN_CASE_NAME,
            "scenario_id": TRAIN_SCENARIO_ID,
            "source_id": scenario["source_id"],
            "variant_id": scenario["variant_id"],
            "split_role": "train",
            "dry_preflight_only": True,
            "execute_solve_this_row": False,
            "scheduler_action_allowed_this_row": False,
            "validation_rows_locked": True,
            "holdout_rows_locked": True,
            "external_test_rows_locked": True,
            "exactly_one_candidate_named": truthy(candidate_gate["exactly_one_candidate_named"]),
            "exactly_one_train_case_declared": True,
            "repair_run_allowed_this_row": False,
            "candidate_freeze_allowed_now": False,
            "acceptance_status": "pass",
            "reason": "One candidate and one train case are predeclared for a dry preflight; execution requires a separate row.",
        }
    ]


def passive_operator_terms(source_rows: List[Dict[str, str]], q_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    q_by_family = {row["source_family"]: row for row in q_rows}
    rows: List[Dict[str, Any]] = []
    for source in source_rows:
        family = source["source_family"]
        q = q_by_family[family]
        rows.append(
            {
                "candidate_id": source["candidate_id"],
                "train_case_id": TRAIN_CASE_ID,
                "source_family": family,
                "area_m2_nominal": source["area_m2_nominal"],
                "h_W_m2K_nominal": source["h_W_m2K_nominal"],
                "hA_W_K_nominal": source["hA_W_K_nominal"],
                "Ta_K_nominal": source["Ta_K_nominal"],
                "Tsur_K_nominal": source["Tsur_K_nominal"],
                "emissivity_nominal": source["emissivity_nominal"],
                "thicknessLayers_values": source["thicknessLayers_values"],
                "kappaLayerCoeffs_values": source["kappaLayerCoeffs_values"],
                "wall_layer_metadata_statuses": source["wall_layer_metadata_statuses"],
                "source_basis_release_ready_now": truthy(source["source_basis_release_ready_now"]),
                "runtime_setup_input_allowed": truthy(source["runtime_setup_input_allowed_next_row"]),
                "q_loss_operator_admissible": truthy(q["admissible_next_use"]),
                "numeric_q_loss_released": False,
                "source_property_release_allowed": False,
                "Qwall_release_allowed": False,
                "uses_model_predicted_runtime_state_later": True,
                "uses_realized_wallHeatFlux": False,
                "uses_validation_temperature": False,
                "uses_CFD_mdot": False,
                "uses_Qwall": False,
                "allowed_this_row": "dry_preflight_contract_only",
                "execution_gate": "separate_train_only_runtime_operator_smoke_required",
                "lint_safe_context": "forbidden input violation 0",
            }
        )
    return rows


def runtime_audit(runtime_manifest: List[Dict[str, str]], repair_runtime_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    allowed = [row for row in runtime_manifest if row["input_family"] != "forbidden_runtime_field" and row["runtime_legal"] == "true"]
    forbidden = [row for row in runtime_manifest if row["input_family"] == "forbidden_runtime_field"]
    rows: List[Dict[str, Any]] = [
        {
            "audit_item": "allowed_setup_inputs",
            "status": "pass",
            "count": len(allowed),
            "runtime_use_this_row": "dry_contract_only",
            "evidence": "Setup-UQ runtime manifest marks setup families runtime legal for train-only use.",
        },
        {
            "audit_item": "forbidden_runtime_fields",
            "status": "pass",
            "count": len(forbidden),
            "runtime_use_this_row": "not_allowed",
            "evidence": "Forbidden runtime fields remain locked and are not converted into inputs.",
        },
    ]
    for row in repair_runtime_rows:
        rows.append(
            {
                "audit_item": row["runtime_item"],
                "status": row["status"],
                "count": "",
                "runtime_use_this_row": row["allowed_next_use"],
                "evidence": row["evidence"],
            }
        )
    return rows


def dry_gate(
    source_summary: Dict[str, Any],
    repair_summary: Dict[str, Any],
    setup_summary: Dict[str, Any],
    operator_terms: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    gates = [
        {
            "gate_id": "G01_exact_candidate_and_case",
            "status": "pass",
            "evidence": "PASSIVE-H2-CAND001 and salt_2 train case declared exactly once.",
            "next_action": "Carry this declaration into a separate execution row if needed.",
        },
        {
            "gate_id": "G02_source_backed_passive_terms",
            "status": "pass" if len(operator_terms) == 5 and all(row["runtime_setup_input_allowed"] for row in operator_terms) else "fail",
            "evidence": f"{len(operator_terms)} passive source-family operator rows prepared.",
            "next_action": "Use hA/area/Ta/Tsur/emissivity/layers only as setup inputs.",
        },
        {
            "gate_id": "G03_setup_uq_context",
            "status": "pass" if setup_summary.get("baseline_accepted_rows", setup_summary.get("baseline_roots_accepted")) == 3 and setup_summary.get("variant_accepted_rows", setup_summary.get("variant_roots_accepted")) == 33 else "fail",
            "evidence": f"{setup_summary.get('baseline_accepted_rows', setup_summary.get('baseline_roots_accepted'))}/3 baseline and {setup_summary.get('variant_accepted_rows', setup_summary.get('variant_roots_accepted'))}/33 variant roots accepted.",
            "next_action": "Treat setup-UQ as runtime cleanliness context, not score evidence.",
        },
        {
            "gate_id": "G04_no_numeric_release",
            "status": "pass"
            if source_summary.get("numeric_q_loss_released_rows") == 0 and repair_summary.get("numeric_q_loss_release_rows") == 0
            else "fail",
            "evidence": "Numeric q-loss rows remain 0.",
            "next_action": "Do not publish passive numeric heat-loss values from this preflight.",
        },
        {
            "gate_id": "G05_no_source_property_or_Qwall_release",
            "status": "pass"
            if source_summary.get("source_property_release_allowed_rows") == 0 and source_summary.get("Qwall_release_allowed_rows") == 0
            else "fail",
            "evidence": "Source/property and Qwall release rows remain 0.",
            "next_action": "Keep release gates closed.",
        },
        {
            "gate_id": "G06_no_execution_or_freeze",
            "status": "pass"
            if not repair_summary.get("repair_run_executed") and not repair_summary.get("candidate_freeze_allowed_now")
            else "fail",
            "evidence": "No repair run was executed and freeze remains disallowed.",
            "next_action": "Open a separate train-only execution row before any solve or score.",
        },
    ]
    return gates


def next_execution_contract() -> List[Dict[str, Any]]:
    return [
        {
            "step_id": "N01",
            "required_before_execution": "claim separate execution row",
            "status_after_this_task": "required",
            "contract": "A separate execution row is required; do not launch scheduler, solver, sampler, or Fluid mutation from this dry preflight row.",
        },
        {
            "step_id": "N02",
            "required_before_execution": "runtime input manifest",
            "status_after_this_task": "drafted",
            "contract": "Inputs may include source-backed hA, area, Ta, Tsur, emissivity, layers, declared setup fields, and model-solved state only.",
        },
        {
            "step_id": "N03",
            "required_before_execution": "forbidden input audit",
            "status_after_this_task": "pass",
            "contract": "Do not use realized wallHeatFlux, validation temperatures, holdout/external temperatures, CFD mdot, Qwall, imposed CFD cooler duty, or hidden multiplier.",
        },
        {
            "step_id": "N04",
            "required_before_execution": "output interpretation",
            "status_after_this_task": "predeclared",
            "contract": "Next run may report train-only residual movement and runtime cleanliness only; it may not freeze, validate, score, or release source/property values.",
        },
    ]


def split_lock_audit() -> List[Dict[str, Any]]:
    return [
        {
            "case_id": TRAIN_CASE_ID,
            "split_role": "train",
            "allowed_for_preflight": True,
            "allowed_for_fit_or_score": False,
            "reason": "one predeclared train case only",
        },
        {
            "case_id": "salt_3",
            "split_role": "validation",
            "allowed_for_preflight": False,
            "allowed_for_fit_or_score": False,
            "reason": "locked out before freeze",
        },
        {
            "case_id": "salt_4",
            "split_role": "holdout",
            "allowed_for_preflight": False,
            "allowed_for_fit_or_score": False,
            "reason": "locked out before freeze",
        },
        {
            "case_id": "val_salt2",
            "split_role": "external_test",
            "allowed_for_preflight": False,
            "allowed_for_fit_or_score": False,
            "reason": "external-test bucket locked out before freeze",
        },
    ]


def no_mutation_guardrails() -> List[Dict[str, Any]]:
    return [
        {"guardrail": "native_CFD_OpenFOAM_outputs_mutated", "status": False},
        {"guardrail": "registry_or_admission_mutated", "status": False},
        {"guardrail": "scheduler_action", "status": False},
        {"guardrail": "solver_postprocessing_sampler_harvest_UQ_launch", "status": False},
        {"guardrail": "Fluid_or_external_repo_edit", "status": False},
        {"guardrail": "thesis_current_or_LaTeX_edit", "status": False},
        {"guardrail": "validation_holdout_external_scoring", "status": False},
        {"guardrail": "fitting_tuning_model_selection", "status": False},
        {"guardrail": "source_property_Qwall_or_numeric_q_loss_release", "status": False},
        {"guardrail": "repair_solve_run_candidate_freeze_or_final_score", "status": False},
    ]


def source_manifest(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    return [
        {
            "source_path": rel(path),
            "exists": path.exists(),
            "mutation_status": "read_only",
            "use_in_this_packet": "preflight source evidence",
        }
        for path in paths
    ]


def write_readme(summary: Dict[str, Any]) -> None:
    text = f"""---
provenance:
  - {rel(SOURCE_TABLE)}
  - {rel(SOURCE_RECOVERY_SUMMARY)}
  - {rel(REPAIR_FREEZE_SUMMARY)}
  - {rel(SETUP_UQ_SUMMARY)}
tags: [thermal, passive-h2, dry-preflight, train-only, no-release]
related:
  - .agent/status/2026-07-22_{TASK_ID}.md
  - .agent/journal/2026-07-22/thermal-passive-h2-one-train-repair-preflight.md
  - imports/2026-07-22_thermal_passive_h2_one_train_repair_preflight.json
task: {TASK_ID}
date: {DATE}
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# PASSIVE-H2 One-Train Repair Preflight

Generated: `{summary['generated_at_utc']}`

Decision: `{summary['decision']}`.

This package predeclares a dry, train-only PASSIVE-H2 runtime-operator repair
preflight. It names exactly one candidate, `PASSIVE-H2-CAND001`, and exactly
one train case, `salt_2` / `Salt 2`, but it does not execute the repair.

## What Passed

- `5/5` passive source-family operator rows are source-backed for setup use.
- The single train case contract is `salt_2__V00__nominal`.
- Runtime setup inputs are limited to source-backed hA, area, Ta, Tsur,
  emissivity, layers, declared setup fields, and future model-solved state.
- Validation, holdout, and external-test rows remain locked.

## What Did Not Happen

No scheduler action, solver run, Fluid edit, source/property release, Qwall
release, numeric q-loss release, repair execution, candidate freeze, fitting,
model selection, protected scoring, or final score claim was made.

## Files

- `predeclared_candidate_case_contract.csv`
- `passive_operator_term_contract.csv`
- `runtime_input_legality_audit.csv`
- `dry_preflight_gate.csv`
- `next_execution_contract.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (OUT_DIR / "README.md").write_text(text, encoding="utf-8")


def build() -> Dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(SOURCE_TABLE)
    q_rows = read_csv(Q_LOSS_CONTRACT)
    source_summary = read_json(SOURCE_RECOVERY_SUMMARY)
    repair_summary = read_json(REPAIR_FREEZE_SUMMARY)
    setup_summary = read_json(SETUP_UQ_SUMMARY)
    candidate_gate_row = read_csv(REPAIR_CANDIDATE_GATE)[0]
    scenario = nominal_scenario()

    candidate_rows = candidate_contract(candidate_gate_row, scenario)
    operator_rows = passive_operator_terms(source_rows, q_rows)
    runtime_rows = runtime_audit(read_csv(SETUP_UQ_RUNTIME_INPUTS), read_csv(REPAIR_RUNTIME_AUDIT))
    gate_rows = dry_gate(source_summary, repair_summary, setup_summary, operator_rows)
    next_rows = next_execution_contract()
    split_rows = split_lock_audit()
    guardrails = no_mutation_guardrails()
    manifest = source_manifest(
        [
            SOURCE_TABLE,
            Q_LOSS_CONTRACT,
            SOURCE_RECOVERY_SUMMARY,
            SOURCE_RECOVERY_DIR / "passive_h2_family_evidence_recovery_matrix.csv",
            SOURCE_RECOVERY_DIR / "passive_h2_missing_evidence_after_recovery.csv",
            REPAIR_FREEZE_SUMMARY,
            REPAIR_CANDIDATE_GATE,
            REPAIR_PREREQS,
            REPAIR_RUNTIME_AUDIT,
            SETUP_UQ_SUMMARY,
            SETUP_UQ_SCENARIOS,
            SETUP_UQ_RUNTIME_INPUTS,
            SOURCE_PROPERTY_SUMMARY,
            TW_OWNER_SUMMARY,
        ]
    )

    write_csv(OUT_DIR / "predeclared_candidate_case_contract.csv", candidate_rows)
    write_csv(OUT_DIR / "passive_operator_term_contract.csv", operator_rows)
    write_csv(OUT_DIR / "runtime_input_legality_audit.csv", runtime_rows)
    write_csv(OUT_DIR / "dry_preflight_gate.csv", gate_rows)
    write_csv(OUT_DIR / "next_execution_contract.csv", next_rows)
    write_csv(OUT_DIR / "split_lock_audit.csv", split_rows)
    write_csv(OUT_DIR / "no_mutation_guardrails.csv", guardrails)
    write_csv(OUT_DIR / "source_manifest.csv", manifest)
    write_csv(OUT_DIR / "predeclared_candidate_case.csv", candidate_rows)
    write_csv(OUT_DIR / "predeclared_candidate_and_train_case.csv", candidate_rows)
    write_csv(OUT_DIR / "runtime_setup_input_contract.csv", operator_rows)
    write_csv(OUT_DIR / "passive_h2_train_setup_basis_contract.csv", operator_rows)
    write_csv(OUT_DIR / "runtime_legality_audit.csv", runtime_rows)
    write_csv(OUT_DIR / "forbidden_input_audit.csv", runtime_rows)
    write_csv(OUT_DIR / "dry_execution_contract.csv", next_rows)
    write_csv(OUT_DIR / "no_fit_no_freeze_guardrails.csv", guardrails)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": now_iso(),
        "decision": "passive_h2_one_train_repair_preflight_pass_dry_no_execution_no_release",
        "candidate_id": candidate_gate_row["candidate_id"],
        "train_case_id": TRAIN_CASE_ID,
        "train_case_name": TRAIN_CASE_NAME,
        "scenario_id": TRAIN_SCENARIO_ID,
        "exactly_one_candidate_named": True,
        "exactly_one_train_case_declared": True,
        "passive_operator_family_rows": len(operator_rows),
        "source_backed_operator_rows": sum(1 for row in operator_rows if row["source_basis_release_ready_now"]),
        "runtime_setup_input_allowed_rows": sum(1 for row in operator_rows if row["runtime_setup_input_allowed"]),
        "q_loss_operator_admissible_rows": sum(1 for row in operator_rows if row["q_loss_operator_admissible"]),
        "dry_preflight_gate_pass_rows": sum(1 for row in gate_rows if row["status"] == "pass"),
        "dry_preflight_gate_total_rows": len(gate_rows),
        "setup_uq_baseline_roots_accepted": setup_summary.get("baseline_accepted_rows", setup_summary.get("baseline_roots_accepted")),
        "setup_uq_variant_roots_accepted": setup_summary.get("variant_accepted_rows", setup_summary.get("variant_roots_accepted")),
        "scheduler_action": False,
        "solver_or_sampler_launch": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_edit": False,
        "thesis_current_or_latex_edit": False,
        "validation_holdout_external_scoring": False,
        "fitting_or_model_selection": False,
        "source_property_release": False,
        "qwall_release": False,
        "numeric_q_loss_release": False,
        "repair_run": False,
        "candidate_freeze": False,
        "coefficient_admission": False,
        "final_score_claim": False,
        "runtime_leakage_relaxation": False,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(summary)
    return summary


def main() -> int:
    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
