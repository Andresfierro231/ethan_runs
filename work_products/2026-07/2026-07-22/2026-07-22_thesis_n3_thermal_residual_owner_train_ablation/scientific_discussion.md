---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s8_s12_thermal_residual_ownership_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_passive_h2_cand001_source_basis_enrichment/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_train_only_external_bc_attribution_freeze_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_empirical_leg_bias_correction_diagnostic/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/summary.json
tags: [thesis, synthesis, publication-evidence, n3]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n1_frozen_runtime_legal_candidate_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n2_upcomer_exchange_qwall_uq_paper_panels/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/README.md
task: TODO-THESIS-N3-THERMAL-RESIDUAL-OWNER-TRAIN-ABLATION-2026-07-21
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer
type: work_product
status: complete
---

# Thesis N3 Thermal Residual-Owner Train Ablation Scientific Discussion

## Observed Evidence

Passive wall and external-boundary evidence show plausible heat-path responses,
while the known heater/source decomposition improves some local residuals and
worsens others. Empirical corrections sharply reduce train residuals, but their
role is diagnostic because they are not source-backed physical closures.

## Interpretation

The useful result is ownership separation. The residual should not be absorbed
into internal Nu or any single ad hoc multiplier. The ablation table documents
which mechanisms are credible enough to discuss and which remain blocked.
