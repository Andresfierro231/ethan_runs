---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/candidate_disposition.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/scheduler_disposition.csv
tags: [pressure, f6, cand001, timeout-disposition, no-admission]
related:
  - .agent/journal/2026-07-21/pressure-f6-cand001-timeout-disposition.md
  - imports/2026-07-21_pressure_f6_cand001_timeout_disposition.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/README.md
task: TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Scheduler / Tester / Writer
type: status
status: complete
---
# TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21

## Objective

Disposition `CAND-001` after high-heat job timeouts by refreshing scheduler
state, inspecting cited logs and partial-output availability, and deciding
whether the candidate is fail-closed, retry-needed, or partial-diagnostic-only.

## Outcome

Completed the package at
`work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/`.

Decision: `retry_needed_with_scheduler_plan`.

Current attempt disposition: `fail_closed_as_F6_evidence`.

Key observations:

- `3299610` / `salt4_q3x_probe`: `TIMEOUT`, elapsed `5-00:00:25`.
- `3299620` / `salt4_heat_pack`: `TIMEOUT`, elapsed `5-00:00:08`.
- Four CAND-001 source cases were reviewed.
- Logs end with Slurm time-limit cancellation, not clean solver completion.
- Root cases do not contain reconstructed terminal fields beyond `0`.
- Processor-local time directories exist, but they are not sampler-ready and
  not admission evidence.
- Terminal-successful source cases: `0`.
- Endpoint fields ready: `0`.

## Changes Made

- Added a reproducible CAND-001 timeout-disposition builder and tests.
- Generated scheduler, log, partial-output, endpoint-gate, candidate-decision,
  no-launch/no-admission, next-task, source-manifest, summary, and README
  artifacts.
- Added this status file, the matching journal entry, and import manifest.
- Updated the board row for this task only.

## Validation

- `python3.11 tools/agent/preflight_task.py --task-id TODO-PRESSURE-F6-CAND001-TIMEOUT-DISPOSITION-2026-07-21`
  passed before package edits.
- `sacct -j 3299610 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P`
  showed `TIMEOUT`.
- `sacct -j 3299620 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList -P`
  showed `TIMEOUT`.
- `tail -80` on the four cited high-heat logs showed time-limit cancellation.
- `find <case>/processors64 -maxdepth 2 -type d` and a read-only Python listing
  confirmed processor-local time directories but no reconstructed root terminal
  fields beyond `0`.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/build_pressure_f6_cand001_timeout_disposition.py work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/test_pressure_f6_cand001_timeout_disposition.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_cand001_timeout_disposition/test_pressure_f6_cand001_timeout_disposition.py`
  passed: `Ran 5 tests in 0.553s OK`.

## Guardrails

No native solver output, registry/admission state, scheduler state, Fluid source
tree, external repo, blocker register, generated docs index, manuscript/report
file, solver, postprocessor, sampler, or harvest output was mutated. No
scheduler submission/cancel/requeue, fitting/model selection, F6 fit, component
`K`, cluster `K`, clipped `K`, hidden/global multiplier, or admission claim was
produced.

## Remaining Blockers

F6 remains blocked by source readiness and ordinary-flow evidence. The next
choice is either a separate CAND-001 retry scheduler plan with walltime/resource
justification, or a separate CAND-002 corrected +/-10Q fallback
terminal-readiness audit. No staged-copy endpoint sampler should be claimed
until a terminal-successful source case exists.
