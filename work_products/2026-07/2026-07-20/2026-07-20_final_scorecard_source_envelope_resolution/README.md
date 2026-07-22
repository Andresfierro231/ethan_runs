# Final Scorecard Source-Envelope Resolution

Task: `TODO-FINAL-SCORECARD-SOURCE-ENVELOPE-RESOLUTION`

This package resolves the four fit/model-selection candidate source/property
blockers left by the July 20 source/property refresh. It is evidence-first:
strict pass is allowed only for clean row-specific source-envelope evidence;
otherwise the integration policy demotes the row to no-fit/no-model-selection.

## Result

- Candidate rows resolved: `4`.
- Strict-pass rows: `0`.
- Demoted source-envelope rows: `3`.
- Blocked pending row-specific envelope rows: `1`.
- Final fit-enabled rows after policy: `0`.
- Source/property gate findings after resolution: `0`.

Salt1 remains pending because no row-specific Salt1 branch envelope exists in
the July 13 package. Salt2/Salt3/Salt4 nominal rows are demoted because their
fit-target branches retain outside/unknown and diagnostic/reference source
evidence; label presence is not enough for final fit or model-selection.

## Next Integration

The next scorecard-builder task should consume
`scorecard_source_property_resolution_policy.csv` and regenerate the final
scorecard shell so `fit_allowed` and `model_selection_allowed` follow the
resolved final policy rather than source-label presence alone.
