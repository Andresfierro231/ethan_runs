#!/usr/bin/env python3
"""Build a scientific-closure and forward-v1 execution dashboard."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_scientific_closure_forward_v1_execution_dashboard"

FINAL_FORWARD_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/summary.json"
FINAL_FORWARD_GATES = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/forward_v1_gate_checklist.csv"
FINAL_FORWARD_WAITLIST = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/scorecard_inputs_waiting_on_agents.csv"
INTERNAL_NU_BLOCKERS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/internal_nu_dependency_blockers.csv"
CFD_TRIAGE_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/summary.json"
CFD_TRIAGE_TABLE = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/steady_candidate_admission_triage.csv"
UPCOMER_COMPUTE_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_upcomer_matched_plane_compute_extraction/summary.json"
UPCOMER_COMPUTE_STATUS = ROOT / ".agent/status/2026-07-14_AGENT-344.md"
HYDRAULIC_F6 = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_hydraulic_reset_k_admission_contract/f6_readiness_handoff.csv"
BOUNDARY_GUARDRAIL_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/summary.json"
INTERNAL_NU_PROGRESS = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_internal_nu_blocker_progress_integration/next_workstream_actions.csv"
SALT_INVENTORY_SUMMARY = ROOT / "work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/summary.json"


WORKSTREAM_COLUMNS = [
    "priority",
    "workstream_id",
    "owner_lane",
    "current_state",
    "admitted_now",
    "pending_or_blocked",
    "next_action",
    "next_artifact",
    "thesis_table_value",
    "source_artifact",
]
REQUIREMENT_COLUMNS = [
    "requirement_id",
    "required_before",
    "current_status",
    "pass_condition",
    "forbidden_shortcut",
    "consumer",
    "source_artifact",
]
EVIDENCE_COLUMNS = [
    "claim_id",
    "claim",
    "evidence_status",
    "thesis_use",
    "limits",
    "source_artifact",
]
QUEUE_COLUMNS = [
    "queue_id",
    "trigger",
    "required_inputs",
    "output_to_refresh",
    "scorecard_effect",
    "do_not_claim",
]
MANIFEST_COLUMNS = ["artifact", "role", "path"]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def status_contains(path: Path, needle: str) -> bool:
    return needle.lower() in path.read_text(encoding="utf-8").lower()


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if not rows:
        return {}
    return rows[0]


def build_workstreams() -> list[dict[str, Any]]:
    forward = read_json(FINAL_FORWARD_SUMMARY)
    cfd = read_json(CFD_TRIAGE_SUMMARY)
    upcomer = read_json(UPCOMER_COMPUTE_SUMMARY)
    f6 = first_row(HYDRAULIC_F6)
    boundary = read_json(BOUNDARY_GUARDRAIL_SUMMARY)
    salt_inventory = read_json(SALT_INVENTORY_SUMMARY)
    matched_plane_state = "submitted_pending" if status_contains(UPCOMER_COMPUTE_STATUS, "submitted/pending") else upcomer.get("status", "unknown")
    return [
        {
            "priority": "P1",
            "workstream_id": "terminal_cfd_admission",
            "owner_lane": "cfd-pp",
            "current_state": f"triage_complete_training_expansion_rows={cfd.get('immediate_training_expansion_rows')}; corrected_q_rows_admitted={forward.get('corrected_q_rows_admitted')}",
            "admitted_now": "current Salt2 train / Salt3 validation / Salt4 holdout only",
            "pending_or_blocked": "corrected-Q rows still need terminal admission before training/onset/hydraulic use",
            "next_action": "Monitor harvest/continuation outputs, then build terminal admission refresh with BC labels and split eligibility.",
            "next_artifact": "corrected_q_terminal_admission_refresh.csv",
            "thesis_table_value": "Separates steady detector evidence from admission and split discipline.",
            "source_artifact": rel(CFD_TRIAGE_SUMMARY),
        },
        {
            "priority": "P2",
            "workstream_id": "upcomer_matched_plane_extraction",
            "owner_lane": "therm-reconstr",
            "current_state": f"{matched_plane_state}; candidate_rows={upcomer.get('candidate_rows')}; runnable_now_rows={upcomer.get('runnable_now_rows')}",
            "admitted_now": "existing upcomer rows remain diagnostic/validation-only",
            "pending_or_blocked": "admission-grade matched vector/thermal plane metrics pending compute job output",
            "next_action": "Harvest parsed AGENT-344 outputs after job 3295492 completes; dependency-gated corrected-Q rows wait on terminal admission.",
            "next_artifact": "upcomer_matched_plane_metrics.csv",
            "thesis_table_value": "Turns recirculation claim into measurable plane-by-plane physics evidence.",
            "source_artifact": rel(UPCOMER_COMPUTE_SUMMARY),
        },
        {
            "priority": "P3",
            "workstream_id": "internal_nu_reopen_gate",
            "owner_lane": "internal-Nu",
            "current_state": f"fit_consumable={forward.get('fitted_internal_nu_rows_consumable')}; dependency_blockers={forward.get('internal_nu_dependency_blocker_count')}",
            "admitted_now": "Nu_section_effective_upcomer_diagnostic as diagnostic/validation-only",
            "pending_or_blocked": "needs at least three fit-admissible single-stream rows including ordinary-pipe and transition/higher-Re anchors",
            "next_action": "Rebuild Nu admission only after matched-plane metrics and admitted onset candidates land.",
            "next_artifact": "upcomer_nu_admission_refresh.csv",
            "thesis_table_value": "Documents why recirculation is an admission rule, not a failed correlation.",
            "source_artifact": rel(INTERNAL_NU_BLOCKERS),
        },
        {
            "priority": "P4",
            "workstream_id": "f6_hydraulic_screen",
            "owner_lane": "hydraulics",
            "current_state": f"ready_for_bounded_test={f6.get('ready_for_bounded_test')}; current_status={f6.get('current_status')}",
            "admitted_now": "H1 and localized fixed-K remain diagnostic/proxy only",
            "pending_or_blocked": f6.get("blocking_gap", "terminal/admitted Re-variation evidence is absent"),
            "next_action": f6.get("next_action", "Run F6 only after terminal/admitted Re-variation rows exist."),
            "next_artifact": "f6_phi_re_hydraulic_scorecard.csv",
            "thesis_table_value": "Keeps pressure-loss closure separate from thermal tuning.",
            "source_artifact": rel(HYDRAULIC_F6),
        },
        {
            "priority": "P5",
            "workstream_id": "setup_only_boundary_api",
            "owner_lane": "BC-modeling / Fluid",
            "current_state": f"residual_guardrail_rows={boundary.get('residual_guardrail_rows')}; boundary_field_rows={boundary.get('boundary_field_rows')}",
            "admitted_now": "boundary residual ownership and field contract, not Fluid implementation",
            "pending_or_blocked": "Fluid still lacks first-class external boundary/HX dictionaries for setup-only predictive mode",
            "next_action": "Claim external Fluid paths and implement h/Ta/Tsur/emissivity/layer/drive-temperature dictionaries with runtime leakage tests.",
            "next_artifact": "setup_only_boundary_hx_outputs.csv",
            "thesis_table_value": "Separates heater, cooler/HX, wall, radiation metadata, storage, and mixing residual ownership.",
            "source_artifact": rel(BOUNDARY_GUARDRAIL_SUMMARY),
        },
        {
            "priority": "P6",
            "workstream_id": "forward_v1_scorecard_refresh",
            "owner_lane": "forward-pred",
            "current_state": f"{forward.get('final_forward_v1_status')}; blocking_gates={forward.get('blocking_gate_count')}; waiting_inputs={forward.get('waiting_input_count')}",
            "admitted_now": "strict input/split hygiene plus diagnostic/proxy evidence only",
            "pending_or_blocked": "wait for terminal CFD admission, F6/hydraulic result, setup-only boundary outputs, and Nu admission/no-fit refresh",
            "next_action": "Refresh only after at least one upstream gate lands; preserve Salt2/Salt3/Salt4 split unless dated split gate supersedes it.",
            "next_artifact": "forward_v1_residual_attribution_scorecard.csv",
            "thesis_table_value": "Provides one dashboard for train/validation/holdout residual attribution.",
            "source_artifact": rel(FINAL_FORWARD_SUMMARY),
        },
        {
            "priority": "P7",
            "workstream_id": "candidate_inventory",
            "owner_lane": "cfd-pp / coordination",
            "current_state": (
                f"candidate_rows={salt_inventory.get('candidate_rows')}; "
                f"corrected_q_rows={salt_inventory.get('corrected_q_rows')}; "
                f"admitted_corrected_q_rows={salt_inventory.get('corrected_q_rows_admitted_now')}"
            ),
            "admitted_now": "current Salt2/Salt3/Salt4 candidate split only",
            "pending_or_blocked": "new rows need explicit admission and split eligibility",
            "next_action": "Use admitted inventory to feed cfd, hydraulic, and Nu/onset consumers.",
            "next_artifact": "admitted_forward_candidate_inventory.csv",
            "thesis_table_value": "Stable source-of-truth table for which CFD cases can support each claim.",
            "source_artifact": rel(SALT_INVENTORY_SUMMARY),
        },
    ]


def build_requirements() -> list[dict[str, Any]]:
    gates = {row["gate_id"]: row for row in read_csv(FINAL_FORWARD_GATES)}
    return [
        {
            "requirement_id": "terminal_cfd_admission",
            "required_before": "training expansion, F6, upcomer onset, final scorecard refresh",
            "current_status": gates["cfd_pp_admitted_training_data"]["gate_status"],
            "pass_condition": "Rows are terminal, admitted, source-labeled, BC-labeled, and split-assigned or diagnostic-only.",
            "forbidden_shortcut": "Do not admit rows from live scheduler state or steady detector label alone.",
            "consumer": "forward-pred; hydraulics; internal-Nu",
            "source_artifact": rel(FINAL_FORWARD_GATES),
        },
        {
            "requirement_id": "matched_plane_metrics",
            "required_before": "internal-Nu fit reopen and upcomer onset calibration",
            "current_status": "submitted_pending",
            "pass_condition": "Matched inlet/mid/outlet vector and thermal plane metrics with exact time windows and face-area/wall-band sampling.",
            "forbidden_shortcut": "Do not use existing proxy rows as admission-grade Nu data.",
            "consumer": "internal-Nu; thesis recirculation story",
            "source_artifact": rel(UPCOMER_COMPUTE_STATUS),
        },
        {
            "requirement_id": "f6_re_variation",
            "required_before": "hydraulic closure upgrade",
            "current_status": first_row(HYDRAULIC_F6).get("current_status"),
            "pass_condition": "Admitted Re-variation rows permit bounded F6 pressure-loss scoring with mdot guardrail.",
            "forbidden_shortcut": "Do not tune thermal terms to hide hydraulic mdot bias.",
            "consumer": "hydraulics; forward-v1",
            "source_artifact": rel(HYDRAULIC_F6),
        },
        {
            "requirement_id": "setup_only_boundary_outputs",
            "required_before": "predictive thermal score without imposed cooler duty",
            "current_status": gates["boundary_hx_wall_radiation"]["gate_status"],
            "pass_condition": "Fluid/API outputs setup-only heater/cooler/wall/radiation lanes without realized CFD heat runtime inputs.",
            "forbidden_shortcut": "Do not call imposed cooler duty or realized wallHeatFlux replay predictive closure evidence.",
            "consumer": "forward-v1; boundary-modeling",
            "source_artifact": rel(FINAL_FORWARD_GATES),
        },
        {
            "requirement_id": "internal_nu_reopen",
            "required_before": "any fitted internal-Nu consumption",
            "current_status": gates["thermal_internal_nu"]["gate_status"],
            "pass_condition": "Later dated gate admits fit rows after recirculation, matched-plane, mesh/time, and residual ownership gates pass.",
            "forbidden_shortcut": "Do not consume Nu_section_effective_upcomer_diagnostic as trainable closure data.",
            "consumer": "internal-Nu; forward-v1",
            "source_artifact": rel(INTERNAL_NU_BLOCKERS),
        },
    ]


def build_evidence_register() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "split_discipline_locked",
            "claim": "Current predictive split is Salt2 train, Salt3 validation, Salt4 holdout.",
            "evidence_status": "admitted_now",
            "thesis_use": "Use as the current train/validation/holdout discipline for all forward-v1 tables.",
            "limits": "Can change only through a later dated split gate.",
            "source_artifact": rel(FINAL_FORWARD_GATES),
        },
        {
            "claim_id": "forward_v1_blocked",
            "claim": "Final forward-v1 is not admitted.",
            "evidence_status": "blocked_no_go",
            "thesis_use": "Use to explain rigor: scorecard structure exists but final claim waits on gates.",
            "limits": "Do not call precursor/proxy rows final closure evidence.",
            "source_artifact": rel(FINAL_FORWARD_SUMMARY),
        },
        {
            "claim_id": "upcomer_recirculation_nu_policy",
            "claim": "Current upcomer Nu evidence is section-effective diagnostic evidence only.",
            "evidence_status": "diagnostic_validation_only",
            "thesis_use": "Use as a scientific admission rule for recirculating upcomer flow.",
            "limits": "Not trainable internal-Nu closure data.",
            "source_artifact": rel(INTERNAL_NU_BLOCKERS),
        },
        {
            "claim_id": "cfd_steady_not_training",
            "claim": "Steady detector rows are not automatically training-admitted.",
            "evidence_status": "guardrail",
            "thesis_use": "Use to distinguish numerical steadiness from admission and split eligibility.",
            "limits": "Terminal/BC/split gates still control use.",
            "source_artifact": rel(CFD_TRIAGE_TABLE),
        },
        {
            "claim_id": "f6_waits_on_re_variation",
            "claim": "F6 is the next bounded hydraulic candidate but is not launchable yet.",
            "evidence_status": "pending_admitted_re_variation",
            "thesis_use": "Use to explain hydraulic path without thermal compensation.",
            "limits": "No global multiplier or thermal fitting.",
            "source_artifact": rel(HYDRAULIC_F6),
        },
        {
            "claim_id": "boundary_residual_ownership",
            "claim": "Heater, cooler/HX, wall, radiation metadata, storage, and mixing residuals have distinct owners.",
            "evidence_status": "contract_ready",
            "thesis_use": "Use to prevent internal Nu from absorbing boundary residuals.",
            "limits": "Fluid first-class setup-only boundary API still pending.",
            "source_artifact": rel(BOUNDARY_GUARDRAIL_SUMMARY),
        },
    ]


def build_refresh_queue() -> list[dict[str, Any]]:
    return [
        {
            "queue_id": "Q1_terminal_cfd",
            "trigger": "corrected-Q harvest/admission package lands",
            "required_inputs": "terminal status, steady/admission verdict, BC labels, split eligibility",
            "output_to_refresh": "corrected_q_terminal_admission_refresh.csv; admitted_forward_candidate_inventory.csv; forward_v1_gate_checklist.csv",
            "scorecard_effect": "May add rows to training/validation/holdout candidate inventory or keep them diagnostic.",
            "do_not_claim": "Do not expand training from named steady rows alone.",
        },
        {
            "queue_id": "Q2_matched_planes",
            "trigger": "AGENT-344 parsed matched-plane outputs land",
            "required_inputs": "reverse fractions, secondary velocity, bulk/wall T, wallHeatFlux, Re/Pr/Ri/Ra/Gr/Gz, time windows",
            "output_to_refresh": "upcomer_nu_admission_refresh.csv; internal_nu_dependency_blockers.csv",
            "scorecard_effect": "May convert upcomer rows from proxy diagnostic to admission-grade diagnostic or fit-rejected evidence.",
            "do_not_claim": "Do not fit Nu until admission criteria pass.",
        },
        {
            "queue_id": "Q3_f6_hydraulics",
            "trigger": "admitted Re-variation pressure rows exist",
            "required_inputs": "admitted corrected-Q/targeted-Re pressure-loss rows and split policy",
            "output_to_refresh": "f6_phi_re_hydraulic_scorecard.csv",
            "scorecard_effect": "May replace H1 proxy with bounded hydraulic residual attribution.",
            "do_not_claim": "Do not tune thermal closure to repair mdot.",
        },
        {
            "queue_id": "Q4_boundary_api",
            "trigger": "Fluid setup-only boundary dictionaries implemented and tested",
            "required_inputs": "h/Ta/Tsur/emissivity/layers/drive selectors, HX/cooler outputs, runtime-input audit",
            "output_to_refresh": "setup_only_boundary_hx_outputs.csv",
            "scorecard_effect": "May replace imposed cooler duty proxy with setup-only thermal boundary evidence.",
            "do_not_claim": "Do not use realized CFD wallHeatFlux as runtime input.",
        },
        {
            "queue_id": "Q5_forward_v1",
            "trigger": "one or more upstream gate-moving artifacts land",
            "required_inputs": "result-intake-compatible cfd, hydraulic, boundary, thermal, and sensor rows",
            "output_to_refresh": "forward_v1_residual_attribution_scorecard.csv",
            "scorecard_effect": "Separates hydraulic, boundary/HX, wall/radiation, internal-Nu diagnostic, and sensor residuals.",
            "do_not_claim": "Do not call final forward-v1 admitted while blocking gates remain.",
        },
    ]


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    readme = f"""---
provenance:
  - {rel(FINAL_FORWARD_SUMMARY)}
  - {rel(CFD_TRIAGE_SUMMARY)}
  - {rel(UPCOMER_COMPUTE_SUMMARY)}
  - {rel(HYDRAULIC_F6)}
tags: [scientific-closure, forward-model, forward-v1, thesis-table, dashboard]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-348
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Scientific Closure / Forward-v1 Execution Dashboard

## Decision

This package implements the first safe slice of the plan: it does not reopen
admission or mutate solver outputs. It consolidates landed evidence into
thesis-useful tables and names the exact gate-moving artifacts needed before
final forward-v1 can be rerun.

Current forward-v1 decision remains
`{summary['final_forward_v1_status']}` with `{summary['blocking_gate_count']}`
blocking gates.

## What Is Admitted Now

- Strict predictive input hygiene and the current split:
  `salt_2=train`, `salt_3=validation`, `salt_4=holdout`.
- H1/localized fixed-K evidence as diagnostic/proxy only.
- `Nu_section_effective_upcomer_diagnostic` as diagnostic/validation-only.
- Boundary residual ownership guardrails and extraction contracts.

## What Is Pending

- Terminal corrected-Q admission before training expansion, F6, or onset use.
- AGENT-344 matched-plane compute results before internal-Nu admission refresh.
- Admitted Re-variation rows before F6 scoring.
- First-class Fluid setup-only boundary dictionaries before predictive thermal
  boundary/HX scoring.

## Math / Theory Guardrails

Forward-v1 must predict from setup inputs. Realized CFD mdot, realized CFD
wallHeatFlux, imposed cooler duty, validation temperatures, and diagnostic
upcomer Nu are targets or diagnostics, not runtime inputs. Internal Nu cannot
absorb heater, cooler/HX, wall/radiation, storage, branch mixing, recirculation,
or hydraulic residuals.

## Files

- `workstream_execution_dashboard.csv`
- `gate_landing_requirements.csv`
- `thesis_evidence_register.csv`
- `forward_v1_refresh_queue.csv`
- `source_manifest.csv`
- `summary.json`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def build_package(output_dir: Path = OUT) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    forward = read_json(FINAL_FORWARD_SUMMARY)
    workstreams = build_workstreams()
    requirements = build_requirements()
    evidence = build_evidence_register()
    queue = build_refresh_queue()
    write_csv(output_dir / "workstream_execution_dashboard.csv", workstreams, WORKSTREAM_COLUMNS)
    write_csv(output_dir / "gate_landing_requirements.csv", requirements, REQUIREMENT_COLUMNS)
    write_csv(output_dir / "thesis_evidence_register.csv", evidence, EVIDENCE_COLUMNS)
    write_csv(output_dir / "forward_v1_refresh_queue.csv", queue, QUEUE_COLUMNS)
    write_csv(
        output_dir / "source_manifest.csv",
        [
            {"artifact": "final_forward_v1_summary", "role": "source", "path": rel(FINAL_FORWARD_SUMMARY)},
            {"artifact": "final_forward_v1_gates", "role": "source", "path": rel(FINAL_FORWARD_GATES)},
            {"artifact": "final_forward_v1_waitlist", "role": "source", "path": rel(FINAL_FORWARD_WAITLIST)},
            {"artifact": "internal_nu_dependency_blockers", "role": "source", "path": rel(INTERNAL_NU_BLOCKERS)},
            {"artifact": "cfd_triage_summary", "role": "source", "path": rel(CFD_TRIAGE_SUMMARY)},
            {"artifact": "upcomer_compute_status", "role": "source", "path": rel(UPCOMER_COMPUTE_STATUS)},
            {"artifact": "hydraulic_f6_handoff", "role": "source", "path": rel(HYDRAULIC_F6)},
            {"artifact": "boundary_guardrail_summary", "role": "source", "path": rel(BOUNDARY_GUARDRAIL_SUMMARY)},
            {"artifact": "workstream_execution_dashboard", "role": "generated", "path": rel(output_dir / "workstream_execution_dashboard.csv")},
            {"artifact": "gate_landing_requirements", "role": "generated", "path": rel(output_dir / "gate_landing_requirements.csv")},
            {"artifact": "thesis_evidence_register", "role": "generated", "path": rel(output_dir / "thesis_evidence_register.csv")},
            {"artifact": "forward_v1_refresh_queue", "role": "generated", "path": rel(output_dir / "forward_v1_refresh_queue.csv")},
        ],
        MANIFEST_COLUMNS,
    )
    summary = {
        "task": "AGENT-348",
        "generated_at_utc": utc_now(),
        "final_forward_v1_status": forward["final_forward_v1_status"],
        "blocking_gate_count": forward["blocking_gate_count"],
        "workstream_count": len(workstreams),
        "gate_requirement_count": len(requirements),
        "thesis_evidence_row_count": len(evidence),
        "refresh_queue_count": len(queue),
        "corrected_q_rows_admitted": forward["corrected_q_rows_admitted"],
        "fitted_internal_nu_rows_consumable": forward["fitted_internal_nu_rows_consumable"],
        "native_solver_outputs_mutated": False,
        "external_fluid_modified": False,
        "generated_indexes_touched": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_dir, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(build_package(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
