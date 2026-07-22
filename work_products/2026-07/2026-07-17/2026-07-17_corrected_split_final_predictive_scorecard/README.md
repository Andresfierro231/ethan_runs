---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/salt1_split_ready_manifest.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_admission_decision.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/coupled_admission_review.csv
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv
tags: [forward-model, corrected-split, predictive-scorecard, holdout-policy]
related:
  - final-predictive-split-policy
  - predictive-wall-test-section-submodels
  - salt2-pm5q-holdout
  - val-salt2-external-test
task: AGENT-499
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Corrected-Split Final Predictive Scorecard

## Result

This package implements the corrected final predictive scorecard wrapper:
train/freeze on Salt1-4 nominal, keep Salt2 +/-5Q and `val_salt2` blind, and
leave +/-10Q/new CFD out until terminal/run admission.

No final candidate is admitted here. The existing PB1+cooler coupled evidence is
legacy-split diagnostic evidence only: it was not frozen on Salt1-4 nominal, it
does not include a Salt1 nominal coupled row, and AGENT-494 already rejected all
four candidates because validation/holdout all-probe/TW error regressed versus
M3 despite mdot improvement.

## Counts

- Final training cases: `4`.
- Blind score-only cases: `3`.
- Candidate definitions reviewed: `4`.
- Legacy coupled rows reclassified as diagnostic: `12`.
- Missing Salt1 corrected-freeze rows inserted: `4`.
- Blind holdout/external rows blocked pending final freeze: `12`.
- Future rows blocked pending terminal/run admission: `5`.
- Final admitted candidates: `0`.

## Files

- `split_legal_case_table.csv` states which cases may train, score blindly, or
  remain blocked under the corrected split.
- `candidate_freeze_manifest.csv` records why each existing PB1+cooler candidate
  is not a corrected-split freeze.
- `coupled_scorecard.csv` reclassifies AGENT-494 coupled rows as diagnostic
  legacy evidence and inserts the missing Salt1 nominal rows required before a
  corrected freeze can exist.
- `blind_holdout_scorecard.csv` keeps Salt2 +/-5Q and `val_salt2` score-only and
  blocked until a corrected final freeze exists.
- `admission_gate_review.csv` summarizes candidate-level gates.
- `blocked_future_rows.csv` keeps PM10 and new CFD out of the current scorecard.
- `runtime_input_audit.csv` records leakage guardrails.
- `next_analysis_queue.csv` is the handoff queue for tomorrow's work.
- `source_manifest.csv` and `summary.json` provide provenance and machine-readable
  package state.

## Start Here Tomorrow

Open this README, then `admission_gate_review.csv`, then
`next_analysis_queue.csv`. The shortest path forward is to wait for or consume
the AGENT-498 wall/test-section distribution ladder; only after an actually
admitted wall/test-section/cooler candidate exists should a new task build a
Salt1-4 nominal freeze runner. Do not use Salt2 +/-5Q, PM10, new CFD, or
`val_salt2` for fit or model selection.
