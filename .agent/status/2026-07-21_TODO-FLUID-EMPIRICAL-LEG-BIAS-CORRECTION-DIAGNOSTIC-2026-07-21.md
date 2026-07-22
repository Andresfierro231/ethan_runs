---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/corrected_train_residual_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/leg_bias_correction_coefficients.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/identifiability_audit.csv
tags: [forward-model, empirical-bias, affine-correction, train-only]
related:
  - .agent/journal/2026-07-21/fluid-empirical-leg-bias-correction-diagnostic.md
  - imports/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
task: TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21

## Objective

Build a train-only empirical per-leg affine correction diagnostic from Phase E
Salt2 sensor residuals, using `offset` as additive bias and `multiplier` as
empirical correction. Keep coefficients diagnostic, not admitted physics.

## Outcome

Complete. The affine layer reduced Salt2 train all-sensor MAE from
`81.5815150583415 K` to `7.2808975996294265 K`, and RMSE from
`83.36187927489736 K` to `12.808105478110905 K`.

This is a strong train-fit upper bound, not a predictive admission. The fitted
coefficients are large and in several legs nonphysical as direct parameters:

- `downcomer`: multiplier `0.03160041207165762`, offset `432.877688945687 K`.
- `upcomer`: multiplier `-1.467820052785808`, offset `998.3334085797089 K`.
- `cooling_branch`: multiplier `7.360667625024831`, offset `-2262.5576959758378 K`.
- `lower_leg`: multiplier `1.7662951035987544`, offset `-179.05867121736838 K`.
- `junction`: no train sensors, not identifiable.

Interpretation: the empirical layer is useful as residual ownership and as a
thesis-safe demonstration of the remaining discrepancy magnitude after the
physics model. It must not be described as a physical closure until multiple
independent train cases and protected split behavior support it.

## Changes Made

- `tools/analyze/build_fluid_empirical_leg_bias_correction_diagnostic.py`
- `tools/analyze/test_fluid_empirical_leg_bias_correction_diagnostic.py`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/*.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/summary.json`
- `operational_notes/maps/forward-predictive-model.md`
- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21.md`
- `.agent/journal/2026-07-21/fluid-empirical-leg-bias-correction-diagnostic.md`
- `imports/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic.json`

## Validation

- `env PYTHONDONTWRITEBYTECODE=1 python3.11 -m py_compile tools/analyze/build_fluid_empirical_leg_bias_correction_diagnostic.py tools/analyze/test_fluid_empirical_leg_bias_correction_diagnostic.py` -> OK.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 tools/analyze/build_fluid_empirical_leg_bias_correction_diagnostic.py` -> OK.
- `env PYTHONDONTWRITEBYTECODE=1 python3.11 tools/analyze/test_fluid_empirical_leg_bias_correction_diagnostic.py` -> `Empirical leg bias/correction diagnostic checks passed.`

## Guardrails

- Fluid solve: not run.
- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: no action.
- Solver/postprocessing/sampler/harvest: not launched.
- External Fluid source: not edited.
- Validation rows scored: 0.
- Holdout rows scored: 0.
- External-test rows scored: 0.
- Physical fitting/model selection: not performed.
- Empirical train fit: diagnostic only.
- Freeze/admission/final predictive score: not claimed.
- Source/property release: not performed.
- Blocker register, generated docs index, and thesis current files: not changed.
