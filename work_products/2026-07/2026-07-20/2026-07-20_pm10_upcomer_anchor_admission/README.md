---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_salt_pm10_terminal_admission_classification/pm10_terminal_drift.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package
tags: [pm10, upcomer, matched-plane, admission]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Upcomer Anchor Admission

This package classifies the four completed PM10 rows after matched-plane
extraction. It separates ordinary-pipe gates from recirculation-aware use:
recirculation can be usable evidence while ordinary single-stream pipe fitting
remains closed.

## Outputs

- `pm10_upcomer_anchor_classification.csv`: 4 case-level
  PM10 classifications.
- `pm10_fit_model_selection_gate.csv`: explicit split-policy gate for fit and
  model-selection use.
- `pm10_model_use_gate.csv`: lane-specific ordinary-pipe versus
  recirculation-aware use gate.
- `pm10_recirculation_anchor_admission.csv`: recirculation calibration,
  model-selection, and hybrid-validation eligibility.
- `pm10_recirculation_feature_matrix.csv`: plane-level recirculation features
  for recirculation-aware scoring.
- `summary.json`: counts and source paths.

## Current Policy

PM10 rows remain excluded from ordinary-pipe Nu/friction/component-K fitting.
Strong-recirculation rows are admitted as recirculation-regime evidence for
conditional recirculation-aware calibration, conditional recirculation-aware
model selection, and hybrid validation. Runtime-input use still requires a dated
policy update.
