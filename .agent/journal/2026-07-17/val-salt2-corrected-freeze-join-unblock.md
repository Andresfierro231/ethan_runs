---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/corrected_freeze_source_audit.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/val_salt2_external_residual_scorecard.csv
tags: [val-salt2, corrected-freeze, external-score, prediction-join, handoff]
related:
  - .agent/status/2026-07-17_AGENT-508.md
  - imports/2026-07-17_val_salt2_corrected_freeze_join_unblock.json
task: AGENT-508
date: 2026-07-17
role: Forward-pred/cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# val_salt2 Corrected-Freeze Join Unblock

## Why This Exists

AGENT-500 created a complete `val_salt2` external-score target contract but
could not compute residuals because no corrected-split frozen prediction artifact
was admitted. This task implemented the next unblocking layer: audit the freeze
source, preserve the join interface, and make the residual computation reusable
for the first valid frozen prediction CSV.

## Files To Open First

1. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/README.md`
2. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/corrected_freeze_source_audit.csv`
3. `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_corrected_freeze_join_unblock/val_salt2_external_residual_scorecard.csv`
4. `tools/analyze/build_val_salt2_corrected_freeze_join_unblock.py`

## Observed Output

- Freeze status: `freeze_blocked_no_wall_candidate_admitted`.
- Target rows reviewed: `61`.
- Joined/scored prediction rows: `0`.
- Policy-excluded rows: `2`.
- Blocked or missing prediction rows: `59`.
- Score-summary lanes with joined predictions: `0`.

## Inference

The `val_salt2` blocker has narrowed. The missing piece is no longer the target
contract or sensor mapping. It is that AGENT-498 completed the wall/test-section
distribution ladder with `0` admitted wall+HX candidates, leaving AGENT-499 with
no corrected-split final predictive candidate to freeze.

The builder now has a stable `--prediction-csv` path. Tests use a synthetic
corrected-freeze CSV and verify pressure, thermal, and sensor residual metrics,
including TP2/TW10 exclusion. This means the next real freeze can be joined
without redesigning the scoring interface.

## Contradictions Or Caveats

- AGENT-498 has both active-history and completed-output traces, but the current
  board row and package summary agree on the important scientific result:
  coupled rows completed and no candidate was admitted.
- Existing PB1/PB2/PB3 wall candidates are diagnostic or blocked evidence. They
  are not treated as frozen predictions.
- The generated SVGs are interface/status figures. They are not evidence of
  prediction accuracy until a valid `--prediction-csv` is supplied.

## Next Useful Actions

1. Build or admit a corrected-split freeze runner trained on Salt1-4 nominal
   only, after resolving the wall/test-section/cooler candidate blocker.
2. Emit a frozen prediction CSV with `case_key`, `evidence_lane`, `target_id`,
   `prediction_model_id`, and lane-specific prediction columns.
3. Rerun:
   `python3.11 tools/analyze/build_val_salt2_corrected_freeze_join_unblock.py --prediction-csv <frozen_predictions.csv>`
4. Keep `val_salt2` as blind external-test evidence and report residuals only.
5. Continue junction metadata, corner-K repaired extraction, and PM10 terminal
   admission as separate lanes.

## Do Not Do

- Do not tune, fit, select, or reclassify from `val_salt2` residuals.
- Do not use blocked AGENT-498 or AGENT-499 candidates as frozen predictions.
- Do not submit duplicate jobs from this package.
- Do not edit native solver outputs, registry/admission state, generated index
  files, or external Fluid source.
