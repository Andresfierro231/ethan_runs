---
provenance:
  - registry/salt2/native_2d_cfd_external/salt_test_2/val_salt_test_2_coarse_mesh_laminar/aggregates/postprocessing.sqlite
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/val_salt2_section_heat_loss_ledger.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_map_scientific_review_and_junction_corner_state/corner_pressure_drop_evidence_state.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
tags: [val-salt2, external-test, heat-ledger, pressure-k, admission]
related:
  - .agent/status/2026-07-17_AGENT-483.md
  - .agent/journal/2026-07-17/val-salt2-training-readiness-and-corner-k-unlock.md
task: AGENT-483
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# val_salt2 Training Readiness and Corner-K Unlock

## Main Conclusions

- `val_salt2` now has a patch-level wallHeatFlux ledger from the existing registry aggregate database. The patch ledger has `69` entities and reconciles to the July 15 section ledger with maximum latest residual `3.451e-07 W`.
- The `val_salt2` junction/stub split closes to the aggregate junction loss: `40.926087 W` across four physical buckets.
- This makes `val_salt2` training-quality as an evidence artifact, but it is **not admitted as training input** under the AGENT-481 split policy. It remains external-test/blind-validation evidence unless explicitly reclassified later.
- Pressure corner K remains diagnostic. Current rows have `0` fit-admitted entries. True centerline straight-loss subtraction over-subtracts the preserved corner rows, all current pressure-map branch rows are recirculation-blocked, and the evidence is coarse/no-GCI.

## Files

- `val_salt2_patch_heat_ledger.csv`: patch-level wallHeatFlux latest and terminal-window values.
- `val_salt2_section_reconciliation.csv`: patch sums compared with the July 15 section ledger.
- `val_salt2_junction_split_heat_ledger.csv`: four-bucket junction/stub split.
- `val_salt2_training_admission_gate.csv`: explicit external-test/training guardrail.
- `pressure_corner_k_admission_table.csv`: joined K, tap-length, recirculation, and pressure-definition admission status.
- `pressure_corner_k_unlock_queue.csv`: minimum evidence needed to turn diagnostic K into admitted component K.
- `val_salt2_pressure_map.csv`: streamwise pressure-map rows used by `pressure_loop_map_val_salt2.svg`.
- `heat_loss_junction_split_by_case.svg`, `corner_k_diagnostic_by_case.svg`, `pressure_loop_map_val_salt2.svg`: quick-look plots.

## Scientific Critique

The heat ledger is now strong enough for external validation scoring because it uses realized `wallHeatFlux` targets only and preserves BC/source/material provenance. It is not a runtime input contract for a predictive model.

The corner-K evidence is internally useful but not a closure coefficient. With mesh-centerline tap distances, the adjacent straight-loss subtraction exceeds the preserved total feature pressure loss, producing negative local centerline K for the preserved corner rows. That is a diagnostic warning about the current tap/straight-reference construction, not evidence that physical corner K is negative.

## Do Not Do

- Do not fit or tune on `val_salt2` while it is labeled external-test only.
- Do not submit duplicate pressure ladder jobs from this package.
- Do not promote corner K into the 1D model until the unlock queue gates pass.
