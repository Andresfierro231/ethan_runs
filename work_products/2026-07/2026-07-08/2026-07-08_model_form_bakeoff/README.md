# Model-Form Bakeoff From Observations

Generated: `2026-07-08T17:47:32`

## Scope

Starter bakeoff for `TODO-MODEL-FORM-BAKEOFF`. This package consumes the
canonical July 8 observation table and existing 1D model-form outputs. It does
not rerun or edit the external Fluid model.

## Observed Facts

- Observation rows consumed: `423` from `work_products/2026-07-08_closure_observation_table/closure_observations.csv`.
- Model/case score rows: `15`.
- Best current mdot form: `F3_shah_apparent` with mean absolute mdot error
  `2.669%`.
- Thermal residuals are scored separately from mdot and pressure; they are not
  used to fit model coefficients.

## Inferred Interpretation

The current admitted Salt 2/3/4 dataset still favors `F3_shah_apparent` / the
currently-degenerate `F5_ri_corrected` on mdot. `F4_leg_class` over-stiffens the
loop in the existing run. Pressure-distribution and thermal-residual axes expose
why mdot alone is not a sufficient closure score.

## Blockers

- This is a starter bakeoff from existing outputs, not a fresh Fluid rerun.
- Thermal scores are model-form-independent until each model emits comparable
  per-segment heat predictions.
- All rows remain coarse mesh without GCI.
- Corrected Salt perturbations remain work in progress and are excluded.

## Recommended Next Action

Rerun the external Fluid model only after deciding which candidate forms should
emit per-segment pressure and heat predictions in a common schema. Keep pressure
distribution, mdot, and thermal-state mismatch as separate objective columns.
