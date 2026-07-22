# Model-Form Bakeoff From Observations

Generated: `2026-07-09T17:58:16`

## Scope

Refresh bakeoff for `AGENT-247`. This package consumes the canonical July 9
observation table and existing 1D model-form outputs. It does not rerun or edit
the external Fluid model.

## Observed Facts

- Observation rows consumed: `1032` from `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`.
- Model/case score rows: `15`.
- Best current mdot form: `F3_shah_apparent` with mean absolute mdot error
  `2.669%`.
- Recirculation-flagged observation rows consumed: `291`; validator
  policy keeps these out of fit targets.
- Radiation-present observation rows consumed: `0`; current
  table carries explicit no-`qr` semantics.
- Thermal residuals and sampled interface rows are scored separately from mdot
  and pressure; they are not used to fit model coefficients.

## Inferred Interpretation

The current admitted Salt 2/3/4 dataset still favors `F3_shah_apparent` / the
currently-degenerate `F5_ri_corrected` on mdot. `F4_leg_class` over-stiffens the
loop in the existing run. Pressure-distribution and thermal-residual axes expose
why mdot alone is not a sufficient closure score.

## Blockers

- This is a bakeoff refresh from existing outputs, not a fresh Fluid rerun.
- Thermal scores are model-form-independent until each model emits comparable
  per-segment heat predictions.
- All rows remain coarse mesh without GCI.
- Corrected Salt perturbations remain work in progress and are excluded.

## Recommended Next Action

Rerun the external Fluid model only after deciding which candidate forms should
emit per-segment pressure and heat predictions in a common schema. Keep pressure
distribution, mdot, and thermal-state mismatch as separate objective columns.
