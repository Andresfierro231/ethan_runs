# Predictive HX Fit

Generated: `2026-07-13T22:02:15+00:00`

This standalone campaign replaces the imposed cooler duty with a declared
low-dimensional HX-duty surrogate for Salt 2-4. It does not edit Fluid source
and does not touch native solver outputs.

## Model Forms

- `HX0_fluid_predictive_airside_hx`: Fluid's existing predictive airside
  epsilon-NTU calculation, no fit.
- `HX1_global_qhx_multiplier_on_fluid_airside`: one global multiplier on the
  `HX0` predicted duty. This is the implemented provisional UA/effectiveness
  surrogate.
- `HX2_direct_UA_multiplier_in_solver`: documented as the cleaner future form,
  but blocked here because this campaign does not claim external Fluid edits.

## Split Policy

Primary split from `TODO-PRED-VALIDATION-SPLIT`: train on `salt_2`, use
`salt_3` for model-selection validation, and reserve `salt_4` as holdout. This
permits only one declared scalar HX/cooler response. Leave-one-out duty-only
scores are emitted as sensitivity checks, not as replacement admissions.

## Primary Score Snapshot

- `F0_current_fluid_sources` `train`: mean abs HX-duty error `0.000 W`, mean abs Tmean error `33.723 K`, mean mdot error `0.007445 kg/s`.
- `F0_current_fluid_sources` `validation`: mean abs HX-duty error `12.916 W`, mean abs Tmean error `44.080 K`, mean mdot error `0.008155 kg/s`.
- `F0_current_fluid_sources` `holdout`: mean abs HX-duty error `31.376 W`, mean abs Tmean error `56.895 K`, mean mdot error `0.009895 kg/s`.
- `F1_heater_only` `train`: mean abs HX-duty error `0.000 W`, mean abs Tmean error `2.322 K`, mean mdot error `0.004633 kg/s`.
- `F1_heater_only` `validation`: mean abs HX-duty error `2.341 W`, mean abs Tmean error `6.534 K`, mean mdot error `0.005655 kg/s`.
- `F1_heater_only` `holdout`: mean abs HX-duty error `17.511 W`, mean abs Tmean error `20.587 K`, mean mdot error `0.007395 kg/s`.

## Files

- `hx_model_forms.csv`: candidate forms, implemented status, and provenance.
- `hx_validation_splits.csv`: primary and leave-one-out split definitions.
- `hx_baseline_predictive_airside.csv`: unfitted Fluid predictive-HX baseline.
- `hx_fit_parameters.csv`: fitted global duty multipliers by split and source
  contract variant.
- `hx_duty_scores.csv`: train/validation cooler-duty scores for all splits.
- `hx_primary_forward_scores.csv`: pressure-rooted forward scores using the
  primary split's predicted HX duty.
- `hx_litrev_gate_reference_audit.csv`: required lit-rev gate references.
- `violations.csv`: strict validation findings; expected to be empty.
- `summary.json`: machine-readable campaign metadata.

## Interpretation Boundaries

The campaign uses CFD/OpenFOAM cooler duty only on declared training rows for
the fitted multiplier and as validation-only scoring evidence elsewhere. It
does not solve heater/test-section transfer, wall/storage residuals, exact
reverse-flow fractions, hydraulic closure quality, or thermal mesh uncertainty.
Some fast-scan rows are flagged as not fully accepted by the current pressure
root validity policy; those flags are preserved in `hx_fit_parameters.csv` and
`hx_primary_forward_scores.csv`. The next clean step is a direct Fluid
UA-multiplier row or an end-to-end score after heater/test/hydraulic gates are
resolved.
