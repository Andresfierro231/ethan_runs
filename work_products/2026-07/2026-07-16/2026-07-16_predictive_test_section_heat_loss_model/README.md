---
provenance:
  task: AGENT-458
  generated_at: 2026-07-16T21:32:25.230926+00:00
  sources:
    - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
    - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/test_section_boundary_form_bakeoff/test_section_model_result_ledger.csv
    - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/test_section_boundary_form_bakeoff/test_section_temperature_probe_summary.csv
    - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/case_mode_error_matrix.csv
tags:
  - predictive
  - test-section
  - heat-loss
  - blocker
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
---

# Predictive Test-Section Heat-Loss Model Admission

AGENT-458 implements the first setup-only test-section heat-loss admission screen for `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`.

## Decision

`predictive-wall-test-section-submodels` remains **open**.

No setup-only physical candidate is admitted. `TS1_salt2_fit_hA_constant_drive_deltaT` is fit on Salt2 only; it has a 4.790662416 W Salt3 validation error and still misses by 45.43047953% on Salt3 and 65.12578464% on Salt4, with holdout absolute error 10.92073801 W. `TS2_salt2_fit_constant_loss_W` behaves similarly, with Salt3/Salt4 percent errors of 46.13737006% and 66.12831651%.

Both physical candidates also lack a solver-coupled M3+TS mdot/TP/TW run. Existing no-loss, negative-source, prescribed-loss, and half-prescribed-loss rows are diagnostic only; they cannot be promoted because they either omit the required physical loss model or consume realized CFD heat evidence.

## Outputs

- `setup_loss_candidates.csv` - Salt2-fit setup-only candidate predictions and held-out W gates.
- `setup_candidate_summary.csv` - per-candidate admission decision.
- `end_to_end_diagnostic_comparison.csv` - existing M2/M3 and boundary-form diagnostics kept separate from admission.
- `runtime_input_audit.csv` - allowed/forbidden runtime input audit.
- `blocker_decision.json` - machine-readable blocker decision.
- `source_manifest.csv` - exact source package paths.

## Next Step

Implement or run a solver-coupled M3+TS path that applies the test-section loss through an external-boundary/resistance-network segment model, not through realized CFD wall heat or validation temperatures. The next package should score Salt3/Salt4 mdot, Tmean, loop delta, and TP/TW errors against M2 and M3.
