---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/smoke_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/runtime_leakage_audit.csv
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/journal/2026-07-21/fluid-external-bc-phase-d-smoke-scorecard.md
  - imports/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21
date: 2026-07-21
role: Forward-pred/Tester/Writer
type: status
status: complete
---
# TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21

## Objective

Run a minimal train/support smoke after Fluid Phase C to prove the runtime-legal
external thermal input path and publish pressure/thermal claim boundaries
without fitting, scoring heldout rows, or admitting a final predictive model.

## Outcome

Complete. The package filters the external boundary dictionary to one
`salt_2` train predictive row (`upcomer:ambient_wall`), maps it explicitly to
`left_upper_vertical`, loads it through the external Fluid parser, converts it
to one solver role row, validates the solver external-boundary contract, and
computes one setup-only heat-path accounting value.

Key result: `computed_external_loss_W = 65.37489732389939` for a synthetic smoke
state (`T_bulk=650 K`, `mdot=0.02 kg/s`). This is heat-path execution evidence
only, not a scored CFD prediction.

## Changes Made

- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/build_phase_d_smoke_scorecard.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/check_phase_d_smoke_scorecard.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/*.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/summary.json`
- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-D-SMOKE-SCORECARD-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-external-bc-phase-d-smoke-scorecard.md`
- `imports/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard.json`

## Validation

- `python3.11 tools/agent/finish_task.py --task-id TODO-FLUID-EXTERNAL-BC-PHASE-C-IMPLEMENTATION-2026-07-21` -> OK before Phase D.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/build_phase_d_smoke_scorecard.py work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/check_phase_d_smoke_scorecard.py` -> OK.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/build_phase_d_smoke_scorecard.py` -> OK.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/check_phase_d_smoke_scorecard.py` -> `Phase D smoke scorecard checks passed.`

## Guardrails

- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: no action.
- Solver/postprocessing launch: no full solver or OpenFOAM postprocessing launched.
- External Fluid repo: imported read-only; not mutated by this task.
- Fitting/model selection: not performed.
- Validation, holdout, external-test scoring: not performed.
- Final predictive admission: not claimed.
- Generated docs index and blocker register: not changed.
