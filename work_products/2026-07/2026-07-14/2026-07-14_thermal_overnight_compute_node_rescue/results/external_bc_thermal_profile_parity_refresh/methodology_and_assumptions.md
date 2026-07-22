# Methodology and Assumptions

## Study Ladder

1. Consolidate the CFD external-boundary and source/sink contract.
2. Preserve patch-level provenance, then form segment-equivalent 1D boundary rows.
3. Compare current best predictive-style 1D heat loss against CFD realized heat
   loss by physical leg.
4. Diagnose whether bulk-temperature external loss drive is plausible using
   existing wall/shell temperature proxies.
5. Classify each result as setup contract, diagnostic-only, blocked, or future
   validation candidate.

## Inputs

- Patch-level CFD boundary table: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`.
- Fluid-ready segment-equivalent external boundary table:
  `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv`.
- Wall-layer drive table: `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv`.
- Best predictive-style heat-loss discrepancy:
  `work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv`.

## Assumptions

- Salt split is fixed: Salt2 trains, Salt3 validates, Salt4 is holdout.
- Realized CFD `wallHeatFlux` can diagnose heat-path placement but cannot be a
  runtime predictive input.
- CFD radiation is embedded in `wallHeatFlux`; it is not separately exported as
  `qr`.
- The current best model is `F1_heater_only`, which still uses imposed cooler
  duty. It is useful for model-form diagnosis, not final predictive-HX scoring.
- Wall-shell temperatures are proxies from existing postprocessing and remain
  diagnostic until a gated forward rerun validates a model form.

## Interpretation Rules

- Pipe-leg over-loss plus junction under-loss means aggregate balance is not an
  adequate success metric.
- Heater, cooler, test section, passive walls, and junction/stub losses must
  remain separate lanes.
- Internal Nu/HTC must not absorb passive external-boundary, radiation, heater,
  cooler, or missing-geometry residuals.
