# Coordinator Status And Task Queue

Date: `2026-07-07`
Role: Coordinator / Writer
Task: `AGENT-180` continuation

## Scheduler Correction

The corrected-Salt postprocess/gate wrapper was accidentally staged on
`development`. It has been patched to `NuclearEnergy` and resubmitted with the
same dependency:

- canceled stale job: `3278453` `saltq_gate_after`, partition `development`;
- replacement job: `3279638` `saltq_gate_after`, partition `NuclearEnergy`;
- dependency: `afterany:3275448:3275449:3275560`.

Current queue check after replacement:

- `3279638` pending on dependency;
- `3275448`, `3275449`, and `3275560` still running on `NuclearEnergy`.

## Water Postprocess Rerun

Job `3278452` finished in `00:00:33` because it was not a new solver run or
heavy OpenFOAM extraction. It was a lightweight status/consolidation pass over
existing logs and existing closure tables:

- build run-status inventory with `--no-sacct` and explicit job-state overrides;
- rebuild consolidated closure table;
- rebuild next-model-form summary.

The short runtime is plausible for this workflow. The caveat is scientific, not
operational: Water rows are provisional freeze/postprocess rows from timed-out
job `3265970`, not completed new Water solver evidence.

## Corrected Salt Q Sanity Check

These are corrected Salt Q perturbation/permutation cases, staged from nominal
Salt Jin continuations with heater power ratios:

- Salt 1: `0.90`, `1.10`;
- Salt 2/3/4: `0.90`, `0.95`, `1.05`, `1.10`.

The manifest records target heater powers and balanced cooler sinks. Launch-time
preflight audits exist for the active cases and report:

- root `0/T` target patch counts present;
- decomposed `processors64/<latest>/T` target patch counts present across all
  64 processors;
- `root_patch_ok=True`;
- `processor_patch_ok=True`.

Live mdot monitors show that every active corrected case is moving in the
expected direction from its restart value:

| Job | Case | Q ratio | Advance (s) | mdot move | Simple expected move | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `3275448` | `salt1_jin_lo10q_corrected` | 0.90 | 1659.7 | -6.879% | -3.451% | running |
| `3275448` | `salt1_jin_hi10q_corrected` | 1.10 | 254.3 | +4.101% | +3.228% | ended early; needs gate scrutiny |
| `3275448` | `salt2_jin_lo10q_corrected` | 0.90 | 1494.0 | -6.910% | -3.451% | running |
| `3275448` | `salt2_jin_lo5q_corrected` | 0.95 | 1497.0 | -3.432% | -1.695% | running |
| `3275449` | `salt2_jin_hi5q_corrected` | 1.05 | 1178.0 | +3.272% | +1.640% | running |
| `3275449` | `salt2_jin_hi10q_corrected` | 1.10 | 1109.0 | +6.377% | +3.228% | running |
| `3275449` | `salt3_jin_lo10q_corrected` | 0.90 | 1143.0 | -6.007% | -3.451% | running |
| `3275449` | `salt3_jin_lo5q_corrected` | 0.95 | 1123.0 | -2.943% | -1.695% | running |
| `3275560` | `salt4_jin_lo10q_corrected` | 0.90 | 1030.0 | -6.128% | -3.451% | running |
| `3275560` | `salt4_jin_lo5q_corrected` | 0.95 | 1065.0 | -3.030% | -1.695% | running |
| `3275560` | `salt4_jin_hi5q_corrected` | 1.05 | 866.0 | +2.761% | +1.640% | running |
| `3275560` | `salt4_jin_hi10q_corrected` | 1.10 | 954.0 | +5.888% | +3.228% | running |

Interpretation: the corrected cases are not stale nominal replays. They are
responding to the intended heat-input perturbations. They still are not
admissible closure data until a late-window operating-point gate confirms that
the new mdot has re-plateaued. The early-ended `salt1_jin_hi10q_corrected` row
is the main caution because the solver stopped after only about `254 s` past
restart.

The pending Salt gate collector now emits explicit inspection columns in
`corrected_salt_solver_audit_summary.csv`:

- `advance_since_restart_s`;
- `advance_fraction_of_target`;
- `mdot_move_pct`;
- `expected_move_pct`;
- `mdot_move_direction_ok`;
- `late_window_drift_pct`;
- `late_window_amp_pct`;
- `needs_special_gate_scrutiny`;
- `scrutiny_reason`.

Smoke test result on `2026-07-07`: `salt1_jin_hi10q_corrected` is flagged with
`needs_special_gate_scrutiny=True` and reason
`solver ended before enough post-restart advancement (<1000s or <20% of target extension)`.
This flag must be carried into any inspection and postprocessing handoff so the
row is not admitted accidentally.

## Jin Per-Leg Gap Failure

Job `3278454` was submitted with the corrected `PYTHONPATH`; the import problem
from job `3275531` is gone. It failed because the copied July 4 script calls
`dataclasses.replace(..., use_radiation=...)`, but the current Fluid
`ScenarioConfig` field is `radiation_on`. This is a script/API drift issue, not
a bad Slurm submission.

## Open Coordinator Task Queue

Proposed distributable work packages:

1. `Salt live sanity monitor`: implement or run a reusable read-only checker
   that maps active packed Salt jobs to cases, reports latest time, mdot
   movement from restart, late-window drift/amplitude, fatal-log markers,
   preflight audit status, and `continue / stop / investigate`. This is the
   highest-value workflow/documentation gap from the July 4 script TODO.
2. `Corrected Salt preflight checker`: promote the current patch audit into a
   maintained command that validates `case_config.yaml`, root `0/T`, and
   `processors64/<latest>/T`, including collated frame preservation and all
   target heater/cooler patch counts.
3. `Jin per-leg gap API refresh`: update the copied analysis script from
   `use_radiation` to `radiation_on`, smoke-test against current Fluid
   `ScenarioConfig`, and resubmit only after confirming no additional stale API
   fields.
4. `Pressure decomposition / F4 queue`: continue the July 4 pressure roadmap:
   extract/fit Ri-vs-`f/f_lam`, implement buoyancy-modified friction candidate
   forms, then compare with existing F1/F3/F5 results.
5. `Water provisional-output audit`: document that the July 6 Water output is a
   freeze/status consolidation from timed-out job `3265970`, not a new completed
   solver run; decide whether any report text needs to downgrade Water language.
6. `Script/workflow inventory`: start the July 4 workflow-streamlining TODO,
   with live CFD convergence triage as the first maintained runbook/wrapper.

Items the user said they will handle directly in this session:

- Salt gate output after `3279638` runs.
- Jin per-leg gap rerun follow-through.
- Water provisional-output follow-through.

Coordinator focus should therefore stay on task definition, evidence capture,
and avoiding overlap between agents.

## Worker Launch Documentation Instructions

Workers should receive explicit documentation instructions up front. Require
each worker to create or update a task-scoped status/handoff note before ending,
even if they only inspect and do not edit code.

Minimum worker prompt requirements:

1. Read root `AGENTS.md`, `.agent/BOARD.md`, `.agent/FILE_OWNERSHIP.md`, and
   `.agent/ROLES.md` before touching files.
2. State role and task ID. If no task row exists, remain read-only or ask the
   coordinator to create a row before editing.
3. State allowed edit paths and read-only paths in the first status update.
4. Write a short objective block:
   - objective;
   - inputs/provenance to inspect;
   - planned outputs;
   - acceptance criteria;
   - what must not be changed.
5. While working, keep generated outputs under a task-scoped dated directory
   such as `work_products/YYYY-MM-DD_<task_slug>/` or
   `tmp/YYYY-MM-DD_<task_slug>/`.
6. At completion, write a status or handoff note with:
   - commands run;
   - files changed or generated;
   - observed results;
   - interpretation vs raw observation;
   - blockers and unresolved questions;
   - exact next action.
7. For scheduler or CFD monitoring workers, require a machine-readable CSV/JSON
   plus a README. The README must include Slurm job IDs, partition, dependency,
   latest case times, fatal/error scan status, and an admit/hold/investigate
   recommendation.
8. For any closure/admission worker, require an explicit admission boundary:
   rows are not closure-fit data unless the named gate says so. For corrected
   Salt Q, carry `needs_special_gate_scrutiny` forward and hold any flagged row
   pending coordinator review.

Suggested worker output note names:

- `.agent/status/YYYY-MM-DD_<TASKID>.md` for task status;
- `.agent/journal/YYYY-MM-DD/<slug>.md` for durable narrative;
- `operational_notes/07-26/07/<dated_slug>.md` for coordinator-facing runbooks
  or task queues.
