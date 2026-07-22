---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_1/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_3/validation_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_4/validation_table.csv
tags: [forward-model, empirical-bias, reduced-dof, frozen-transfer]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/README.md
  - .agent/status/2026-07-21_TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-reduced-dof-bias-transfer-screen.md
  - imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json
task: TODO-FLUID-REDUCED-DOF-BIAS-TRANSFER-SCREEN-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Reduced-DOF Bias Transfer Screen

This package reduces the empirical correction layer from the previous per-leg
affine diagnostic into predeclared low- and moderate-DOF families, fits
coefficients on Salt1/Salt2 train/support rows only, and applies the frozen
coefficients unchanged to Salt3/Salt4 legacy validation/holdout-style stress
rows.

No Fluid solve is run here. No external-test row is scored. This is not a final
corrected-split admission because the source package remains
`not_admitted_no_grid_expansion`.

## Headline

- Fit rows: `32`.
- Frozen transfer rows: `32`.
- Best train/support family by corrected MAE: `F2_global_affine`.
- Best frozen-transfer family by corrected MAE, reported score-only:
  `F5_thermal_family_offset_shared_multiplier`.
- External-test rows scored: `0`.

## Open First

- `model_family_dof_ledger.csv`
- `frozen_coefficients.csv`
- `split_metric_scorecard.csv`
- `transfer_summary.csv`
- `split_runtime_leakage_audit.csv`
- `explanation_hypothesis_ledger.csv`
- `source_property_gate_todo.csv` after running the documented
  `tools/agent/source_property_gate.py --warn --todo-out ...` check.
