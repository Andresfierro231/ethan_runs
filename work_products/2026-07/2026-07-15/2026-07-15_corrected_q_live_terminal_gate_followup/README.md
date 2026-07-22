---
provenance:
  - operational_notes/07-26/13/2026-07-13_TOMORROW_CORRECTED_SALT_Q_LIVE_JOB_HANDOFF.md
  - .agent/journal/2026-07-14/corrected-salt-q-live-job-admission.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/logs/selected_runtime_preflight_3293924.csv
tags: [cfd-pp, salt-q-perturbation, live-job, terminal-harvest, admission]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/README.md
  - operational_notes/maps/cfd-runs-and-admission.md
task: AGENT-408
date: 2026-07-15
role: cfd-pp/Coordinator/Writer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Corrected-Q Live Terminal Gate Followup

## Observed Facts

Slurm job `3293924` (`saltq_sel_cont`) is still running on `c318-016`. The batch job and all four `foamRun` steps are live after `1-15:26:54` top-level elapsed time at this snapshot.

The dependent selected +/-10Q harvester `3295438` (`saltq_s24_sel_harv`) is pending for dependency. Its sbatch contract is `afterany:3293924`, so it should not start until the parent selected continuation exits.

The stopped +/-5Q harvest job `3295437` completed successfully on 2026-07-14 and wrote outputs under `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/stopped_salt2_salt4_pm5q`. That work should not be relaunched.

The runtime preflight for `3293924` passed for all four selected cases: `config_ok`, `root_field_ok`, `processor_field_ok`, `runtime_controls_ok`, and `overall_ok` are all true with 64 processor blocks and zero frame errors.

Latest live solver times parsed from the current solver logs:

| Row | Latest live solver time (s) | State |
| --- | ---: | --- |
| `salt2_lo10q` | 11036.153374 | running |
| `salt2_hi10q` | 10389.701657 | running |
| `salt4_lo10q` | 12278.286458 | running |
| `salt4_hi10q` | 13145.502392 | running |

## Inferred Interpretation

The selected +/-10Q corrected-Q continuation is alive and progressing. It is not yet terminal evidence. These four rows remain `blocked_pending_terminal_gate` and must not enter downstream training, validation, holdout, pressure/upcomer, or split products until terminal harvest and operating-point convergence evidence exists.

The current blocker is not missing submission. The selected harvester is already submitted as `3295438` and correctly held behind `3293924`.

## What Is Usable Now

No selected +/-10Q row from `3293924` is usable now.

Stopped +/-5Q rows from `3295437` have completed harvest evidence and are being consumed by later BC/admission/split work products. That lane is separate from this live +/-10Q gate.

## What Is Running

`3293924` is running:

- `3293924.0`: `salt2_lo10q`
- `3293924.1`: `salt2_hi10q`
- `3293924.2`: `salt4_lo10q`
- `3293924.3`: `salt4_hi10q`

## What Is Blocked

The following remain blocked:

- selected +/-10Q terminal harvest;
- selected +/-10Q operating-point convergence/admission gate;
- any downstream split/training/holdout use of selected +/-10Q rows;
- dependency-held selected +/-10Q harvester `3295438`;
- downstream hydraulic stages `3295989`, `3295990`, and `3295991`, because they remain dependency-held.

## Next Required Actions

1. Keep monitoring `3293924` with the commands in `next_monitoring_commands.md`.
2. When `3293924` and steps `.0` through `.3` are terminal, verify `3295438` starts and finishes.
3. Consume `3295438` outputs from `selected_salt2_salt4_pm10q_after_3293924`.
4. Run or refresh the operating-point convergence gate; do not admit on Slurm `COMPLETED` alone.
5. Hand admitted rows to the active admission/split ledger only after row-specific terminal evidence exists.

## Guardrails

No native CFD outputs were modified. No solver, postprocessing, or scheduler job was launched or cancelled by this task. Whole-log fatal scans are misleading here because the solver logs retain historical appended failure blocks; use scheduler state plus current terminal tails/ranges for live status.
