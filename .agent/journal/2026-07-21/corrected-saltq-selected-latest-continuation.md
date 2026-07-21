---
provenance:
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/README.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/TODO.md
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/scripts/run_selected_corrected_salt_q_continuation_20260721_latest.sbatch
  - jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv
tags: [openfoam, slurm, corrected-salt-q, continuation, thermal]
related:
  - .agent/status/2026-07-21_AGENT-576.md
  - imports/2026-07-21_corrected_saltq_selected_latest_continuation.json
task: AGENT-576
date: 2026-07-21
role: Coordinator/Scheduler/Implementer/Tester/Writer
type: journal
status: submitted
---
# Corrected Salt-Q Selected Latest Continuation

User objective: continue the selected corrected-Q Salt2/Salt4 runs for about a
day and a half because mdot looked steady but the thermal probes, especially
`salt4_hi10q`, were still moving.

Observed before submission:

- Prior solver job `3293924` timed out after five days.
- Dependent selected harvester `3295438` completed, but the timeout meant the
  four-row set still needed a renewed thermal stationarity check.
- Latest retained integer restart directories existed at `12382`, `11668`,
  `13421`, and `14017`.
- No active `saltq` job was present in `squeue`.

Implementation:

- Added `run_selected_corrected_salt_q_continuation_20260721_latest.sbatch` as
  a distinct copy of the July 13 selected launcher.
- Changed the job name to `saltq_sel36_cont` and walltime to `36:00:00`.
- Changed restart overrides to the latest retained integer restarts:
  `12382`, `11668`, `13421`, and `14017`.
- Updated the four staged `system/controlDict` files to the same starts so the
  read-only preflight checker validated the exact intended runtime controls.

OpenFOAM lessons preserved:

- Patch the selected `processors64/<restart>/T` immediately before launch.
- Use explicit integer `startTime`, not `latestTime`.
- Keep `timeFormat general` and `timePrecision 6`; avoid the failed fixed-format
  and high-general-precision restart attempts from July 13.
- Reject any `writeNow` stop monitor before launch.
- Use the current LS6 OpenFOAM 13 / Intel MPI runtime and `libRCWallBC.so`.
- Pack four 64-rank cases into one 256-task node.

Validation:

- `bash -n` passed on the new launcher.
- `check_corrected_salt_preflight.py` passed locally for all four latest
  restarts with runtime controls checked.
- Submitting directly from this shell did not work because it was running on
  compute node `c318-008`; the local `sbatch` is a function that prints
  "sbatch not available on compute nodes." Submission was therefore repeated
  through `login3`.
- Slurm accepted job `3307441`; it started on `c318-020`.
- In-job preflight passed and all four `foamRun` steps advanced past startup.

Next useful action:

Monitor `3307441` to terminal state. When it lands, rerun mdot and thermal
stationarity checks before any harvest/admission. Do not submit a duplicate
selected harvester while this continuation is running.

Guardrails: no native imported CFD output mutation, no registry mutation, no
Fluid edit, no admission change, and no duplicate harvest.
