# Salt1 Combined Rigor Relaunch Plan

Date: `2026-07-08`
Role: Coordinator / Implementer / Writer
Task ID: `AGENT-222`

## Objective

Evaluate the request to cancel the running Salt1 nominal continuation and
relaunch it together with lightweight monitor/replay work in one allocation.

## Evidence Checked

- `squeue -j 3282992`
- Salt1 continuation stdout/stderr.
- Salt1 `logs/log.foamRun_salt1_nominal_continuation`.
- Salt1 retained `processors64` restart directories.
- Salt1 `system/controlDict`.
- Current Slurm queue state.
- Prior AGENT-218 allocation rejection.

## Findings

- Salt1 job `3282992` is running.
- The live log was advancing around `Time = 4187.4s`.
- The case has retained restart directories up to `4187`.
- `controlDict` uses `startFrom latestTime`, `writeInterval 1`, and
  `purgeWrite 21`.
- Canceling would terminate the job, not pause it.
- A replacement combined job still needs a one-node 120-hour Salt1 allocation.
- TACC already rejected a 12-SU lightweight job because the project is
  over-encumbered, so cancel-and-relaunch is not currently safe.

## Action

Did not cancel `3282992`.

Staged:

- `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_with_rigor_monitors.sbatch`

The staged script runs the lightweight corrected-Salt monitor/preflight and 1D
replays first, then starts the Salt1 OpenFOAM continuation from latest retained
restart.

## Validation

Validation command:

```bash
bash -n jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/scripts/run_salt1_nominal_with_rigor_monitors.sbatch
```

No native solver output was modified.
