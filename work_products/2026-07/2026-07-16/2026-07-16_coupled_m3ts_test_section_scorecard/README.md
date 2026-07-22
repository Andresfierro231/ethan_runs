---
provenance:
  task: AGENT-461
  generated_at: 2026-07-16T23:25:00.027465+00:00
  sources:
    - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
    - work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/setup_candidate_summary.csv
    - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/case_mode_error_matrix.csv
    - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/fluid_variant_contract.csv
tags: [forward-model, m3ts, test-section, fluid-role-boundary]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
---
# Coupled M3+TS Test-Section Scorecard

This package implements the M3+TS blocker-removal path up to the compute-node
coupled solve gate.

Implemented:

- Fluid now supports role-local external-boundary rows, so `ambient_wall` and
  `test_section` subspans on `left_upper_vertical` can replace the parent
  upcomer ambient-loss approximation without using realized CFD heat evidence.
- The scorecard builder emits exact role-row scenario contracts for Salt2 train,
  Salt3 validation, and Salt4 holdout.
- Runtime audit passes for the generated scenario contracts.

Decision: `keep_open` for `predictive-wall-test-section-submodels`.

Why: Fluid solves completed, but no candidate has both an admitted coupled gate
and held-out heat-loss gates.

Next required action: Adjudicate coupled mdot/TP/TW thresholds, then improve the
predictive test-section/cooler heat-loss model before rerunning admission.
