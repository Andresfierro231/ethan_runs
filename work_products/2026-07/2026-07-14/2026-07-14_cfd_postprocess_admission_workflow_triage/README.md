---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/submitted_cfd_run_steady_state_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/stopped_salt2_salt4_pm5q/status_table/selected_corrected_q_status_table.csv
  - jadyn_runs/modern_runs/2026-06-19_ethan_blocker_and_1d_followon_wave/campaign_manifest.csv
tags: [cfd-pp, salt-cfd, postprocessing, admission, split-discipline]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_postprocess_harvest_submission/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/README.md
task: AGENT-347
date: 2026-07-14
role: cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# CFD Postprocessing Admission Workflow Triage

## Observed Facts

- A workflow can be automated as a staged gate: terminal harvest, registered postprocessing, BC role labeling, steady/operating-point admission, then split discipline.
- The seven user-named rows are steady only in the detector sense where the steady table says `steady`; that is not the same as training admission.
- `salt4_jin` is already admitted current mainline evidence but is reserved as holdout, not training.
- The legacy `salt4_jin_hi5q_balq`, `salt4_jin_hiq_hiins`, and `salt4_jin_lo5q_balq` rows are historical/diagnostic unless a future row reopens their evidence contract.
- Corrected Salt2/Salt4 +/-5Q harvest job `3295437` completed and produced registry aggregates plus a terminal status table marking the four +/-5Q corrected rows closure-fit admissible under current coordinator policy.

## Inferred Interpretation

The immediate useful progress is not to train on the historical `balq`/`hiins` names. It is to process the newly harvested corrected-Q +/-5Q rows through BC role reduction, admission-matrix refresh, and split-aware labeling. Perturbations should remain grouped with their baseline unless a dated split policy allows them to expand training.

## Why The Named Rows Are Not Training-Admitted

See `steady_candidate_admission_triage.csv`. In short:

- Salt1 rows need a Salt1-specific admission/split policy before training use.
- `salt4_jin` is holdout by design.
- The Salt4 `balq`/`hiins` rows are legacy/historical and need a reopened evidence contract.

## Hiins/Loins Construction

See `hiins_loins_construction_review.csv`. The June 19 manifest records `salt3_jin_hiq_hiins` as `hiQ_balQ_baselineIns` with `insulation_delta_in=0.00`; that means it should not be treated as a true high-insulation case. There is a report trail, and it supports diagnostic/historical use rather than current fit use.

## Drift Ratio

See `drift_ratio_definition.md`. Ratio means `|a * W| / RMSE_about_trend`: the trend's change across the window measured in units of detrended oscillation amplitude.

## Salt2 Jin Versus Salt2 Val

See `salt2_jin_vs_val_comparison.csv`. `2026-06-01_continuation_candidate` is best displayed in new reports as `val_salt_test_2_coarse_mesh_laminar_continuation`. It is a distinct historical validation/coarse-mesh lineage, not the current `salt2_jin` continuation. The source spelling is `coarse`, not `course`; historical paths are preserved as provenance.

## Process Completed Harvest 3295437

This means: consume the completed postprocessing harvest outputs for Salt2/Salt4 corrected +/-5Q, verify the registry aggregates, run BC labeling/admission/split workflow, and then decide downstream use. It does not mean launch duplicate harvest jobs.

## Outputs

- `workflow_automation_steps.csv`
- `steady_candidate_admission_triage.csv`
- `corrected_q_harvest_3295437_processing_status.csv`
- `hiins_loins_construction_review.csv`
- `salt2_jin_vs_val_comparison.csv`
- `drift_ratio_definition.md`
- `source_manifest.csv`
- `summary.json`

## Summary

- Named triage rows: 7
- Harvested corrected +/-5Q rows ready for workflow processing: 4
- Rows that can expand training immediately without split-policy change: 0
