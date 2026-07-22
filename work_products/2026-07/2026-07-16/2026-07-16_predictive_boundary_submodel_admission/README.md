---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_heater_fraction_forward_v1_paper_methods/heater_fraction_scalar_candidates.csv
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/part5_heating_rmse_summary.csv
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/heater_cooler_model_form_errors.csv
  - work_products/2026-07/2026-07-15/2026-07-15_setup_only_hx_cooler_scorecard_unlock/setup_only_hx_boundary_scorecard.csv
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/fluid_variant_contract.csv
  - work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger/diagnostic_test_section_negative_source_rows.csv
tags: [forward-model, boundary-modeling, blocker-resolution, heater, hx, wall-loss]
related:
  - operational_notes/maps/forward-predictive-model.md
  - .agent/blockers.yml
task: AGENT-454
date: 2026-07-16
role: Coordinator/BC-modeling/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Predictive Boundary-Submodel Admission

Date: 2026-07-16
Task: AGENT-454

## Result

This package applies a split-aware runtime-input admission gate to the broad
`predictive-heater-cooler-wall-submodels` blocker. It uses existing evidence
only and does not mutate native CFD outputs, launch solver/postprocessing jobs,
or edit external Fluid source.

Decision: `supersede_broad_blocker_with_narrow_wall_test_section_blocker`.

## Submodel Decisions

- Heater: `admitted_predictive_boundary_submodel` using `salt2_fit_constant_heater_efficiency`.
  Validation error `0.4909731562 W`, holdout error
  `1.070245015 W`, runtime gate `pass`.
- Cooler/HX: `admitted_predictive_boundary_submodel` using `salt2_fit_constant_UA_bulk_drive`.
  Validation error `2.869104004 W`, holdout error
  `7.502618613 W`, runtime gate `pass`.
- Wall/test-section/passive boundary: `not_admitted_narrow_blocker_required`.
  No setup-only physical wall/test-section loss model is currently scored on
  Salt3/Salt4; existing rows are diagnostic negative-source compatibility
  screens, not predictive boundary proof.

## Blocker Register Action

The broad blocker is superseded by the narrower
`predictive-wall-test-section-submodels` blocker. This is not a final forward-v1
admission: hydraulic/F6, internal-Nu/sign/heat-balance, recirculation, and
mesh/GCI blockers still govern final forward-v1.

After updating `.agent/blockers.yml`, regenerate `.agent/STATE.md`,
`.agent/BLOCKERS.md`, `.agent/catalog.json`, and `.agent/catalog.csv` so the
new narrowed blocker is authoritative.

## Files

- `submodel_admission_summary.csv`
- `heater_scorecard.csv`
- `cooler_hx_scorecard.csv`
- `wall_test_section_scorecard.csv`
- `runtime_input_audit.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`

## Guardrails

- Salt2 is the training row; Salt3 is validation; Salt4 is holdout.
- No realized CFD `wallHeatFlux`, imposed CFD cooler duty, CFD mdot, or
  validation/holdout temperatures are predictive runtime inputs.
- Internal Nu does not absorb heater, cooler, wall, radiation, storage, or
  test-section residuals.
