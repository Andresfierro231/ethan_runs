#!/usr/bin/env python3
"""Build the CAND001 pressure terminal endpoint readiness gate package."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.common import csv_dump, ensure_dir, iso_timestamp, json_dump, relative_to_workspace

TASK_ID = "TODO-PRESSURE-CAND001-TERMINAL-ENDPOINT-READINESS-GATE-2026-07-22"
SLUG = "pressure_cand001_terminal_endpoint_readiness_gate"
OUT = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_cand001_terminal_endpoint_readiness_gate"
STATUS = ROOT / f".agent/status/2026-07-22_{TASK_ID}.md"
JOURNAL = ROOT / ".agent/journal/2026-07-22/pressure-cand001-terminal-endpoint-readiness-gate.md"
IMPORT = ROOT / "imports/2026-07-22_pressure_cand001_terminal_endpoint_readiness_gate.json"

ACTIVE_RETRY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery"
S10_GATE = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate"
ANCHOR_INVENTORY = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory"
FUTURE_ANCHOR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_future_low_reverse_anchor_design_refine"

SACCT_OBSERVED = [
    {
        "job_id_step": "3308712",
        "job_name": "salt4_heat2_pack",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:18:24",
        "time_limit": "5-00:00:00",
        "start": "2026-07-21T18:05:12",
        "end": "Unknown",
        "node": "c318-017",
    },
    {
        "job_id_step": "3308712.batch",
        "job_name": "batch",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:18:24",
        "time_limit": "",
        "start": "2026-07-21T18:05:12",
        "end": "Unknown",
        "node": "c318-017",
    },
    {
        "job_id_step": "3308712.0",
        "job_name": "foamRun",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:17:59",
        "time_limit": "",
        "start": "2026-07-21T18:05:37",
        "end": "Unknown",
        "node": "c318-017",
    },
    {
        "job_id_step": "3308712.1",
        "job_name": "foamRun",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:17:59",
        "time_limit": "",
        "start": "2026-07-21T18:05:37",
        "end": "Unknown",
        "node": "c318-017",
    },
    {
        "job_id_step": "3308712.2",
        "job_name": "foamRun",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:17:59",
        "time_limit": "",
        "start": "2026-07-21T18:05:37",
        "end": "Unknown",
        "node": "c318-017",
    },
    {
        "job_id_step": "3308712.3",
        "job_name": "foamRun",
        "state": "RUNNING",
        "exit_code": "0:0",
        "elapsed": "20:17:59",
        "time_limit": "",
        "start": "2026-07-21T18:05:37",
        "end": "Unknown",
        "node": "c318-017",
    },
]


def rel(path: Path) -> str:
    return relative_to_workspace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scheduler_rows(generated_at: str) -> list[dict[str, str]]:
    rows = [
        {
            "observed_at": "2026-07-22T14:24:28-05:00",
            "command": "sacct -j 3308712 --format=JobID,JobName%40,State,ExitCode,Elapsed,Timelimit,Start,End,NodeList%40 -P",
            "command_context": "sandbox_read_only",
            "return_code": "0",
            "evidence_type": "accounting_snapshot",
            "job_id_step": row["job_id_step"],
            "job_name": row["job_name"],
            "state": row["state"],
            "exit_code": row["exit_code"],
            "elapsed": row["elapsed"],
            "time_limit": row["time_limit"],
            "start": row["start"],
            "end": row["end"],
            "node": row["node"],
            "terminal": "false",
            "ready_effect": "blocks_endpoint_harvest",
        }
        for row in SACCT_OBSERVED
    ]
    rows.append(
        {
            "observed_at": "2026-07-22T14:24:28-05:00",
            "command": "squeue -j 3308712 -o '%i|%j|%T|%M|%l|%D|%R'",
            "command_context": "escalated_read_only_after_sandbox_socket_denial",
            "return_code": "0",
            "evidence_type": "live_queue_snapshot",
            "job_id_step": "3308712",
            "job_name": "salt4_heat2_pack",
            "state": "RUNNING",
            "exit_code": "",
            "elapsed": "20:19:05",
            "time_limit": "5-00:00:00",
            "start": "",
            "end": "",
            "node": "c318-017",
            "terminal": "false",
            "ready_effect": "blocks_endpoint_harvest",
        }
    )
    rows.append(
        {
            "observed_at": "2026-07-22T14:24:28-05:00",
            "command": "squeue -j 3308712 -o %i|%j|%T|%M|%l|%D|%R",
            "command_context": "sandbox_malformed_unquoted_format_then_socket_denial",
            "return_code": "130",
            "evidence_type": "discarded_command_failure",
            "job_id_step": "3308712",
            "job_name": "",
            "state": "not_used",
            "exit_code": "",
            "elapsed": "",
            "time_limit": "",
            "start": "",
            "end": "",
            "node": "",
            "terminal": "false",
            "ready_effect": "not_decision_basis",
        }
    )
    for row in rows:
        row["generated_at"] = generated_at
    return rows


def endpoint_gate_rows() -> list[dict[str, str]]:
    source_rows = read_csv(S10_GATE / "endpoint_field_requirement_table.csv")
    rows: list[dict[str, str]] = []
    for row in source_rows:
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "field_name": row["field_name"],
                "field_class": row["field_class"],
                "upstream_status": row["current_status"],
                "terminal_state_now": "RUNNING",
                "field_present_now": "not_checked_native_outputs_guarded",
                "readiness_now": "blocked_job_not_terminal",
                "required_before_use": row["required_before_use"],
                "admission_effect_now": row["admission_effect_now"],
            }
        )
    return rows


def ordinary_flow_uq_rows() -> list[dict[str, str]]:
    inventory = read_json(ANCHOR_INVENTORY / "summary.json")
    gate = read_json(S10_GATE / "summary.json")
    return [
        {
            "gate": "terminal_success",
            "basis": "scheduler/accounting terminal state",
            "status_now": "fail_blocked_running",
            "evidence": "job 3308712 parent and foamRun steps RUNNING",
            "required_to_pass": "COMPLETED 0:0 or explicit terminal failure classification",
        },
        {
            "gate": "endpoint_fields",
            "basis": "p,p_rgh,U,rho,T,face_area,face_normal and derived pressure fields",
            "status_now": f"fail_{gate['endpoint_fields_ready']}_ready_fields",
            "evidence": rel(S10_GATE / "endpoint_field_requirement_table.csv"),
            "required_to_pass": "terminal staged-copy sampler with finite endpoint fields",
        },
        {
            "gate": "ordinary_flow_RAF_RMF",
            "basis": "reverse area and reverse mass fractions at endpoint pair",
            "status_now": f"fail_{inventory['sampled_endpoint_ordinary_flow_pass_rows']}_sampled_endpoint_pass_rows",
            "evidence": rel(ANCHOR_INVENTORY / "sampled_endpoint_ordinary_flow_gate.csv"),
            "required_to_pass": "ordinary-flow pass on exact endpoint pair after terminal source recovery",
        },
        {
            "gate": "same_qoi_uq",
            "basis": "same-QOI temporal/mesh/neighbour evidence for endpoint pressure residual",
            "status_now": f"fail_{inventory['same_qoi_uq_ready_rows']}_ready_rows",
            "evidence": rel(ANCHOR_INVENTORY / "summary.json"),
            "required_to_pass": "same-QOI UQ on the same pressure residual being considered",
        },
        {
            "gate": "admission_guard",
            "basis": "no component K/F6 while terminal/source and UQ gates fail",
            "status_now": "pass_guardrail_no_admission",
            "evidence": rel(S10_GATE / "summary.json"),
            "required_to_pass": "separate admission row after all upstream gates pass",
        },
    ]


def next_queue_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "1",
            "next_task": "monitor_3308712_until_terminal",
            "trigger": "job remains RUNNING",
            "allowed_action": "read-only squeue/sacct/log-growth monitor under a narrow row",
            "forbidden_action": "duplicate submit, cancel, sampler, F6 score, component-K admission",
        },
        {
            "priority": "2",
            "next_task": "terminal_disposition_and_staged_copy_preflight",
            "trigger": "3308712 reaches COMPLETED or failed terminal state",
            "allowed_action": "classify terminal outcome, source paths, final times, endpoint field availability",
            "forbidden_action": "treat terminal success as pressure admission",
        },
        {
            "priority": "3",
            "next_task": "endpoint_sampler_manifest_after_terminal_success",
            "trigger": "terminal disposition shows finite fields likely present and source paths stable",
            "allowed_action": "claim sampler manifest only, with exact endpoint labels and RAF/RMF requirements",
            "forbidden_action": "harvest or score in the manifest row unless explicitly granted",
        },
        {
            "priority": "4",
            "next_task": "CAND002_or_future_anchor_fallback",
            "trigger": "3308712 times out/fails or remains non-ordinary after terminal sampling",
            "allowed_action": "use future low-reverse anchor design and inventory to choose a lower-risk source family",
            "forbidden_action": "silent retry of CAND001",
        },
    ]


def guardrail_rows() -> list[dict[str, str]]:
    return [
        {"guardrail": "native_output_mutation", "status": "false", "note": "no native CFD/OpenFOAM files written"},
        {"guardrail": "scheduler_mutation", "status": "false", "note": "read-only squeue/sacct only; no submit/cancel/requeue"},
        {"guardrail": "sampler_or_harvest_launch", "status": "false", "note": "job not terminal; endpoint fields not harvested"},
        {"guardrail": "component_k_or_f6_admission", "status": "false", "note": "all pressure model admission/scoring remains closed"},
        {"guardrail": "hidden_multiplier_or_clipped_k", "status": "false", "note": "no correction, fit, or pressure multiplier applied"},
        {"guardrail": "source_property_release", "status": "false", "note": "no source/property or pressure basis release"},
    ]


def source_manifest_rows() -> list[dict[str, str]]:
    return [
        {"role": "active_retry_summary", "path": rel(ACTIVE_RETRY / "summary.json"), "mode": "read_only"},
        {"role": "active_retry_scheduler_snapshot", "path": rel(ACTIVE_RETRY / "current_scheduler_snapshot.csv"), "mode": "read_only"},
        {"role": "s10_s14_endpoint_requirements", "path": rel(S10_GATE / "endpoint_field_requirement_table.csv"), "mode": "read_only"},
        {"role": "s10_s14_summary", "path": rel(S10_GATE / "summary.json"), "mode": "read_only"},
        {"role": "anchor_inventory_summary", "path": rel(ANCHOR_INVENTORY / "summary.json"), "mode": "read_only"},
        {"role": "future_anchor_dependency", "path": rel(FUTURE_ANCHOR / "cand001_dependency_state.csv"), "mode": "read_only"},
    ]


def write_readme(summary: dict[str, Any], out: Path = OUT) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_pressure_cand001_terminal_endpoint_readiness_gate.py
  task_id: {TASK_ID}
tags: [pressure, CAND001, terminal-readiness, scheduler-monitor, no-admission]
related:
  - {rel(ACTIVE_RETRY / "README.md")}
  - {rel(S10_GATE / "README.md")}
  - {rel(ANCHOR_INVENTORY / "README.md")}
---
# Pressure CAND001 Terminal Endpoint Readiness Gate

Decision: `{summary["decision"]}`.

Job `3308712` is still `RUNNING`, so CAND001 is not endpoint-ready. This
package records scheduler state, endpoint-field prerequisites, ordinary-flow
and same-QOI UQ blockers, and the next legal queue. It does not launch a
sampler or admit any pressure coefficient.

Key counts:

- scheduler terminal rows: `{summary["scheduler_terminal_rows"]}`
- endpoint ready fields: `{summary["endpoint_ready_fields"]}`
- ordinary-flow ready rows: `{summary["ordinary_flow_ready_rows"]}`
- same-QOI UQ ready rows: `{summary["same_qoi_uq_ready_rows"]}`
- F6/component-K admission rows: `0`
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def write_status(summary: dict[str, Any]) -> None:
    text = f"""---
provenance:
  generated_by: tools/analyze/build_pressure_cand001_terminal_endpoint_readiness_gate.py
  task_id: {TASK_ID}
tags: [status, pressure, CAND001, terminal-readiness]
related:
  - {rel(OUT / "README.md")}
  - {rel(OUT / "summary.json")}
---
# {TASK_ID}

## Objective

Objective: decide whether CAND001 job `3308712` is terminal/source ready for a
later pressure endpoint row.

Outcome: `{summary["decision"]}`. `sacct` and read-only escalated `squeue`
both showed job `3308712` still `RUNNING` on `c318-017`, with four `foamRun`
steps also running. Endpoint fields remain unharvested and not ready.

## Changes Made

Changed artifacts: `{rel(OUT)}`, `{rel(STATUS)}`, `{rel(JOURNAL)}`, and
`{rel(IMPORT)}`.

## Validation

Validation: builder, unit tests, py_compile, JSON parse, `finish_task.py`, and
scoped `git diff --check`.

## Guardrails

Guardrails: no native-output mutation, registry/admission mutation, scheduler
mutation, solver/postprocessing/sampler/harvest/UQ launch, F6 score,
component-K/cluster-K admission, clipped K, hidden multiplier, source/property
release, Fluid/external edit, or thesis-current edit.
"""
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(text, encoding="utf-8")


def write_journal(summary: dict[str, Any]) -> None:
    text = f"""---
task: {TASK_ID}
provenance:
  generated_by: tools/analyze/build_pressure_cand001_terminal_endpoint_readiness_gate.py
  task_id: {TASK_ID}
tags: [journal, pressure, CAND001, scheduler-monitor]
related:
  - {rel(OUT / "scheduler_terminal_snapshot.csv")}
  - {rel(OUT / "endpoint_readiness_gate.csv")}
---
# Pressure CAND001 Terminal Endpoint Readiness Gate

## Attempted

Claimed the board row, read the active CAND001 retry package, S10/S14 endpoint
requirements, low-recirc/nonrecirc inventory, and future anchor design. Checked
job `3308712` through Slurm accounting and live queue state.

## Observed

The successful `sacct` snapshot showed the parent job, batch step, and four
`foamRun` steps all `RUNNING`. The successful read-only `squeue` snapshot also
showed `RUNNING`. The earlier sandboxed `squeue` attempt was discarded because
the format string was malformed and then hit a Slurm socket denial.

## Inferred

CAND001 remains scientifically worth monitoring as terminal-source recovery,
but it is not endpoint-ready. The pressure gate remains fail-closed because the
job is not terminal, endpoint fields have not been staged or sampled, RAF/RMF
ordinary-flow status has not been recovered for the terminal case, and same-QOI
UQ is not ready.

## Next Useful Actions

Monitor `3308712` until terminal state. If it completes, claim a terminal
disposition/staged-copy preflight row before any sampler. If it times out or
fails, classify the failure and consider CAND002/future low-reverse anchor
fallback under a new row.
"""
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(text, encoding="utf-8")


def write_import(summary: dict[str, Any]) -> None:
    changed = [
        ".agent/BOARD.md",
        rel(STATUS),
        rel(JOURNAL),
        rel(IMPORT),
        "tools/analyze/build_pressure_cand001_terminal_endpoint_readiness_gate.py",
        "tools/analyze/test_pressure_cand001_terminal_endpoint_readiness_gate.py",
        f"{rel(OUT)}/README.md",
        f"{rel(OUT)}/scheduler_terminal_snapshot.csv",
        f"{rel(OUT)}/endpoint_readiness_gate.csv",
        f"{rel(OUT)}/ordinary_flow_uq_gate.csv",
        f"{rel(OUT)}/next_action_queue.csv",
        f"{rel(OUT)}/no_mutation_guardrails.csv",
        f"{rel(OUT)}/source_manifest.csv",
        f"{rel(OUT)}/summary.json",
    ]
    manifest = {
        "task": TASK_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "objective": "Read-only terminal endpoint readiness gate for pressure CAND001 job 3308712.",
        "changed_files": changed,
        "read_only_context": [row["path"] for row in source_manifest_rows()]
        + ["Slurm sacct/squeue read-only snapshots for job 3308712"],
        "results": {
            "decision": summary["decision"],
            "job_state": summary["active_job_state"],
            "endpoint_ready_fields": summary["endpoint_ready_fields"],
            "sampler_allowed_now": summary["sampler_allowed_now"],
            "admission_allowed_now": summary["admission_allowed_now"],
        },
        "mutation_flags": {
            "native_output_mutation": False,
            "registry_or_admission_mutation": False,
            "scheduler_mutation": False,
            "solver_sampler_harvest_uq_launched": False,
            "fluid_or_external_edit": False,
            "thesis_current_file_edit": False,
        },
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": False,
        "external_fluid_edit": False,
        "no_scorecard_outputs": True,
    }
    IMPORT.parent.mkdir(parents=True, exist_ok=True)
    json_dump(IMPORT, manifest)


def build(out: Path = OUT) -> dict[str, Any]:
    ensure_dir(out)
    generated_at = iso_timestamp()
    active_summary = read_json(ACTIVE_RETRY / "summary.json")
    s10_summary = read_json(S10_GATE / "summary.json")
    inventory_summary = read_json(ANCHOR_INVENTORY / "summary.json")

    sched = scheduler_rows(generated_at)
    endpoints = endpoint_gate_rows()
    ordinary = ordinary_flow_uq_rows()
    next_queue = next_queue_rows()
    guards = guardrail_rows()
    sources = source_manifest_rows()

    endpoint_ready_fields = sum(1 for row in endpoints if row["readiness_now"] == "ready")
    terminal_rows = sum(1 for row in sched if row["terminal"] == "true")
    ordinary_ready = int(inventory_summary["sampled_endpoint_ordinary_flow_pass_rows"])
    same_qoi_ready = int(inventory_summary["same_qoi_uq_ready_rows"])
    sampler_allowed = False
    admission_allowed = False

    summary = {
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": "cand001_endpoint_readiness_blocked_job_running_no_sampler_no_admission",
        "candidate_id": "CAND-001",
        "active_job_id": active_summary["active_retry_job_id"],
        "active_job_state": "RUNNING",
        "active_job_node": "c318-017",
        "active_job_terminal": False,
        "scheduler_snapshot_rows": len(sched),
        "scheduler_terminal_rows": terminal_rows,
        "endpoint_requirement_rows": len(endpoints),
        "endpoint_ready_fields": endpoint_ready_fields,
        "ordinary_flow_ready_rows": ordinary_ready,
        "same_qoi_uq_ready_rows": same_qoi_ready,
        "source_property_release_ready_rows": 0,
        "sampler_allowed_now": sampler_allowed,
        "harvest_allowed_now": False,
        "admission_allowed_now": admission_allowed,
        "f6_scoring_allowed_now": False,
        "component_k_admitted": False,
        "cluster_k_admitted": False,
        "clipped_k": False,
        "hidden_global_multiplier": False,
        "new_scheduler_submission": False,
        "scheduler_mutation": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "solver_sampler_harvest_uq_launched": False,
        "fluid_or_external_repo_edited": False,
        "thesis_current_file_edit": False,
        "s10_prior_endpoint_fields_ready": s10_summary["endpoint_fields_ready"],
        "s10_prior_terminal_success_cases": s10_summary["terminal_success_cases"],
        "worth_monitoring_existing_job": True,
    }

    csv_dump(out / "scheduler_terminal_snapshot.csv", list(sched[0]), sched)
    csv_dump(out / "endpoint_readiness_gate.csv", list(endpoints[0]), endpoints)
    csv_dump(out / "ordinary_flow_uq_gate.csv", list(ordinary[0]), ordinary)
    csv_dump(out / "next_action_queue.csv", list(next_queue[0]), next_queue)
    csv_dump(out / "no_mutation_guardrails.csv", list(guards[0]), guards)
    csv_dump(out / "source_manifest.csv", list(sources[0]), sources)
    json_dump(out / "summary.json", summary)
    write_readme(summary, out)
    if out == OUT:
        write_status(summary)
        write_journal(summary)
        write_import(summary)
    return summary


def main() -> int:
    print(json.dumps(build(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
