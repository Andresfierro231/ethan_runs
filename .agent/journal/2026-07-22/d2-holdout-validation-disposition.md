---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate/d2_score_improvement_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf14_same_qoi_tp_projection_uq_gate/split_claim_matrix.csv
tags: [journal, d2, validation, holdout, diagnostic-only]
related:
  - .agent/status/2026-07-22_TODO-D2-HOLDOUT-VALIDATION-DISPOSITION-2026-07-22.md
  - imports/2026-07-22_d2_holdout_validation_disposition.json
task: TODO-D2-HOLDOUT-VALIDATION-DISPOSITION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Sensor-map / Writer / Reviewer / Tester
status: complete
---
# Journal: D2 Holdout/Validation Disposition

## Attempted

Created a narrow audit row and compact package answering the user's D2 question
without running new scoring or touching protected rows.

## Observed

D2 improves diagnostic transfer RMSE from 17.3645293096 K to 10.5253939442 K,
with TP transfer RMSE improving from 13.5673279702 K to 4.38159298515 K. MF14
states validation was not used except as read-only prior transfer context,
holdout was not used, external-test was not used, and no new protected scoring
or correction release occurred.

## Inferred

D2 is best treated as a study-priority and model-layering result. It says TP
projection/thermal development should be handled before TW wall/boundary/source
residual ownership. It does not justify runtime empirical offsets.

## Caveats

The D2 transfer split is not a frozen validation/holdout/external score. A
source-bounded successor must be frozen before any protected score.

## Next Useful Actions

Build a source-bounded bulk-to-TP projection formula with same-QOI projection
UQ, row-specific source/property labels, and a freeze manifest. Then, and only
then, score validation/holdout/external rows.
