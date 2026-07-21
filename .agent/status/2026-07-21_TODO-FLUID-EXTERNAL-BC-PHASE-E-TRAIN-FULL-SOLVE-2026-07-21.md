---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/pressure_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
tags: [forward-model, predictive-1d, thermal-boundary, runtime-leakage]
related:
  - .agent/journal/2026-07-21/fluid-external-bc-phase-e-train-full-solve.md
  - imports/2026-07-21_fluid_external_bc_phase_e_train_full_solve.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/README.md
task: TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21
date: 2026-07-21
role: Forward-pred/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21

## Objective

Run a train/support-only full local Fluid 1D solve through the Phase C/D
external-boundary dictionary path, emit pressure and thermal residual
attribution, and keep validation, holdout, external-test, fitting, freeze, and
admission claims out of scope.

## Outcome

Complete. The package filtered the 24-row external BC dictionary to 8 `salt_2`
train rows, converted 5 predictive passive source rows into 12 Fluid role rows
through the Phase B segment map, and ran `solve_case` for `Salt 2` with
`outer_closure_mode=external_boundary_table`.

The numerical solve returned `root_status=accepted` with:

- `mdot_kg_s = 0.00626567502343775`
- `pressure_residual_Pa = -1.3016870923365786e-06`
- `temperature_periodicity_error_K = 4.201831416139612e-08`
- `qambient_total_W = 288.37885218645016`
- `qhx_total_W = 14.312904798460508`

The post-solve train reference residuals are large:

- reference mdot `0.0168 kg/s`; residual `-0.010534324976562249 kg/s`
- TP mean absolute residual `80.24939106239617 K`
- TW mean absolute residual `82.18702596558934 K`
- max absolute temperature residual `109.09380824932663 K`

Interpretation: the runtime path now executes as a full local Fluid solve, but
the result is residual-attribution evidence only. It is not a freeze, score, or
admission.

## Changes Made

- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/build_phase_e_train_full_solve.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/check_phase_e_train_full_solve.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/*.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/*.json`
- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-PHASE-E-TRAIN-FULL-SOLVE-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-external-bc-phase-e-train-full-solve.md`
- `imports/2026-07-21_fluid_external_bc_phase_e_train_full_solve.json`

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/build_phase_e_train_full_solve.py work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/check_phase_e_train_full_solve.py` -> OK.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/build_phase_e_train_full_solve.py` -> OK.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/check_phase_e_train_full_solve.py` -> `Phase E train full solve checks passed.`
- In external Fluid root: `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m pytest -q -p no:cacheprovider tests/test_external_boundary_contract.py` -> `7 passed, 6 subtests passed in 0.52s`.

## Guardrails

- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: no action.
- OpenFOAM solver/postprocessing: not launched.
- Local Fluid 1D solver: `solve_case` only, allowed by this row.
- External Fluid repo: imported and tested read-only; not edited.
- Validation rows consumed: 0.
- Holdout rows consumed: 0.
- External-test rows consumed: 0.
- Fitting/model selection: not performed.
- Freeze/admission/final predictive score: not claimed.
- Blocker register, generated docs index, and thesis files: not changed.
