---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensor_delta.csv
tags: [forward-model, empirical-bias, affine-correction, train-only]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-empirical-leg-bias-correction-diagnostic.md
  - imports/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic.json
task: TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Empirical Leg Bias/Correction Diagnostic

This package fits a train-only affine empirical correction:

`T_corrected = multiplier_leg * T_1D + offset_leg`

The words are intentionally separated: `offset` is the additive empirical bias,
and `multiplier` is the empirical correction factor. Neither is admitted
physics.

## Result

All-sensor train MAE changes from `81.581515 K` to
`7.280898 K`.

Gate: diagnostic only. This is the best train-only fit under the declared
per-leg affine layer, but it is not a predictive model until tested through
frozen train/validation/holdout/external protocol.

## Open First

- `leg_bias_correction_coefficients.csv`
- `corrected_train_residual_metrics.csv`
- `identifiability_audit.csv`
- `explanation_hypothesis_ledger.csv`
- `split_runtime_leakage_audit.csv`
