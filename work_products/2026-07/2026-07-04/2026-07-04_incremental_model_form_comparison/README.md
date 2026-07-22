# Incremental Model-Form Comparison

Generated: `2026-07-04T09:01:59-05:00`

## What This Package Does

This package reorganizes existing July 1 1D-vs-CFD model-form outputs into an incremental ladder.
It does not run OpenFOAM and does not mutate case data.

## Current Best Evaluated Form

- Best current Salt 2-4 mean |mdot error|: `3.103%` from `fit_major_k90_1p4`.
- This is an mdot-focused compact fit, not a final physical closure law.

## Files

- `incremental_model_form_ladder.csv`: evaluated forms ordered as a one-term-at-a-time ladder.
- `model_form_case_scores.csv`: per-Salt scores for the ladder forms.
- `boundary_sensitivity_ladder.csv`: insulation/radiation sensitivity separated from hydraulic closure form changes.
- `friction_re_only_candidates.csv`: mesh-corrected friction rows for Re-only screening.
- `friction_re_fit_summary.csv`: screen-only log-log f(Re) fits by span/method.
- `missing_model_form_backlog.csv`: model forms not yet fit or not yet supported by data.

## Immediate Interpretation

- The current Re-only/major-only proxy is weak by itself.
- A single global major-loss multiplier explains most current mdot improvement, but it is not yet a defended friction law.
- The joint major-plus-bend fit is the best compact mdot score, but improves only marginally over the best one-parameter major-loss fit and is fitted on only Salt 2-4.
- Per-leg friction, thermal UA', and upcomer-cell terms remain the highest-value next model forms.

## Missing High-Value Forms

- `M1` `per_leg_friction_multiplier`: needs consolidated closure table and uncertainty flags
- `M2` `per_leg_f_of_Re_power_law`: false-steady perturbations cannot be admitted
- `M3` `bend_K_Re_term`: bend K exists for nominal Salt only; perturbation spread is invalid
- `M4` `thermal_UA_prime_term`: external Fluid campaign integration not yet committed
- `M5` `upcomer_recirculation_cell_term`: needs T2/T13 data; current perturbations false-steady
- `M6` `water_family_validation_axis`: Water job still running
