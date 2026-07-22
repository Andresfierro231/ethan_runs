---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/d2_score_improvement_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/split_claim_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/d2_reuse_boundary.csv
tags: [d2, holdout, validation, qoi-projection, diagnostic-only]
related:
  - .agent/status/2026-07-22_TODO-D2-HOLDOUT-VALIDATION-DISPOSITION-2026-07-22.md
  - .agent/journal/2026-07-22/d2-holdout-validation-disposition.md
  - imports/2026-07-22_d2_holdout_validation_disposition.json
task: TODO-D2-HOLDOUT-VALIDATION-DISPOSITION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Writer / Reviewer / Tester
type: work_product
status: complete
---
# D2 Holdout/Validation Disposition

Decision: `d2_promising_diagnostic_transfer_not_holdout_or_validation_tested`.

D2 is a TP/TW QOI-projection diagnostic model form. It uses train residual
offsets to test whether part of the model error is a bulk-to-probe / sensor-kind
projection effect. It is not a released runtime correction and it has not been
tested as a frozen model on protected holdout, validation, or external-test
rows.

## Current Evidence

D2 has useful diagnostic transfer evidence:

- M3 transfer RMSE: `17.3645293096 K`
- D2 transfer RMSE: `10.5253939442 K`
- reduction: `6.8391353654 K` or `39.3856651307 %`
- M3 transfer TP RMSE: `13.5673279702 K`
- D2 transfer TP RMSE: `4.38159298515 K`
- M3 transfer TW RMSE: `18.980361511 K`
- D2 transfer TW RMSE: `12.5130610954 K`

This supports the modeling sequence: correct or explain TP/bulk projection
first, then diagnose remaining TW wall/boundary/source ownership.

## Has It Been Tested On Holdout Or Validation?

No, not as a frozen predictive model. MF14 records:

- validation: not used; existing D2 transfer values are read-only prior-package
  context;
- holdout: not used;
- external-test: not used;
- new validation/holdout/external scoring: `False`;
- fitting/model selection: `False`;
- runtime temperature release: `False`;
- correction release/admission: `False`.

The word `transfer` in the D2 packet should not be read as protected holdout or
external validation scoring.

## What To Do With D2

Use D2 as a diagnostic layer and study-priority result:

1. Preserve it as evidence that TP projection / thermal development matters.
2. Do not admit the empirical TP/TW offsets as runtime inputs.
3. Use it to justify source-bounded bulk-to-TP projection work with same-QOI UQ.
4. Treat remaining TW residual after D2 as a separate wall/core/source/passive
   boundary ownership problem.
5. Only after a source-bounded D2 successor is specified, freeze it before any
   validation/holdout/external score.

## Guardrails

No new scoring, fitting/model selection, runtime temperature release,
source/property release, coefficient admission, final score, thesis-body edit,
native-output mutation, scheduler action, or residual absorption into internal
Nu was performed.
