# Salt 2 Internal Technical Report Brief

Generated from the current Salt 2 case-analysis package without regenerating the underlying extraction.

## Purpose

This brief is the smallest report-facing companion to the current Salt 2 package in
`reports/2026-06-10_ethan_salt2_case_analysis_package/`. It is written for internal
technical use, with enough detail to feed later report or manuscript drafting.

The brief makes only three claims:

1. The repaired loopwise coordinate is now good enough to compare shear-based and
   direct wall-`p_rgh` major-loss views on one common span coordinate.
2. The late-tail wall-heat accounting gives a stable first answer to
   "where is the heat going?" in the current Salt 2 continuation.
3. The streamwise thermal package is useful as an effective, support-gated indicator
   of loopwise transfer structure, but not yet as a clean intrinsic local HTC result.

## Canonical inputs

- Package meaning and provenance:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/README.md`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/summary.json`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/analysis_manifest.json`
- Hydraulic summary table:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/major_loss_summary.csv`
- Feature-budget caveat table:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/feature_minor_loss_summary.csv`
- Heat summary:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/heat_loss_summary.json`
- Context and interpretation boundary:
  - `journals/2026-06/2026-06-10_ethan_runs.md`
  - `reports/2026-06-09_ethan_steady_state_heat_flow_audit/README.md`

## Current technical findings

### Hydraulic comparison

The direct wall-pressure comparison is now on the same repaired streamwise bins as the
existing shear-based reduction. That is the key report-path improvement: the hydraulic
comparison is no longer mixing different coordinates or different retained windows.

The current span-mean comparison from `major_loss_summary.csv` is:

| Span | Shear `dp/ds` [Pa/m] | Direct `p_rgh` `dp/ds` [Pa/m] | Shear `f_D` | Direct `f_D` |
| --- | ---: | ---: | ---: | ---: |
| lower_leg | 13.24 | 8.20 | 0.892 | 0.466 |
| right_leg | 16.50 | 17.42 | 1.123 | 1.150 |
| left_lower_leg | 18.68 | 17.79 | 1.275 | 1.328 |
| test_section_span | 19.51 | 18.53 | 0.944 | 0.787 |
| left_upper_leg | 14.04 | 25.28 | 0.961 | 1.938 |
| upper_leg | 13.60 | 59.27 | 0.943 | 4.036 |

Interpretation:

- `right_leg`, `left_lower_leg`, and `test_section_span` show the strongest agreement.
- `lower_leg` is directionally consistent but still lower in the direct `p_rgh` view.
- `left_upper_leg` and especially `upper_leg` still diverge materially. These spans
  should remain open technical issues, not settled report evidence.

### Heat partition

At the current late tail (`7506 s`), the package heat summary reports:

- heater input: `+244.64 W`
- cooling branch removal: `-136.35 W`
- junction losses: `-40.94 W`
- downcomer losses: `-22.14 W`
- upcomer losses: `-19.19 W`
- upper transport losses: `-11.83 W`
- test-section losses: `-7.31 W`
- lower transport losses: `-6.36 W`
- net total closure: about `+0.23 W`, or `0.09%` of heater input

Interpretation:

- The late-tail wall-heat balance is tight enough to support a first report statement
  about where the injected heat goes.
- The cooling branch is the dominant explicit sink.
- Junction losses are the next nontrivial recurring sink after the cooling branch.
- The ambient-style proxy remains useful as a diagnostic partition, not as an extra
  independent conservation term.

### Streamwise thermal status

The June 10 package now includes matched streamwise thermal reductions on the shared
retained window `7483-7487 s`, with thermal support masking and explicit QC.

Interpretation boundary:

- The primary thermal curves are suitable for discussing where transfer is strong,
  weak, heating, or cooling along the loop.
- They are not yet clean enough to be written up as intrinsic local HTC coefficients.
- The thermal QC figure is part of the evidence, not an appendix-only artifact,
  because it shows where interpretation is intentionally withheld.

## Required caveats

- `profile_dp_pa` remains unsampled directly; feature `wall_dp_pa` is still inferred
  from adjacent major-span gradients.
- `flow_direction_sign_hint` remains a manual profile assumption used to align
  streamwise flux with the local span coordinate. The current pipeline does not
  infer or independently validate direction automatically.
- Hydraulic diameter and flow area remain geometry surrogates derived from wall area
  per unit length using a circular-perimeter approximation.
- The direct hydraulic comparison is based on wall-area-averaged `p_rgh`, not a
  volume-centerline probe. It is a wall-registered pressure-drop diagnostic.
- No major-loss spans are quarantined now, but every span remains `warning_heavy`.
- Negative-residual features `corner_lower_left`, `corner_lower_right`, and
  `corner_upper_left` remain reference-budget caveats, not settled negative-loss
  physics.
- Heat validation still lags the live heat tail: the current package extends to
  `7506 s`, while the reused direct-validation reference still ends at `3871 s`.
- If local HTC or `UA'` is mentioned, it must stay in effective,
  support-filtered language.

## Recommended next report use

- Use the loopwise hydraulic comparison figures as the headline technical result.
- Use the heat-loss summary figure as the headline thermal-balance result.
- Use the thermal support-QC figure only to define the safe interpretation boundary
  for the streamwise thermal products.
- Keep the current brief aligned with the package-level caveats until a fresh Salt 2
  reviewer pass closes the remaining hydraulic and thermal open items.
