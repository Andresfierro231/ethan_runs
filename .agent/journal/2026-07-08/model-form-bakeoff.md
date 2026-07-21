# Model-Form Bakeoff

Date: `2026-07-08`
Task: `TODO-MODEL-FORM-BAKEOFF`
Role: Implementer / Reviewer
Owner: codex

## Observed Facts

- `work_products/2026-07-08_model_form_bakeoff/` now exists.
- The package consumes the canonical closure observation table and existing
  model-form outputs.
- Scores are split into mdot, pressure-distribution, and thermal-state mismatch
  axes.
- F3 Shah apparent is the current mdot leader; F5 is currently the same result
  in the admitted dataset.

## Inferred Interpretation

The model-form comparison is no longer a raw per-task CSV comparison. It is
anchored to the observation contract, but it still needs external model reruns
before thermal scores can become model-specific.

## Blockers

- No fresh external Fluid runs were performed in this row.
- Thermal score is currently a CFD residual diagnostic shared across forms.
- Corrected Salt and mesh uncertainty remain excluded work in progress.

## Files Used

- `work_products/2026-07-08_closure_observation_table/closure_observations.csv`
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-08_postprocessor_summary_charts/tables/heat_enthalpy_residual_summary.csv`
- `tools/analyze/build_model_form_bakeoff_from_observations.py`
- `tools/analyze/test_model_form_bakeoff_from_observations.py`

## Recommended Next Action

Use this package to define the external Fluid rerun output schema, not as the
final bakeoff.
