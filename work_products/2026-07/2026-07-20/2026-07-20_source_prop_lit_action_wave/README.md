# Source/Property/Literature Action Wave

Task: AGENT-571

This package implements seven bounded source/property/literature progress actions without changing final scorecards, fit admission, model selection, CFD outputs, scheduler state, registry state, Fluid source, analysis tooling, or maps.

## Decisions

- Salt1 remains blocked for fit/model-selection until row-specific branch source-envelope labels exist.
- AMX1 remains diagnostic-only until a literature or setup-only multiplier envelope exists and behavior improves.
- PM10, PM5, and `val_salt2` rows are labelled for validation, holdout, or external score-only use; none are fit/model-selection rows.
- Salt2-Salt4 nominal rows cannot be reclassified as strict-pass source-envelope rows from the current evidence package.
- The thesis literature table is ready as a chapter-facing evidence index, not a fit release.
- Property-mode sensitivity still blocks material-closure fitting from current source-sensitive rows.
- Regression sweep records the current gate state and next validation hooks.

## Artifacts

- `salt1_branch_source_envelope.csv`
- `amx1_multiplier_source_envelope.csv`
- `score_only_source_property_labels.csv`
- `salt2_4_source_envelope_reclassification.csv`
- `thesis_literature_source_envelope_table.csv`
- `property_mode_sensitivity_ledger.csv`
- `source_property_regression_sweep.csv`
- `source_manifest.csv`
- `summary.json`

