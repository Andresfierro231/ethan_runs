---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/explanation_hypothesis_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/split_runtime_leakage_audit.csv
tags: [journal, empirical-bias, train-only, forward-model]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21.md
  - imports/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
task: TODO-FLUID-EMPIRICAL-LEG-BIAS-CORRECTION-DIAGNOSTIC-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Empirical Leg Bias/Correction Diagnostic

## Attempted

Built a train-only affine empirical correction layer from Phase E Salt2
temperature residuals. The model is per leg:

`T_corrected = multiplier_leg * T_1D + offset_leg`.

The fit uses Phase H sensor source-segment mapping to group sensors by leg and
reports identifiability separately from train residual improvement.

## Observed

The empirical layer reduces train all-sensor MAE from `81.5815150583415 K` to
`7.2808975996294265 K`. TP MAE reduces from `80.24939106239617 K` to
`7.417446376296164 K`; TW MAE reduces from `82.18702596558934 K` to
`7.218829973871819 K`.

The coefficients are diagnostic rather than physically plausible direct
parameters. `junction` has no train sensors. `downcomer`, `upcomer`,
`cooling_branch`, and `lower_leg` are train-identifiable but carry
moderate-to-high overfit risk because the fit uses one Salt2 train case.

## Inferred

This is useful as a best-achievable train residual compression under a simple
affine residual layer. It supports a thesis explanation that physics carries
the model to the current Phase E residual, and the empirical layer measures
remaining leg-wise discrepancy. The coefficient signs/magnitudes suggest the
remaining discrepancy is not a clean scalar correction; it likely absorbs wall
layer mapping, source distribution, passive boundary, 3D-to-1D geometry, and
sensor placement effects.

## Contradictions Or Caveats

The empirical layer consumes post-solve train reference temperatures and is not
a runtime predictive model. It cannot be used for validation, holdout, or
external-test claims until frozen after a training protocol with multiple
independent train cases. Current coefficients should not be admitted as physics.

## Next Useful Actions

1. Create a frozen empirical-correction protocol that decides whether offsets,
   multipliers, or offset-only terms are allowed per leg before seeing
   validation rows.
2. Extend train/support data beyond one Salt2 case before using multipliers.
3. Compare the empirical coefficients against passive-boundary, source/sink,
   wall-layer, sensor-map, and upcomer exchange evidence to identify likely
   discrepancy owners.
4. Only after freezing a protocol, score validation; holdout and external-test
   remain untouched until after candidate freeze.
