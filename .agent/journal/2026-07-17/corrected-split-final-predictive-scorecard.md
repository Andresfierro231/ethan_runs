---
provenance:
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/coupled_admission_review.csv
  - work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/README.md
tags: [journal, corrected-split, predictive-scorecard, holdout-policy]
related:
  - .agent/status/2026-07-17_AGENT-499.md
  - imports/2026-07-17_corrected_split_final_predictive_scorecard.json
task: AGENT-499
date: 2026-07-17
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Corrected-Split Final Predictive Scorecard

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `.agent/status/README.md`
- `.agent/journal/README.md`
- `.agent/README.md`
- `operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md`
- `work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/salt1_split_ready_manifest.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_val_salt2_external_ledger/val_salt2_external_admission_decision.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/pm10_case_readiness.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission/{scenario_contracts.csv,coupled_scorecard.csv,coupled_delta_vs_m3.csv,coupled_admission_review.csv,README.md}`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_segment_pressure_models/segment_pressure_model_scorecard.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/segment_thermal_model_scorecard.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_upcomer_pipe_cell_hybrid_model/{README.md,upcomer_admission_decision.csv}`
- `work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/sensor_policy_scorecard.csv`

## Files Changed

- Added `tools/analyze/build_corrected_split_final_predictive_scorecard.py`
- Added `tools/analyze/test_corrected_split_final_predictive_scorecard.py`
- Generated `work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/**`
- Added `.agent/status/2026-07-17_AGENT-499.md`
- Added this journal entry
- Added `imports/2026-07-17_corrected_split_final_predictive_scorecard.json`
- Updated `.agent/BOARD.md` own AGENT-499 row status

## Observations

The corrected split is explicit: Salt1 nominal, Salt2 nominal, Salt3 nominal,
and Salt4 nominal are the final training/freeze set. Salt2 +/-5Q and
`val_salt2` are blind score-only rows after a final freeze exists. PM10 and new
CFD remain future candidates.

Salt1 schema promotion is complete, so the previous `admitted_needs_schema_promotion`
label in the canonical split policy is stale for this wrapper. The wrapper
records Salt1 nominal as `ready_schema_promoted`.

The AGENT-494 coupled PB1+cooler rows are useful evidence but not a final
corrected scorecard. They use old train/validation/holdout labels over
Salt2/Salt3/Salt4, lack Salt1 nominal coupled rows, and have no candidate that
passed coupled admission. The wrapper inserts missing Salt1 nominal rows and
marks all four candidates as diagnostic legacy-split evidence only.

## Interpretation

The next final predictive scorecard should not be a rerun of the old
Salt2/Salt3/Salt4 validation split. It needs a new corrected freeze step:
fit/freeze only on Salt1-4 nominal, then score the blind Salt2 +/-5Q and
`val_salt2` rows without tuning. Current evidence cannot admit a final
candidate because both the corrected freeze and the coupled validation gate are
missing/failing.

## Commands Run

- `python3 -m py_compile tools/analyze/build_corrected_split_final_predictive_scorecard.py tools/analyze/test_corrected_split_final_predictive_scorecard.py`
- `python3 -m unittest tools.analyze.test_corrected_split_final_predictive_scorecard`
- `python3 -m json.tool work_products/2026-07/2026-07-17/2026-07-17_corrected_split_final_predictive_scorecard/summary.json`

## Results

Validation passed. The generated summary reports:

- final training cases: `4`
- blind cases: `3`
- candidate count: `4`
- legacy coupled rows reclassified as diagnostic: `12`
- missing Salt1 rows inserted: `4`
- future blocked rows: `5`
- runtime audit failures: `0`
- final admitted candidates: `0`

## Incomplete Lines Of Investigation

AGENT-498 is still the active path for wall/test-section distribution physics.
This package did not inspect or alter that active output scope. It records the
dependency in `next_analysis_queue.csv`.

No PM10 terminal admission was attempted because the PM10 readiness package
still records live/pending job state. No new CFD row was promoted because the
Salt3 Q x insulation matrix remains proposed/not run.

## Next Steps

1. Consume AGENT-498 after completion and decide whether any wall/test-section
   distribution candidate is actually admitted.
2. If and only if a candidate is admitted, create a new assigned task to build a
   Salt1-4 nominal freeze runner.
3. Score Salt2 +/-5Q and `val_salt2` only after that corrected freeze exists.
4. Revisit PM10 and new CFD only after terminal/run admission packages exist.
