# TODO-MODEL-FORM-BAKEOFF Status

Date: `2026-07-08`
Role: Implementer / Reviewer
Owner: codex

## Scope

Started the model-form bakeoff from the completed observation table. This pass
does not rerun the external Fluid model; it consumes existing July 7/8 outputs
and separates mdot, pressure-distribution, and thermal-state mismatch scores.

## Completed

- Added `tools/analyze/build_model_form_bakeoff_from_observations.py`.
- Added `tools/analyze/test_model_form_bakeoff_from_observations.py`.
- Generated `work_products/2026-07-08_model_form_bakeoff/**`.

## Observed Facts

- Consumed `423` canonical observation rows.
- Scored `15` model/case rows across five model forms.
- Best current mdot score is `F3_shah_apparent` with mean absolute mdot error
  `2.669%`; `F5_ri_corrected` is currently degenerate with F3.
- `F4_leg_class` remains over-stiff in the existing run with mean absolute mdot
  error `23.804%`.
- Thermal mismatch is carried as a separate CFD validation axis, not as a model
  fit target.

## Interpretation

The bakeoff is now started on the common observation contract. It confirms the
current story: mdot alone favors F3/F5-degenerate forms, while pressure and heat
axes are needed to prevent friction-only overinterpretation.

## Blockers

- This is a starter package from existing outputs, not a fresh external Fluid
  rerun.
- Model-specific thermal scores require each candidate model to emit
  per-segment heat predictions in the heat-ledger schema.
- Mesh/GCI and corrected-Salt perturbation conclusions remain work in progress.

## Validation

- `python tools/analyze/build_model_form_bakeoff_from_observations.py`: passed.
- `python -m pytest tools/analyze/test_model_form_bakeoff_from_observations.py`:
  passed, `2 passed`.

## Recommended Next Action

Choose the next external Fluid rerun schema so each model form emits comparable
pressure and heat segment predictions, then refresh this bakeoff without
changing the observation contract.

## Status

STARTED / STARTER PACKAGE COMPLETE.
