---
provenance:
  task: AGENT-355
  generated_by: tools/analyze/build_salt_training_promotion_and_legacy_perturbation_audit.py
tags: [cfd-pp, salt, training-data, admission, perturbation, boundary-conditions]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md
---
# Salt Training Promotion And Legacy Perturbation Audit

## Observed Facts

- Salt1 nominal, lo10q, and hi10q have terminal harvest evidence in `work_products/2026-07/2026-07-13/2026-07-13_salt1_terminal_harvest_admission_review/admission_decision_table.csv` and final-window steady labels in the submitted-run table.
- Salt2/Salt4 +/-5Q perturbed-Q rows from harvest job `3295437` have completed terminal harvest, registered aggregates, and heat-role reductions in `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv` and `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv`.
- The user-requested split override is encoded here: Salt2 +/-5Q are holdout rows; Salt4 +/-5Q and Salt4 nominal are training rows.
- Legacy `hiins` names are not reliable physics labels. The June 19 manifest records `mutation_profile=hiQ_balQ_baselineIns` and `insulation_delta_in=0.00` for `salt3_jin_hiq_hiins` and `salt4_jin_hiq_hiins`.
- `salt3_jin_hiq_hiins` is not training-ready: it is heat-drifting in the joined steady-state table and failed the older operating-point movement gate.

## Inferred Interpretation

- Salt1 can now be used for training/correlation support under the dated Salt1 policy override captured in `salt1_training_admission_package.csv`, but `salt1_jin_hi10q_corrected` still needs curator signoff because older inventory evidence conflicts with the terminal-harvest review.
- Salt4 nominal is no longer holdout in this package. It is a training row by user policy; future holdout data must be collected separately.
- Salt4 legacy `balq`/`hiins` rows are useful sensitivity evidence, but the trustworthy label is Q/cooling perturbation with baseline insulation unless an actual terminal case dictionary proves otherwise. Last-window flatness alone does not erase the prior false-steady operating-point gate.

## Math And Gate Assumptions

- Perturbed-Q labels use `q_ratio = Q_case / Q_nominal`.
- A row can be terminal-harvested and still not fully admitted: admission also requires boundary-condition labels, registered postprocessing aggregates, an operating-point/steady-state gate, and split-policy assignment.
- `wallHeatFlux` for `rcExternalTemperature` patches includes the radiation semantics available to OpenFOAM in the total heat flux; no separate predictive `qr` runtime target is created here.

## Usable Now

- Training: Salt4 nominal, Salt4 +/-5Q perturbed-Q thermal closure rows, Salt1 nominal and Salt1 lo10q under caveats.
- Holdout: Salt2 +/-5Q perturbed-Q thermal closure rows, with leakage guardrails.
- Not yet fit-use: Salt1 hi10q until the failed/not-admissible conflict is resolved; Salt3 hiq/hiins; legacy Salt4 balq/hiins unless the operating-point gate is explicitly overridden.

## Perturbed +/-5Q Full Workflow Status

The +/-5Q rows have terminal harvest and thermal postprocessing. They have **not** completed matched pressure/upcomer metric extraction. The current matched-plane runner does not include the harvested +/-5Q cases, so this package does not submit a misleading job. The exact blocker and next command/workflow action are in `matched_pressure_upcomer_workflow_readiness.csv`.

## val_salt_test_2_coarse_mesh

Documentation is ready at `work_products/2026-07/2026-07-14/2026-07-14_val_salt_test_2_coarse_mesh_documentation/README.md` and includes alias migration, BC/property evidence, and the Salt2 Jin comparison.

## Files

- `salt1_training_admission_package.csv`
- `pm5_perturbed_q_split_override.csv`
- `salt_training_split_override.csv`
- `legacy_perturbation_label_audit.csv`
- `salt3_hiq_hiins_documentation.csv`
- `matched_pressure_upcomer_workflow_readiness.csv`
- `more_training_data_todo.csv`
- `source_manifest.csv`
- `summary.json`

## Summary

- Rows generated: `32`
- Training rows now allowed by this package: `5`
- Holdout rows now allowed by this package: `2`
- Native CFD outputs mutated: `false`
