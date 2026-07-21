---
provenance:
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/README.md
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv
  - jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_high_heat_steady_relaunch_pack.sbatch
tags: [openfoam, salt4, high-heat, relaunch, scheduler]
related:
  - .agent/journal/2026-07-21/high-heat-salt4-steady-relaunch.md
  - imports/2026-07-21_high_heat_salt4_steady_relaunch.json
task: TODO-HIGH-HEAT-SALT4-STEADY-RELAUNCH-2026-07-21
date: 2026-07-21
role: Scheduler/cfd-pp/Implementer/Tester/Writer
status: complete
---
# TODO-HIGH-HEAT-SALT4-STEADY-RELAUNCH-2026-07-21

## Objective

Relaunch the timed-out Salt4 high-heat bracket/probe cases for five more days
using the latest completed processor fields instead of returning to the stale
`10000 s` restart.

## Outcome

Submitted Slurm job `3308712` (`salt4_heat2_pack`) from `login1`. Early
scheduler state showed `RUNNING` on `c318-017` with four running `foamRun`
steps:

- `3308712.0`
- `3308712.1`
- `3308712.2`
- `3308712.3`

The job uses one node, `256` tasks, `64` tasks per case, and a `120:00:00`
walltime.

## Restart Contract

| Case | Restart time |
| --- | ---: |
| `salt4_q0500w_no_recirc_probe` | `11658` |
| `salt4_q1000w_no_recirc_probe` | `11031` |
| `salt4_q1500w_no_recirc_probe` | `10795` |
| `salt4_q3x_no_recirc_probe` | `11395` |

The launcher enforces `startFrom startTime`, the case-specific `startTime`,
`timeFormat general`, and `timePrecision 6`.

## Changes Made

- Added `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv`.
- Added `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_high_heat_steady_relaunch_pack.sbatch`.
- Updated the four staged high-heat `system/controlDict` files to use the
  case-specific restart times.
- Updated `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/README.md`
  with job `3308712` monitoring and guardrails.
- Wrote preflight logs under
  `jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/logs/`.

## Validation

- `bash -n jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/scripts/run_salt4_high_heat_steady_relaunch_pack.sbatch`
  passed.
- `python3.11 tools/analyze/check_corrected_salt_preflight.py --manifest jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/high_heat_steady_relaunch_manifest.csv --audit-out jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/logs/steady_relaunch_pre_submit_preflight.csv --json-out jadyn_runs/modern_runs/2026-07-16_high_heat_no_recirc_probe/logs/steady_relaunch_pre_submit_preflight.json --check-runtime-controls --min-time-precision 6 --max-time-precision 6 --required-time-format general --expected-processors 64 --restart-time salt4_jin_q0500w_no_recirc_probe=11658 --restart-time salt4_jin_q1000w_no_recirc_probe=11031 --restart-time salt4_jin_q1500w_no_recirc_probe=10795 --restart-time salt4_jin_q3x_no_recirc_probe=11395`
  reported `Audited 4 corrected Salt cases; failures=0`.
- In-job preflight
  `logs/steady_relaunch_runtime_preflight_3308712.csv` reported
  `overall_ok=True` for all four cases.
- `sacct -j 3308712 --format=JobID,JobName%30,State,ExitCode,Elapsed,Timelimit,NodeList%30`
  showed the parent job and four `foamRun` steps running.

## Guardrails

- Native imported source outputs were not modified.
- Registry/admission state was not modified.
- No solver postprocessing, harvest, sampler, fitting, model selection, closure
  admission, or thesis/manuscript claim was made.
- Do not harvest or admit results from `3308712` until it reaches terminal
  state and a separate board row claims endpoint disposition/postprocessing.

## Next Useful Action

Monitor `3308712` with `squeue`/`sacct` and per-case solver logs. On terminal
success or timeout, compute mdot, temperature, and heat drift over the latest
window before deciding whether any case is steady enough to use.
