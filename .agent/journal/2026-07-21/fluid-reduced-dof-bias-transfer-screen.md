---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
tags: [journal, forward-model, empirical-bias, frozen-transfer]
related:
  - .agent/status/2026-07-21_TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21.md
  - imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json
task: TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Reduced-DOF Bias Transfer Screen

## Attempted

Built a reduced empirical temperature correction screen following the prior
per-leg affine diagnostic. The new screen predeclares six lower-complexity
families:

- `F0_null_baseline`
- `F1_global_offset`
- `F2_global_affine`
- `F3_sensor_kind_offset`
- `F4_thermal_family_offset`
- `F5_thermal_family_offset_shared_multiplier`

The package fits coefficients only on Salt1/Salt2 train/support rows from the
existing TSWFC2 bounded nominal scorecard and applies the frozen coefficients
unchanged to Salt3/Salt4 legacy validation/holdout-style stress rows.

## Observed

The source Phase E package had only Salt2 train rows, so it could not support
protected split transfer scoring. The existing TSWFC2 bounded nominal scorecard
had compatible sensor-level predicted/reference rows for Salt1-Salt4 and a
runtime audit stating validation records were loaded only after `solve_case`
returned.

The reduced families compress the Salt3/Salt4 score-only transfer residuals
strongly. The best score-only transfer result is
`F5_thermal_family_offset_shared_multiplier`, reducing transfer MAE from
`106.121666 K` to `13.324483 K`. The best train/support result is
`F2_global_affine`, with corrected MAE `8.501470 K`.

## Inferred

A large fraction of the TSWFC2 temperature discrepancy appears systematic and
low-dimensional rather than arbitrary sensor noise. A uniform or shared-scale
correction transferring from Salt1/Salt2 to Salt3/Salt4 suggests the residual
may represent a stable 1D/3D temperature-reference, wall/bulk reduction,
source/sink distribution, or material/source-property mismatch.

The most flexible reduced family scored here still has only four degrees of
freedom, much lower than the prior per-leg affine upper-bound diagnostic. That
supports using empirical correction screens as discrepancy-localization tools.

## Caveats

This is not final predictive admission. The TSWFC2 source package remains
`not_admitted_no_grid_expansion`, with source/property and numerical gates
blocked. Salt3/Salt4 are legacy validation/holdout-style stress rows here, not
released external-test evidence. No val_salt2 external-test row is scored.

Transfer rows were not allowed to refit coefficients or select the final model.
The transfer ranking is reported as score-only diagnostic evidence.

## Next Useful Actions

1. Run or harvest a compatible runtime-legal Fluid external-BC multi-split
   sensor table so the same reduced families can be tested under the current
   Phase C/D/E external-boundary path rather than cross-artifact TSWFC2 rows.
2. Treat `F1_global_offset` and `F2_global_affine` as the first candidate
   thesis explanations because they are the lowest DOF and transfer well.
3. Use `F5` as an upper reduced-DOF diagnostic bound, not as the default
   closure, because it adds heat-family offsets and therefore needs stronger
   physical ownership evidence.
4. Investigate whether the global offset/multiplier maps to source-property
   choices, wall/bulk reduction, sensor-map reference location, or a stable
   thermal source/sink distribution discrepancy.
