---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_d_smoke_scorecard/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s8_wall_ts_residual_atlas/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/summary.json
tags: [thesis-dossier, forward-model, uncertainty, runtime-leakage]
related:
  - chapter_insertion_matrix.csv
  - claim_boundary_ledger.csv
task: TODO-THESIS-CSEM-UQ-FLUID-READINESS-INTEGRATION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: work_product
status: complete
---
# Caption Bank

## External Boundary Runtime Smoke

Train/support-only runtime smoke for the external thermal-boundary dictionary.
One `salt_2` upcomer ambient-wall row is converted to a Fluid solver role row
and heat-accounted without consuming validation, holdout, or external-test
targets. This demonstrates runtime mechanism readiness, not a predictive score.

## Same-QOI UQ Admission Gate

Same-QOI UQ Phase C admission table showing zero accepted closure/coefficient
rows. The table is thesis-useful because it prevents pressure or thermal
residuals from being hidden in under-supported fitted coefficients.

## Thermal Residual Ownership

Wall/test-section residual atlas for the TW5/TW6 lane. The figure/table should
be captioned as residual attribution and blocker evidence; it should not be
captioned as an admitted wall/test-section closure.

## Upcomer Recirculation Guard

Upcomer onset and exchange evidence showing why ordinary upcomer `Nu`, `f_D`,
and `K` closures remain excluded. The caption should emphasize gate discipline
and the need for low-recirculation/onset anchors before coefficient admission.

## Pressure/F6 Gate Waterfall

Pressure/F6 gate-waterfall summary with zero component-`K`, cluster-`K`, or F6
fits admitted. This supports pressure residual ownership and blocks hidden
global multipliers.
