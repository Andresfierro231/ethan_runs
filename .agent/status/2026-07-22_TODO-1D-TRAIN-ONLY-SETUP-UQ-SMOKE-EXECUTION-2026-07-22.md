---
provenance:
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
tags: [status, predictive-1d, setup-uq, smoke-execution]
related:
  - .agent/journal/2026-07-22/1d-train-only-setup-uq-smoke-execution.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_execution.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22

## Objective

Execute a bounded train-only setup-UQ smoke against the read-only Fluid
`solve_case` API, with fail-closed runtime legality and no release/scoring.

## Current Outcome

Complete. Slurm job `3310985` completed `COMPLETED 0:0` in `00:38:40` on
`c318-011`. The canonical terminal harvest is recorded under
`work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator/`.

Execution decision:
`train_only_setup_uq_smoke_executed_no_release_no_score`.

Terminal result: `3/3` baseline roots accepted and `33/33` one-at-a-time
setup-legal variant roots accepted. This remains smoke-only evidence: no
candidate freeze, protected scoring, source/property release, coefficient
admission, or final score was produced.

## Changes Made

- Added `tools/analyze/build_1d_train_only_setup_uq_smoke_execution.py`.
- Added `tools/analyze/test_1d_train_only_setup_uq_smoke_execution.py`.
- Added backward-compatible handling for the scheduler wrapper's legacy
  `--output-dir --run-smoke` builder CLI and test `--output-dir` argument.
- Published `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/` with runtime, baseline,
  sensitivity, skip, heat-ledger, split-audit, source-manifest, guardrail, and
  summary artifacts.
- Added `LOCAL_BOUNDED_SMOKE_CAVEAT.md` to prevent the bounded local addendum
  from being mistaken for the terminal Slurm harvest.
- Terminal harvest row reconciled Slurm job `3310985` and wrote the terminal
  interpretation package.

## Validation

- Fluid one-case API preflight completed for Salt 2 before implementation.
- Task builder executed locally with solve budget `3`.
- Unit tests passed.
- JSON manifests parsed.
- Slurm job `3310985` was observed `COMPLETED 0:0`.
- Terminal post-run validator passed:
  `python3.11 tools/analyze/test_1d_train_only_setup_uq_smoke_execution.py --output-dir work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution`.

## Unresolved Blockers

No execution-row blocker remains. Scientific admission remains blocked outside
this row because the terminal harvest is smoke-only and residual-owner rows
remain diagnostic.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
OpenFOAM/postprocessing/sampler/harvest launch, Fluid/external edit,
validation/holdout/external-test tuning or scoring, fitting/tuning/model
selection, source/property release, candidate freeze, coefficient admission,
F6/component-K/internal-Nu/exchange-coefficient emission, final-score claim,
S11/S12/S13/S15/S6 trigger, blocker-register change, generated-index refresh,
or runtime use of CFD mdot, realized wallHeatFlux, imposed cooler duty,
validation temperatures, holdout temperatures, external-test temperatures,
realized test-section heat, or hidden global multiplier occurred.
