---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensitivity_status.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensitivity_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/owner_delta.csv
tags: [forward-model, external-bc, heat-loss-sensitivity, train-only]
related:
  - .agent/journal/2026-07-21/fluid-extbc-phase-h-compute-safe-sensitivity.md
  - imports/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/README.md
task: TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21

## Objective

Run the six predeclared Phase H train-only external-BC heat-loss perturbations
one-at-a-time through local Fluid 1D subprocesses with hard timeouts and
partial CSV flushing. Keep the output diagnostic only: no validation, holdout,
external-test scoring, fitting, repair, freeze, or admission.

## Outcome

Complete. All six requested perturbations completed within the `90 s`
per-sensitivity timeout and wrote the requested CSV outputs:

- `sensitivity_status.csv`: `6` pass, `0` fail, `0` timeout.
- `sensitivity_metrics.csv`: mdot, pressure residual, heat totals, and TP/TW/all residual metrics.
- `sensor_delta.csv`: per-sensor change versus Phase E/F-J baseline.
- `owner_delta.csv`: heated-incline/TW5 response classification.

The dominant heated-incline/TW5 residual is responsive to passive heat-loss
assumptions, but the response is not localized cleanly to the lower-leg lane:

- `lower_leg_hA_scale_0.5`: TW5 absolute residual improved by `4.59310690807564 K`.
- `lower_leg_hA_scale_2.0`: TW5 absolute residual worsened by `7.478576361192836 K`.
- `global_passive_hA_scale_0.5`: TW5 absolute residual improved by `51.63369382647278 K`; all-probe MAE improved by `47.133590749185956 K`.
- `global_passive_hA_scale_2.0`: TW5 absolute residual worsened by `27.638341480119664 K`; all-probe MAE worsened by `28.155039906096434 K`.
- `ambient_drive_delta_+15K`: TW5 absolute residual improved by `13.472549886792422 K`.
- `ambient_drive_delta_-5K`: TW5 absolute residual worsened by `4.492058432100237 K`.

Interpretation: the Phase E thermal residual is not insensitive to the passive
heat-loss network. A global passive hA decrease can recover a large share of
the residual, while lower-leg-only scaling has a small effect. This supports a
focused next analysis on dictionary/source-family coverage, physical hA basis,
and missing source/sink or axial redistribution physics before any repair is
admitted.

## Changes Made

- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/run_phase_h_compute_safe_sensitivity.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/check_phase_h_compute_safe_sensitivity.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/*.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/*.json`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/worker_results/*`
- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H-COMPUTE-SAFE-SENSITIVITY-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-extbc-phase-h-compute-safe-sensitivity.md`
- `imports/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity.json`

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/run_phase_h_compute_safe_sensitivity.py work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/check_phase_h_compute_safe_sensitivity.py` -> OK.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/run_phase_h_compute_safe_sensitivity.py --timeout-seconds 90` -> OK; six subprocess sensitivities passed.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/check_phase_h_compute_safe_sensitivity.py` -> `Phase H compute-safe sensitivity checks passed.`

## Notes

The first runner implementation used `subprocess.run(..., timeout=150,
capture_output=True)` and was interrupted after hanging inside subprocess
communication. The final runner uses `Popen(..., start_new_session=True)`,
captures stdout/stderr to task-owned log files, polls manually, and kills the
worker process group on timeout before flushing partial CSVs.

## Guardrails

- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: no action.
- OpenFOAM solver/postprocessing/sampler/harvest: not launched.
- Local Fluid 1D solver: `solve_case` only, inside task-owned subprocesses.
- External Fluid repo: imported read-only; not edited.
- Validation rows consumed: 0.
- Holdout rows consumed: 0.
- External-test rows consumed: 0.
- Fitting/model selection: not performed.
- Repair/freeze/admission/final predictive score: not claimed.
- Source/property release: not performed.
- Blocker register, generated docs index, and thesis files: not changed.
