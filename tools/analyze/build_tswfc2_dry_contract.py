#!/usr/bin/env python3
"""Build AGENT-541 TSWFC2 distributed wall/fluid dry contract."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TASK = "AGENT-541"
DATE = "2026-07-18"
ROOT = Path(__file__).resolve().parents[2]
OUT_REL = Path("work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract")
OUT = ROOT / OUT_REL

SOURCES = {
    "tp_tw_summary": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/summary.json",
    "tp_tw_candidates": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/candidate_family_gate_matrix.csv",
    "tp_tw_requirements": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/physics_requirement_matrix.csv",
    "tp_tw_next_contract": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/next_model_contract.csv",
    "blocker_synthesis": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/research_paths.csv",
    "source_property_summary": ROOT / "work_products/2026-07/2026-07-18/2026-07-18_source_envelope_property_carryforward/summary.json",
    "tswfc1_readme": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md",
    "tswfc1_admission": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/candidate_admission_review.csv",
    "wall_audit": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/README.md",
    "wall_failure_modes": ROOT / "work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/invariant_failure_modes.csv",
}

NODE_COLUMNS = [
    "node_id",
    "role",
    "parent_segment",
    "axial_zone",
    "fluid_state",
    "inner_wall_state",
    "outer_wall_state",
    "ambient_or_radiation_state",
    "required_setup_inputs",
    "forbidden_runtime_inputs",
    "status_before_implementation",
]

HEAT_COLUMNS = [
    "ledger_id",
    "node_scope",
    "term",
    "sign_convention",
    "required_output",
    "closure_source",
    "energy_balance_requirement",
    "forbidden_shortcut",
]

RUNTIME_COLUMNS = [
    "gate_id",
    "input_or_behavior",
    "required_status",
    "reason",
    "source_paths",
]

SCORE_COLUMNS = [
    "gate_id",
    "split_role",
    "rows",
    "metric",
    "acceptance_signal",
    "hard_no_go",
]

DISTINCTION_COLUMNS = [
    "dimension",
    "tswfc1_observed_behavior",
    "tswfc2_required_difference",
    "acceptance_signal",
    "source_paths",
]

NEXT_COLUMNS = [
    "rank",
    "next_step_id",
    "action",
    "blocked_by",
    "acceptance_signal",
    "guardrails",
]

MANIFEST_COLUMNS = ["source_id", "path", "exists", "role"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return data


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({column: "" if row.get(column) is None else str(row.get(column, "")) for column in columns})
    return len(materialized)


def require_sources() -> None:
    missing = [rel(path) for path in SOURCES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AGENT-541 source files: " + "; ".join(missing))


def build_node_contract() -> list[dict[str, Any]]:
    common_forbidden = "realized CFD test-section net heat; CFD wallHeatFlux; CFD mdot; imposed CFD cooler duty; validation TP/TW temperatures"
    setup_inputs = "segment length/elevation/diameter; wall thickness/material; setup hA/radiation/coverage rows; heater/cooler setup models; selected property mode"
    return [
        {
            "node_id": "TSWFC2_N01_pre_test_upper_upcomer",
            "role": "left_upper_vertical",
            "parent_segment": "left_upper_vertical",
            "axial_zone": "pre_test_section_bracket",
            "fluid_state": "bulk fluid temperature and enthalpy flow entering the test-section bracket",
            "inner_wall_state": "inner pipe wall temperature for upstream bracket node",
            "outer_wall_state": "outer wall or surface temperature for upstream bracket node",
            "ambient_or_radiation_state": "setup ambient/radiation boundary only",
            "required_setup_inputs": setup_inputs,
            "forbidden_runtime_inputs": common_forbidden,
            "status_before_implementation": "required_missing",
        },
        {
            "node_id": "TSWFC2_N02_test_section_lower",
            "role": "test_section",
            "parent_segment": "left_upper_vertical",
            "axial_zone": "test_section_lower",
            "fluid_state": "bulk fluid temperature and enthalpy flow through lower test-section subnode",
            "inner_wall_state": "inner wall state coupled to local fluid node",
            "outer_wall_state": "outer wall/surface state coupled through wall resistance",
            "ambient_or_radiation_state": "setup ambient/radiation boundary only",
            "required_setup_inputs": setup_inputs,
            "forbidden_runtime_inputs": common_forbidden,
            "status_before_implementation": "required_missing",
        },
        {
            "node_id": "TSWFC2_N03_test_section_upper",
            "role": "test_section",
            "parent_segment": "left_upper_vertical",
            "axial_zone": "test_section_upper",
            "fluid_state": "bulk fluid temperature and enthalpy flow through upper test-section subnode",
            "inner_wall_state": "inner wall state coupled to local fluid node",
            "outer_wall_state": "outer wall/surface state coupled through wall resistance",
            "ambient_or_radiation_state": "setup ambient/radiation boundary only",
            "required_setup_inputs": setup_inputs,
            "forbidden_runtime_inputs": common_forbidden,
            "status_before_implementation": "required_missing",
        },
        {
            "node_id": "TSWFC2_N04_post_test_upper_upcomer",
            "role": "left_upper_vertical",
            "parent_segment": "left_upper_vertical",
            "axial_zone": "post_test_section_bracket",
            "fluid_state": "bulk fluid temperature and enthalpy flow leaving the test-section bracket",
            "inner_wall_state": "inner pipe wall temperature for downstream bracket node",
            "outer_wall_state": "outer wall or surface temperature for downstream bracket node",
            "ambient_or_radiation_state": "setup ambient/radiation boundary only",
            "required_setup_inputs": setup_inputs,
            "forbidden_runtime_inputs": common_forbidden,
            "status_before_implementation": "required_missing",
        },
    ]


def build_heat_ledger_contract() -> list[dict[str, Any]]:
    return [
        {
            "ledger_id": "HL1_fluid_axial_enthalpy",
            "node_scope": "each TSWFC2 node and bracket",
            "term": "mdot_cp_dT",
            "sign_convention": "positive adds heat to fluid control volume",
            "required_output": "per-node fluid enthalpy in/out and residual_W",
            "closure_source": "setup heater/cooler inputs plus solved fluid temperatures",
            "energy_balance_requirement": "sum of node heat terms closes within declared tolerance before scoring",
            "forbidden_shortcut": "do not use CFD mdot or validation temperatures to close residual",
        },
        {
            "ledger_id": "HL2_internal_convection",
            "node_scope": "fluid to inner wall for each TSWFC2 node",
            "term": "q_fluid_inner_wall_W",
            "sign_convention": "positive leaves fluid and enters wall",
            "required_output": "per-node internal convection heat transfer and driving deltaT",
            "closure_source": "predeclared internal Nu/HTC rule or diagnostic placeholder",
            "energy_balance_requirement": "equal and opposite fluid/wall entries per node",
            "forbidden_shortcut": "do not tune internal HTC from Salt3, perturbation, blind, or realized wallHeatFlux rows",
        },
        {
            "ledger_id": "HL3_wall_conduction_storage",
            "node_scope": "inner wall to outer wall for each TSWFC2 node",
            "term": "q_wall_conduction_W",
            "sign_convention": "positive moves heat outward",
            "required_output": "inner/outer wall temperatures, wall resistance, optional storage flag",
            "closure_source": "setup material and geometry only",
            "energy_balance_requirement": "wall term balances internal convection and external loss/source terms",
            "forbidden_shortcut": "do not replace distributed wall state with one bulk-to-ambient resistance",
        },
        {
            "ledger_id": "HL4_external_loss_or_gain",
            "node_scope": "outer wall/surface to ambient/radiation boundary",
            "term": "q_external_W",
            "sign_convention": "positive leaves wall to ambient",
            "required_output": "per-node external convection/radiation heat term and boundary labels",
            "closure_source": "setup external hA/radiation/coverage rows",
            "energy_balance_requirement": "external terms remain separated from internal Nu and heater/cooler source terms",
            "forbidden_shortcut": "do not absorb test-section residual into global passive hA or cooler compensation",
        },
    ]


def build_runtime_audit() -> list[dict[str, Any]]:
    sources = f"{rel(SOURCES['tp_tw_requirements'])};{rel(SOURCES['tp_tw_next_contract'])}"
    return [
        {
            "gate_id": "RA1_setup_only_inputs",
            "input_or_behavior": "runtime input table",
            "required_status": "only setup geometry, material, ambient/radiation, property, heater, and admitted cooler setup inputs allowed",
            "reason": "predictive mode cannot consume realized CFD heat, mdot, or validation temperatures",
            "source_paths": sources,
        },
        {
            "gate_id": "RA2_distributed_nodes_present",
            "input_or_behavior": "node topology",
            "required_status": "at least four axial nodes with fluid, inner-wall, outer-wall, and external boundary states",
            "reason": "AGENT-526 single-node bulk-to-ambient fallback failed and must not be duplicated",
            "source_paths": f"{rel(SOURCES['tp_tw_candidates'])};{rel(SOURCES['tswfc1_admission'])}",
        },
        {
            "gate_id": "RA3_salt1_role_rows",
            "input_or_behavior": "case split readiness",
            "required_status": "Salt1/Salt2/Salt4 nominal fit-selection rows exist or the grid is blocked explicitly",
            "reason": "final predictive split requires Salt1-4 nominal training envelope; missing Salt1 role rows cannot be silently omitted",
            "source_paths": rel(SOURCES["tp_tw_next_contract"]),
        },
        {
            "gate_id": "RA4_root_and_output_integrity",
            "input_or_behavior": "solver dry-run outputs",
            "required_status": "accepted train roots and finite TP/TW/probe outputs before expansion",
            "reason": "rejected roots or finite-output gaps invalidate score expansion",
            "source_paths": rel(SOURCES["tp_tw_next_contract"]),
        },
        {
            "gate_id": "RA5_source_property_labels",
            "input_or_behavior": "scorecard metadata",
            "required_status": "property and source-validity labels carried on every candidate row",
            "reason": "AGENT-538 requires source/property labels before future scorecards report fits or admissions",
            "source_paths": rel(SOURCES["source_property_summary"]),
        },
    ]


def build_score_gate_contract() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "SG1_train_nominal",
            "split_role": "fit_selection",
            "rows": "Salt1/Salt2/Salt4 nominal if Salt1 role rows exist; otherwise block before scoring",
            "metric": "accepted roots; mdot abs error; TP RMSE; TW RMSE; all-probe RMSE",
            "acceptance_signal": "no worse than M3 and best prior wall/source candidate on every declared train metric",
            "hard_no_go": "Salt1 omission without release gate; rejected train root; mdot-only improvement",
        },
        {
            "gate_id": "SG2_validation_holdout",
            "split_role": "score_only",
            "rows": "Salt3 nominal plus current holdout/blind rows after adapters exist",
            "metric": "delta vs M3 and prior candidates for mdot, TP, TW, all-probe, TW5, TW6, TP5, TP6, TW8",
            "acceptance_signal": "thermal-shape probes improve without new compensation failures",
            "hard_no_go": "Salt3 or blind rows used for parameter choice",
        },
        {
            "gate_id": "SG3_sensor_policy",
            "split_role": "score_policy",
            "rows": "frozen sensor map",
            "metric": "TP2 only if finite projection gates pass; TW10 excluded until active-HX shell-state output exists; TW5/TW6 always scoreable",
            "acceptance_signal": "candidate improves scoreable sensors rather than changing sensor policy",
            "hard_no_go": "posthoc sensor exclusion or residual-driven sensor-map changes",
        },
    ]


def build_distinction_rows() -> list[dict[str, Any]]:
    source_paths = f"{rel(SOURCES['tswfc1_readme'])};{rel(SOURCES['tp_tw_candidates'])}"
    return [
        {
            "dimension": "topology",
            "tswfc1_observed_behavior": "single test-section bulk-to-ambient series resistance on one role row",
            "tswfc2_required_difference": "distributed axial nodes with separate fluid, inner-wall, outer-wall, and ambient/radiation states",
            "acceptance_signal": "node contract has multiple axial nodes and no single bulk-to-ambient replacement",
            "source_paths": source_paths,
        },
        {
            "dimension": "energy ledger",
            "tswfc1_observed_behavior": "local series-resistance behavior completed but failed TP/TW/all-probe gates",
            "tswfc2_required_difference": "per-node conservation ledger separating axial enthalpy, internal convection, wall conduction/storage, and external loss",
            "acceptance_signal": "per-node residuals are finite and separated before scorecard generation",
            "source_paths": source_paths,
        },
        {
            "dimension": "selection objective",
            "tswfc1_observed_behavior": "mdot improved for candidates while validation and holdout thermal gates failed",
            "tswfc2_required_difference": "candidate cannot expand or admit unless mdot, TP, TW, and all-probe gates all pass",
            "acceptance_signal": "candidate_admission_review has zero mdot-only admissions",
            "source_paths": source_paths,
        },
        {
            "dimension": "runtime evidence",
            "tswfc1_observed_behavior": "process-local adapter used setup-only data but still lacked sufficient distributed thermal shape",
            "tswfc2_required_difference": "persistent implementation must expose setup-only distributed states without realized CFD heat or validation temperatures",
            "acceptance_signal": "runtime audit passes with no forbidden inputs",
            "source_paths": source_paths,
        },
    ]


def build_next_steps() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "next_step_id": "NS1_wait_for_or_read_umx1_api_result",
            "action": "Inspect AGENT-540 completion before promoting TSWFC2 to primary scoring path.",
            "blocked_by": "active AGENT-540 owns Fluid UMX1 API paths",
            "acceptance_signal": "AGENT-540 status says real hook implemented, rejected, or blocked with source paths",
            "guardrails": "do not edit Fluid or launch TSWFC2 grid while AGENT-540 is active",
        },
        {
            "rank": 2,
            "next_step_id": "NS2_external_fluid_design_row_if_needed",
            "action": "If UMX1 is rejected or unavailable, open a separate Fluid design row for TSWFC2 distributed node interfaces.",
            "blocked_by": "no claimed external Fluid edit authority in AGENT-541",
            "acceptance_signal": "Fluid design declares node state schema, setup inputs, outputs, root behavior, and no-op/default behavior",
            "guardrails": "no broad Fluid refactor; no score grid in the API design row",
        },
        {
            "rank": 3,
            "next_step_id": "NS3_small_no_solver_contract_review",
            "action": "Review this dry contract against AGENT-536 requirement R2 and AGENT-526 failure evidence.",
            "blocked_by": "none",
            "acceptance_signal": "review confirms TSWFC2 differs from TSWFC1 and carries runtime/input/sensor/source-property gates",
            "guardrails": "do not weaken gates to admit mdot-only improvement",
        },
        {
            "rank": 4,
            "next_step_id": "NS4_future_smoke_only_after_api",
            "action": "After API contract passes, run one or two predeclared smoke cases before any grid expansion.",
            "blocked_by": "missing API implementation and accepted-root dry audit",
            "acceptance_signal": "finite outputs, accepted roots, per-node heat ledger, and no forbidden runtime inputs",
            "guardrails": "scheduler work requires a new row and compute-resource handoff",
        },
    ]


def build_source_manifest() -> list[dict[str, Any]]:
    return [{"source_id": key, "path": rel(path), "exists": path.exists(), "role": "read-only synthesis input"} for key, path in SOURCES.items()]


def write_readme(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        f"""---
provenance:
  - {rel(SOURCES['tp_tw_summary'])}
  - {rel(SOURCES['tp_tw_requirements'])}
  - {rel(SOURCES['tp_tw_next_contract'])}
  - {rel(SOURCES['tswfc1_readme'])}
  - {rel(SOURCES['wall_audit'])}
tags: [forward-model, wall-fluid-coupling, test-section, dry-contract]
related:
  - .agent/status/2026-07-18_AGENT-541.md
  - .agent/journal/2026-07-18/tswfc2-dry-contract.md
  - imports/2026-07-18_tswfc2_dry_contract.json
task: {TASK}
date: {DATE}
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# TSWFC2 Distributed Wall/Fluid Dry Contract

Generated: `{summary['generated_at_utc']}`

## Decision

This package defines the dry contract for `TSWFC2`, a distributed test-section
wall/fluid node model. It does not implement Fluid behavior or launch a solver.

`TSWFC2` remains secondary while AGENT-540 owns the UMX1 Fluid API unblock. If
UMX1 is unavailable or fails cleanly, this contract is the next wall/test-section
path to review before any Fluid grid.

## Outputs

- `node_geometry_contract.csv`
- `node_heat_ledger_contract.csv`
- `runtime_input_audit_contract.csv`
- `score_gate_contract.csv`
- `distinction_from_tswfc1.csv`
- `next_step_handoff.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Node rows: `{summary['node_contract_rows']}`.
- Heat-ledger rows: `{summary['heat_ledger_rows']}`.
- Runtime-audit rows: `{summary['runtime_audit_rows']}`.
- Score-gate rows: `{summary['score_gate_rows']}`.
- TSWFC1 distinction rows: `{summary['distinction_rows']}`.
- Next-step rows: `{summary['next_step_rows']}`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, Fluid source,
generated index files, fitting, tuning, model selection, or scientific admission
state were changed. This package explicitly forbids duplicating AGENT-526's
single-node bulk-to-ambient series-resistance model unchanged.
""",
        encoding="utf-8",
    )


def build_package(out: Path = OUT) -> dict[str, Any]:
    require_sources()
    out.mkdir(parents=True, exist_ok=True)

    tp_tw_summary = read_json(SOURCES["tp_tw_summary"])
    source_property_summary = read_json(SOURCES["source_property_summary"])
    node_rows = build_node_contract()
    heat_rows = build_heat_ledger_contract()
    runtime_rows = build_runtime_audit()
    score_rows = build_score_gate_contract()
    distinction_rows = build_distinction_rows()
    next_rows = build_next_steps()
    manifest = build_source_manifest()

    if tp_tw_summary.get("secondary_model") != "TSWFC2_distributed_test_section_wall_fluid_nodes":
        raise ValueError("AGENT-536 no longer identifies TSWFC2 as the secondary model")
    if tp_tw_summary.get("admitted_candidate_families") != 0:
        raise ValueError("AGENT-536 candidate family admissions changed; refresh contract before reuse")
    if source_property_summary.get("scientific_admission_change") != "none":
        raise ValueError("AGENT-538 source/property summary unexpectedly changed admission state")

    summary = {
        "task": TASK,
        "date": DATE,
        "generated_at_utc": utc_now(),
        "output_dir": rel(out),
        "decision": "dry_contract_only_no_solver",
        "model_family": "TSWFC2_distributed_test_section_wall_fluid_nodes",
        "priority_status": "secondary_after_umx1_api_result",
        "blocker_addressed": "predictive-wall-test-section-submodels",
        "node_contract_rows": len(node_rows),
        "heat_ledger_rows": len(heat_rows),
        "runtime_audit_rows": len(runtime_rows),
        "score_gate_rows": len(score_rows),
        "distinction_rows": len(distinction_rows),
        "next_step_rows": len(next_rows),
        "tswfc1_duplicate_status": "blocked_do_not_duplicate",
        "salt1_role_rows_status": "required_or_block_before_grid",
        "source_property_label_policy": "required_before_scorecard_rows",
        "scientific_admission_change": "none",
        "native_output_mutation": "none",
        "registry_mutation": "none",
        "scheduler_action": "none",
        "solver_or_postprocessing_launch": "none",
        "external_fluid_edit": "none",
        "generated_index_refresh": "not_run_dry_contract_only",
    }

    write_csv(out / "node_geometry_contract.csv", node_rows, NODE_COLUMNS)
    write_csv(out / "node_heat_ledger_contract.csv", heat_rows, HEAT_COLUMNS)
    write_csv(out / "runtime_input_audit_contract.csv", runtime_rows, RUNTIME_COLUMNS)
    write_csv(out / "score_gate_contract.csv", score_rows, SCORE_COLUMNS)
    write_csv(out / "distinction_from_tswfc1.csv", distinction_rows, DISTINCTION_COLUMNS)
    write_csv(out / "next_step_handoff.csv", next_rows, NEXT_COLUMNS)
    write_csv(out / "source_manifest.csv", manifest, MANIFEST_COLUMNS)
    write_readme(out / "README.md", summary)
    write_json(out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.out), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
