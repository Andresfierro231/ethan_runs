# Thermal Control-Volume Admission Review

Generated: `2026-07-09T17:58:17`

## Scope

This package compresses the July 9 canonical observation table into
thermal-control-volume admission rows. It is a review/index package, not a new
OpenFOAM extraction and not a fit promotion.

## Outputs

- `thermal_control_volume_admission.csv`: detailed evidence rows from sampled
  OpenFOAM planes and physical-interface enthalpy residuals.
- `thermal_thesis_evidence_table.csv`: compact case/control-volume-class table
  suitable for thesis validation notes.
- `summary.json`: counts and source paths.

## Counts

- Detail rows: `66`
- Thesis evidence rows: `9`
- Admission verdicts: `{'validation_only_defensible_cv_reviewed': 6, 'validation_only_not_bracketed': 3, 'validation_only_partial_bracket': 6, 'validation_only_recirc_contaminated': 21, 'validation_only_sampled_interface_no_residual': 30}`
- Recirculation-contaminated detail rows: `21`
- Radiation-present detail rows: `0`

## Interpretation

All rows remain `fit_eligible=no`. Heater and cooler/reducer rows are usable as
thermal validation evidence where bracketing is explicit, but recirculation,
partial bracketing, and missing model-specific thermal predictions prevent fit
promotion. Junction evidence is mostly sampled-interface diagnostics unless
separate residual assignment exists.

Radiation remains absent in the current OpenFOAM outputs; this package carries
no inferred radiation term.
