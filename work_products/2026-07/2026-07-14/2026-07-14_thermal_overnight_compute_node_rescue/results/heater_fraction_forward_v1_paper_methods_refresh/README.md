---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_contract_interpretation.csv
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/case_heat_ledger.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/summary.json
tags: [forward-model, boundary-modeling, heater-source, paper-methods]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-390
date: 2026-07-14
role: BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Fraction / Forward-v1 Paper Methods

## Decision

This package implements the repo-local heater/source-contract slice of the
forward-v1 completion plan. Heater-only remains the admitted unfitted source
contract for the next boundary/HX work. A Salt2-only fitted `eta_heater` or
test-section external-loss scalar improves the held-out Tmean score in this
linearized screen, but neither scalar admits final forward-v1 because the
cooler/HX model is still not setup-only.

## Main Results

- Split: `salt_2=train`, `salt_3=validation`, `salt_4=holdout`.
- Runtime-input audit violations: `0`.
- Heater-only held-out mean absolute Tmean error:
  `5.753 K`.
- Salt2-fitted `eta_heater`: `0.989703`;
  held-out mean absolute Tmean error:
  `3.199 K`.
- Salt2-fitted test-section external loss:
  `2.736 W`;
  held-out mean absolute Tmean error:
  `3.612 K`.
- Legacy 37 W test-section source held-out mean absolute Tmean error:
  `34.699 K`.

## Files

- `heater_fraction_scalar_candidates.csv`
- `heater_fraction_split_scores.csv`
- `heater_fraction_model_summary.csv`
- `heater_fraction_decision_table.csv`
- `runtime_input_audit.csv`
- `result_intake_table.csv`
- `claim_limitations_table.csv`
- `figure_table_index.csv`
- `methods_process.md`
- `source_manifest.csv`
- `summary.json`

## Boundaries

This package does not mutate native CFD outputs, registry/admission state,
scheduler state, generated indexes, or external Fluid files. It does not
replace the required setup-only cooler/HX model and does not reopen internal Nu.
