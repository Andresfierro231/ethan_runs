#!/usr/bin/env python3.11
"""Document the active CAND001 terminal-source recovery retry.

This builder is intentionally read-only with respect to CFD outputs and the
scheduler. It records whether the existing Salt4 high-heat relaunch job is worth
continuing as terminal source recovery evidence, while preserving the no-F6
scoring guardrail from the prior S10/S14 gate.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "TODO-PRESSURE-F6-CAND001-ACTIVE-RETRY-TERMINAL-RECOVERY-2026-07-22"
SLUG = "pressure_f6_cand001_active_retry_terminal_recovery"
ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_pressure_f6_cand001_active_retry_terminal_recovery"

GATE_DIR = ROOT / "work_products/2026-07/2026-07-22/2026-07-22_s10_s14_pressure_f6_cand001_retry_and_uq_gate"
TIMEOUT_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition"
READINESS_DIR = ROOT / "work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_low_recirc_source_readiness"
RELAUNCH_MANIFEST = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv"
RELAUNCH_README = ROOT / "jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/README.md"
RELAUNCH_STATUS = ROOT / ".agent/status/2026-07-21_TODO-HIGH-HEAT-SALT4-STEADY-RELAUNCH-2026-07-21.md"

ACTIVE_JOB_ID = "3308712"
PRIOR_TIMEOUT_JOBS = ("3299610", "3299620")
ENDPOINT_LABELS = "lower_leg__s04;right_leg__s00"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        seen: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.append(key)
        fieldnames = seen
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_command(args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)
    except Exception as exc:  # pragma: no cover - defensive for scheduler outages
        return 999, "", f"{type(exc).__name__}: {exc}"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def parse_sacct(stdout: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in stdout.splitlines():
        if not line or line.startswith("JobID|"):
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        rows.append(
            {
                "job_id_step": parts[0],
                "job_name": parts[1],
                "state": parts[2],
                "exit_code": parts[3],
                "elapsed": parts[4],
                "node": parts[5],
            }
        )
    return rows


def current_scheduler_snapshot(generated_at: str) -> tuple[list[dict[str, object]], bool, str]:
    rows: list[dict[str, object]] = []
    active_running = False
    active_state = "unknown"
    for job_id in (ACTIVE_JOB_ID, *PRIOR_TIMEOUT_JOBS):
        sq_code, sq_out, sq_err = run_command(["squeue", "-j", job_id])
        sacct_code, sacct_out, sacct_err = run_command(
            ["sacct", "-j", job_id, "--format=JobID,JobName%30,State,ExitCode,Elapsed,NodeList%30", "-P"]
        )
        sacct_rows = parse_sacct(sacct_out)
        parent = next((row for row in sacct_rows if row["job_id_step"] == job_id), sacct_rows[0] if sacct_rows else {})
        state = parent.get("state", "not_returned")
        if job_id == ACTIVE_JOB_ID:
            active_state = state
            active_running = state == "RUNNING" or (" R " in f" {sq_out} ")
        rows.append(
            {
                "generated_at_utc": generated_at,
                "job_id": job_id,
                "role": "active_cand001_retry" if job_id == ACTIVE_JOB_ID else "prior_timeout_context",
                "squeue_return_code": sq_code,
                "squeue_state_hint": "running_or_queued" if sq_out and "JOBID" in sq_out and job_id in sq_out else "not_visible_in_squeue",
                "sacct_return_code": sacct_code,
                "sacct_parent_state": state,
                "sacct_parent_elapsed": parent.get("elapsed", ""),
                "sacct_parent_node": parent.get("node", ""),
                "squeue_stderr": sq_err,
                "sacct_stderr": sacct_err,
                "read_only_scheduler_snapshot": True,
            }
        )
        for step in sacct_rows:
            rows.append(
                {
                    "generated_at_utc": generated_at,
                    "job_id": job_id,
                    "role": "sacct_step",
                    "squeue_return_code": sq_code,
                    "squeue_state_hint": "",
                    "sacct_return_code": sacct_code,
                    "sacct_parent_state": step["state"],
                    "sacct_parent_elapsed": step["elapsed"],
                    "sacct_parent_node": step["node"],
                    "squeue_stderr": "",
                    "sacct_stderr": "",
                    "read_only_scheduler_snapshot": True,
                    "job_id_step": step["job_id_step"],
                    "job_name": step["job_name"],
                }
            )
    return rows, active_running, active_state


def build_source_contract(manifest_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for src in manifest_rows:
        rows.append(
            {
                "candidate_id": "CAND-001",
                "active_retry_job_id": ACTIVE_JOB_ID,
                "case_key": src["case_key"],
                "display_name": src["display_name"],
                "salt": src["salt"],
                "target_heater_power_W": src["target_heater_power_W"],
                "relaunch_restart_time_s": src["relaunch_restart_time_s"],
                "target_end_time_s": src["target_end_time_s"],
                "walltime": src["walltime"],
                "case_dir": src["case_dir"],
                "source_processors64": src["source_processors64"],
                "endpoint_labels": ENDPOINT_LABELS,
                "terminal_evidence_needed": "solver_terminal_success;post_terminal_steady_state_review;endpoint_fields_present_before_sampler",
                "allowed_use": "terminal_source_recovery_only_not_F6_scoring",
                "scientific_caveat": src["scientific_caveat"],
            }
        )
    return rows


def build_outputs() -> dict[str, object]:
    generated_at = now_utc()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gate_summary = json.loads((GATE_DIR / "summary.json").read_text(encoding="utf-8"))
    manifest_rows = read_csv(RELAUNCH_MANIFEST)
    timeout_rows = read_csv(TIMEOUT_DIR / "scheduler_disposition.csv")
    readiness_rows = [row for row in read_csv(READINESS_DIR / "source_case_readiness_refresh.csv") if row.get("candidate_id") == "CAND-001"]
    scheduler_rows, active_running, active_state = current_scheduler_snapshot(generated_at)

    source_contract_rows = build_source_contract(manifest_rows)
    write_csv(OUT_DIR / "current_scheduler_snapshot.csv", scheduler_rows)
    write_csv(OUT_DIR / "active_retry_source_contract.csv", source_contract_rows)

    worth_rows = [
        {
            "candidate_id": "CAND-001",
            "decision": "worth_continuing_existing_3308712_monitor_only_no_duplicate_submit",
            "scientifically_worth_continuing": True,
            "active_retry_job_id": ACTIVE_JOB_ID,
            "active_retry_state_at_snapshot": active_state,
            "why_worth_trying": (
                "Prior CAND001 failure was scheduler timeout, not a physics rejection. "
                "The existing Salt4 high-heat/no-recirculation relaunch contains four source cases "
                "from explicit restart times and can still supply the missing terminal-source evidence "
                "needed before any pressure endpoint harvest is considered."
            ),
            "what_worked": "Runbook/gate separated terminal recovery from F6 scoring; high-heat relaunch job is already active with four CAND001 source cases.",
            "what_did_not_work": "Earlier jobs 3299610 and 3299620 timed out before terminal success; no endpoint fields or ordinary-flow evidence were recovered.",
            "risk_and_cost": "Continue monitoring the active job; do not spend additional queue time on a duplicate submission. If it times out again, review CAND002 or a lower-recirculation source family before retrying.",
            "scientific_payoff_if_success": "Terminal, steady, low-recirculation source evidence could unlock a later endpoint-field readiness row; it would not by itself admit F6.",
            "stop_condition": "If terminal recovery fails again or post-terminal RAF/RMF/SVF remains non-ordinary, close CAND001 as diagnostic/blocked and consider CAND002 fallback under a new row.",
        }
    ]
    write_csv(OUT_DIR / "worth_trying_decision.csv", worth_rows)

    duplicate_rows = [
        {
            "candidate_id": "CAND-001",
            "active_retry_job_id": ACTIVE_JOB_ID,
            "active_retry_seen_running_at_snapshot": active_running,
            "active_retry_state_at_snapshot": active_state,
            "new_submit_allowed": False,
            "cancel_or_requeue_allowed": False,
            "monitor_allowed": True,
            "reason": "A separate relaunch job already exists for the four CAND001 source cases; duplicate submission would confuse provenance and spend compute without adding independent evidence.",
            "required_before_any_future_submit": "terminal_accounting_of_3308712;failure_mode_classification;new_board_row;explicit_nonduplicate_case_scope",
        }
    ]
    write_csv(OUT_DIR / "duplicate_launch_guard.csv", duplicate_rows)

    terminal_rows = [
        {
            "event": "3308712_success_and_cases_terminal",
            "next_allowed_row": "terminal_disposition_and_steady_state_readiness",
            "allowed_action": "read solver logs, confirm terminal times, evaluate steady-state drift and endpoint field presence",
            "forbidden_action": "F6 scoring, component-K admission, sampler launch without a new exact scope",
        },
        {
            "event": "3308712_timeout_or_failed",
            "next_allowed_row": "timeout_disposition_or_CAND002_fallback_gate",
            "allowed_action": "classify timeout/failure and decide no-retry, adjusted retry, or CAND002 fallback",
            "forbidden_action": "silent resubmit or treating partial fields as terminal evidence",
        },
        {
            "event": "terminal_but_not_steady",
            "next_allowed_row": "steady_state_extension_gate",
            "allowed_action": "document drift, decide whether further scheduler time has scientific value",
            "forbidden_action": "endpoint harvest as if steady",
        },
        {
            "event": "terminal_steady_but_RAF_RMF_SVF_nonordinary",
            "next_allowed_row": "diagnostic_pressure_source_package",
            "allowed_action": "record as section-effective/recovery/diagnostic evidence",
            "forbidden_action": "ordinary component-K/F6 coefficient review",
        },
        {
            "event": "terminal_steady_low_recirculation_and_endpoint_fields_present",
            "next_allowed_row": "endpoint_field_harvest_readiness_then_same_QOI_UQ_gate",
            "allowed_action": "claim a sampler/readiness row for endpoint fields and hydrostatic/kinetic/recovery decomposition",
            "forbidden_action": "F6 admission before same-QOI mesh/time UQ and F3 comparison",
        },
    ]
    write_csv(OUT_DIR / "post_terminal_decision_tree.csv", terminal_rows)

    guardrail_rows = [
        {"guardrail": "new_scheduler_submission_in_this_task", "allowed": False, "reason": "existing active retry job is the source recovery attempt"},
        {"guardrail": "F6_scoring_now", "allowed": False, "reason": "terminal source evidence and endpoint fields are still missing"},
        {"guardrail": "component_K_or_cluster_K_admission", "allowed": False, "reason": "ordinary-flow and same-QOI UQ gates remain closed"},
        {"guardrail": "clipped_K_or_global_multiplier", "allowed": False, "reason": "explicitly prohibited pressure basis shortcuts"},
        {"guardrail": "native_output_mutation", "allowed": False, "reason": "CFD outputs are read-only provenance"},
        {"guardrail": "registry_or_admission_mutation", "allowed": False, "reason": "this is a monitor/documentation package only"},
    ]
    write_csv(OUT_DIR / "no_scoring_guardrails.csv", guardrail_rows)

    summary = {
        "task_id": TASK_ID,
        "generated_at_utc": generated_at,
        "decision": "continue_existing_cand001_retry_monitor_only_no_duplicate_submit",
        "candidate_id": "CAND-001",
        "active_retry_job_id": ACTIVE_JOB_ID,
        "active_retry_state_at_snapshot": active_state,
        "active_retry_running_at_snapshot": active_running,
        "active_retry_case_rows": len(source_contract_rows),
        "prior_timeout_jobs": len(timeout_rows),
        "readiness_context_rows": len(readiness_rows),
        "previous_gate_decision": gate_summary["decision"],
        "worth_continuing": True,
        "terminal_source_recovery_only": True,
        "new_scheduler_submission": False,
        "duplicate_submit_allowed": False,
        "f6_scoring_allowed_now": False,
        "component_k_admitted": False,
        "cluster_k_admitted": False,
        "clipped_k": False,
        "hidden_global_multiplier": False,
        "f6_fit_performed": False,
        "s11_s15_s6_trigger": False,
        "native_output_mutation": False,
        "registry_or_admission_mutation": False,
        "fluid_or_external_repo_edited": False,
        "blocker_register_change": False,
        "generated_index_refresh": False,
        "source_context": [
            str(GATE_DIR.relative_to(ROOT)),
            str(TIMEOUT_DIR.relative_to(ROOT)),
            str(READINESS_DIR.relative_to(ROOT)),
            str(RELAUNCH_MANIFEST.relative_to(ROOT)),
            str(RELAUNCH_README.relative_to(ROOT)),
            str(RELAUNCH_STATUS.relative_to(ROOT)),
        ],
    }
    write_text(OUT_DIR / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")

    readme = f"""---
provenance:
  generated_by: {Path(__file__).relative_to(ROOT)}
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - pressure
  - F6
  - CAND001
  - scheduler
  - terminal-source-recovery
related:
  - {GATE_DIR.relative_to(ROOT)}
  - {TIMEOUT_DIR.relative_to(ROOT)}
  - {RELAUNCH_MANIFEST.relative_to(ROOT)}
---

# CAND001 active retry terminal recovery

## Decision

CAND001 remains scientifically worth monitoring as terminal-source recovery, but
only through the already-running Salt4 high-heat relaunch job `{ACTIVE_JOB_ID}`.
This task did not submit, cancel, requeue, sample, harvest, or score anything.

The reason to continue is narrow: previous CAND001 evidence failed by scheduler
timeout, not by a physics contradiction, and the active relaunch has four source
cases with explicit restart times and a common target end time. If those cases
finish, they may provide the first terminal source evidence needed before an
endpoint-field readiness row.

## Why this is not F6 evidence

The current state is still missing terminal success, endpoint fields, ordinary
flow evidence, and same-QOI mesh/time UQ. Therefore this package explicitly
keeps `F6_scoring_now=false`, `component_K=false`, `cluster_K=false`, and
`S11/S15/S6 trigger=false`.

## What worked

- The S10/S14 gate produced a scheduler-safe runbook that separated terminal
  source recovery from F6 scoring.
- The high-heat relaunch package already created the appropriate scheduler
  attempt for CAND001, so the pressure path can avoid a duplicate submission.

## What did not work

- Prior jobs `3299610` and `3299620` timed out before terminal success.
- No endpoint pressure/F6 field package exists yet.
- No ordinary-flow or same-QOI UQ gate has passed.

## Next post-terminal action

After `{ACTIVE_JOB_ID}` reaches a terminal scheduler state, claim a separate
terminal-disposition/readiness row. That row may read logs and terminal fields,
but it still must not score F6 unless a later endpoint-field, ordinary-flow, F3,
and same-QOI UQ gate passes.
"""
    write_text(OUT_DIR / "README.md", readme)

    worth_doc = f"""---
provenance:
  generated_by: {Path(__file__).relative_to(ROOT)}
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - pressure
  - CAND001
  - scientific-worth
  - retry-gate
related:
  - {OUT_DIR.relative_to(ROOT) / 'worth_trying_decision.csv'}
  - {OUT_DIR.relative_to(ROOT) / 'post_terminal_decision_tree.csv'}
---

# Scientific worth assessment

## Finding

Continue CAND001 only as an active monitor of job `{ACTIVE_JOB_ID}`. Do not
launch a duplicate scheduler job. Do not score F6.

## Analysis

The retry is still scientifically defensible because the negative evidence so
far is operational: jobs `3299610` and `3299620` timed out. Timeout means the
source family has not yet produced terminal fields; it is not evidence that the
pressure decomposition is physically wrong.

The expected value is limited but real. A successful terminal run would provide
a low-recirculation/high-heat Salt4 source family that can be checked for
steady-state drift, endpoint field availability, and RAF/RMF/SVF ordinary-flow
status. Only after those checks could a separate endpoint harvest row be
considered.

The work should stop or pivot if `{ACTIVE_JOB_ID}` times out again, finishes
with unacceptable drift, or remains strongly recirculating at the target
sections. In those cases CAND001 should remain diagnostic/blocked and CAND002
or another lower-recirculation source family should be considered.
"""
    write_text(OUT_DIR / "scientific_worth_assessment.md", worth_doc)

    status = f"""---
provenance:
  generated_by: {Path(__file__).relative_to(ROOT)}
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - status
  - pressure
  - CAND001
related:
  - {OUT_DIR.relative_to(ROOT)}
---

# {TASK_ID}

## Objective

Claim and close a separate pressure-owned scheduler retry follow-up row for
CAND001 that only recovers terminal source evidence and cannot score F6.

## Outcome

Decision: `continue_existing_cand001_retry_monitor_only_no_duplicate_submit`.
The active relaunch job is `{ACTIVE_JOB_ID}` with `{len(source_contract_rows)}`
CAND001 source cases in the relaunch manifest. CAND001 is still worth monitoring
because prior failures were timeouts rather than physics rejections, but no new
job was submitted and no sampler/F6 work was authorized.

## Changes Made

- Wrote `{OUT_DIR.relative_to(ROOT)}/README.md`.
- Wrote `{OUT_DIR.relative_to(ROOT)}/scientific_worth_assessment.md`.
- Wrote scheduler/source/guardrail CSVs and summary JSON under
  `{OUT_DIR.relative_to(ROOT)}`.
- Wrote this status, a journal entry, and an import manifest.

## Validation

Pending at generation time; final validation is recorded after running the task
test and finish-task checker.

## Guardrails

- Native-output mutation: false.
- Registry/admission mutation: false.
- Scheduler submission/cancel/requeue: false.
- Solver/postprocessing/sampler/harvest launch: false.
- F6 fit/scoring, component-K, cluster-K, clipped-K, hidden/global multiplier:
  false.
- S11/S15/S6 trigger: false.
- Fluid/external edit: false.
"""
    write_text(ROOT / f".agent/status/2026-07-22_{TASK_ID}.md", status)

    journal = f"""---
provenance:
  generated_by: {Path(__file__).relative_to(ROOT)}
  task_id: {TASK_ID}
  generated_at_utc: {generated_at}
task: {TASK_ID}
tags:
  - journal
  - pressure
  - CAND001
related:
  - {OUT_DIR.relative_to(ROOT)}
---

# CAND001 active retry terminal recovery

## Attempted

Claimed a pressure-owned active retry row, read the prior S10/S14 retry/UQ gate,
the CAND001 timeout disposition, the low-recirculation source readiness table,
and the high-heat steady relaunch manifest. Queried scheduler/accounting state
for `{ACTIVE_JOB_ID}` and prior timeout jobs using read-only commands.

## Observed

The previous CAND001 jobs timed out before terminal source evidence. The current
active relaunch package contains four CAND001 Salt4 high-heat/no-recirculation
source cases targeted to `22000 s`. The scheduler snapshot recorded state
`{active_state}` for `{ACTIVE_JOB_ID}` at `{generated_at}`.

## Inferred

CAND001 is worth continuing only as monitor-only terminal source recovery. The
scientific basis is that timeout is not a physics rejection and terminal fields
could still unlock a later readiness decision. It remains non-evidence for F6
until terminal success, steady-state review, endpoint fields, ordinary-flow
screening, F3 comparison, and same-QOI UQ all pass under future rows.

## Contradictions or Caveats

The relaunch can become worthless for pressure admission if it times out again,
if drift remains large, or if endpoint sections remain nonordinary. This package
does not inspect native fields or make any flow-quality finding.

## Next Useful Actions

After `{ACTIVE_JOB_ID}` reaches terminal scheduler state, claim a terminal
disposition/readiness row. If successful, document terminal times, drift,
endpoint-field availability, and RAF/RMF/SVF screening. If failed, classify the
failure and decide whether CAND002 or another source family is a better use of
compute.
"""
    write_text(ROOT / ".agent/journal/2026-07-22/pressure-f6-cand001-active-retry-terminal-recovery.md", journal)

    import_manifest = {
        "task": TASK_ID,
        "generated_at_utc": generated_at,
        "native_solver_outputs_mutated": False,
        "registry_mutated": False,
        "scheduler_action": "read_only_squeue_sacct_snapshot_no_submit_cancel_requeue",
        "external_fluid_edit": False,
        "changed_files": [
            str((OUT_DIR / name).relative_to(ROOT))
            for name in [
                "README.md",
                "scientific_worth_assessment.md",
                "summary.json",
                "current_scheduler_snapshot.csv",
                "active_retry_source_contract.csv",
                "worth_trying_decision.csv",
                "duplicate_launch_guard.csv",
                "post_terminal_decision_tree.csv",
                "no_scoring_guardrails.csv",
            ]
        ]
        + [
            f".agent/status/2026-07-22_{TASK_ID}.md",
            ".agent/journal/2026-07-22/pressure-f6-cand001-active-retry-terminal-recovery.md",
            f"imports/2026-07-22_{SLUG}.json",
            "tools/analyze/build_pressure_f6_cand001_active_retry_terminal_recovery.py",
            "tools/analyze/test_pressure_f6_cand001_active_retry_terminal_recovery.py",
            ".agent/BOARD.md",
        ],
        "read_only_context": summary["source_context"]
        + [
            "scheduler/accounting state for jobs 3308712, 3299610, 3299620",
            "native CFD/OpenFOAM outputs",
            "registry/admission state",
            "Fluid source tree",
            "external repos",
            "blocker register",
            "generated docs index files",
        ],
        "mutation_flags": {
            "native_output_mutation": False,
            "registry_or_admission_mutation": False,
            "scheduler_submission_or_mutation": False,
            "solver_postprocessing_sampler_or_harvest_launch": False,
            "f6_scoring_or_fit": False,
            "component_cluster_or_clipped_k": False,
            "hidden_global_multiplier": False,
            "fluid_or_external_repo_edit": False,
            "blocker_register_change": False,
        },
        "provenance_notes": "Scheduler state was read only. Existing job 3308712 was recognized as the active CAND001 retry; no duplicate job was submitted.",
    }
    write_text(ROOT / f"imports/2026-07-22_{SLUG}.json", json.dumps(import_manifest, indent=2, sort_keys=True) + "\n")

    return summary


if __name__ == "__main__":
    print(json.dumps(build_outputs(), indent=2, sort_keys=True))
