---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_diagnostic_cfd_heat_loss_replay_and_predictive_loss_plan/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [thermal-parity, forward-v1, fluid-api, heat-loss, setup-only]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-418
date: 2026-07-15
role: Forward-pred/BC-modeling/Fluid API/Implementer/Tester/Writer
type: journal
status: complete
---
# Setup-Predictive Heat-Loss Fluid Variant

## Why This Exists

AGENT-410 converted the forced CFD-realized heat-loss replay into a report-ready
diagnostic and proposed a setup-predictive variant. The user then asked to
implement that 1D variant. The implementation needed to preserve the scientific
guardrail: use setup quantities only, not realized CFD `wallHeatFlux`, CFD mdot,
imposed CFD cooler duty, or validation temperatures at runtime.

## Implementation

External Fluid now has an active setup-only external-boundary heat-loss mode:

- `outer_closure_mode: external_boundary_table`
- `external_boundary_h_by_parent_segment`
- `external_boundary_ambient_temperature_by_parent_segment`
- `external_boundary_surroundings_temperature_by_parent_segment`
- `external_boundary_emissivity_by_parent_segment`
- `external_boundary_coverage_multiplier_by_parent_segment`
- `external_boundary_drive_selector_by_parent_segment`
- `external_boundary_source_by_parent_segment`

The prior AGENT-413 path parsed h/Ta/Tsur/emissivity/source/drive metadata into
diagnostics. AGENT-418 extends that path so the scenario table changes actual
passive heat loss. The actual ambient-loss calculation now uses per-segment
external Ta when present, applies coverage multipliers for junction/stub or
connector area, and supports bulk, pipe-outer-wall, and outer-surface effective
drive selectors.

## Evidence

The generated dry-run table shows:

- heated bulk drive: `5.02026698217 W`
- heated pipe-outer-wall drive: `4.97417620724 W`
- heated outer-surface drive: `0.948181943603 W`
- junction unit coverage: `0.979822998426 W`
- junction double coverage: `1.95964599685 W`
- heated warmer ambient: `3.83902769225 W`

These are demonstration values only, not forward-v1 admission scores.

## Validation

Passed:

```bash
python3.11 -m unittest tools.analyze.test_setup_predictive_heat_loss_fluid_variant
python3.11 -m unittest tests.test_solver_contracts.SolverContractTests.test_scenario_config_defaults_match_active_solver_contract tests.test_solver_contracts.SolverContractTests.test_config_loader_parses_friction_and_external_boundary_fields tests.test_solver_contracts.SolverContractTests.test_external_boundary_override_changes_target_segment_only tests.test_solver_contracts.SolverContractTests.test_external_boundary_table_affects_actual_ambient_loss tests.test_solver_contracts.SolverContractTests.test_external_boundary_coverage_multiplier_scales_junction_loss tests.test_solver_contracts.SolverContractTests.test_external_boundary_drive_selector_changes_loss_without_cfd_runtime_inputs
python3.11 -m py_compile tools/analyze/build_setup_predictive_heat_loss_fluid_variant.py tools/analyze/test_setup_predictive_heat_loss_fluid_variant.py ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
```

The broad Fluid `tests.test_solver_contracts` module was started and stopped
because unrelated solver-heavy tests exceeded the interactive turn budget.

## Remaining Work

This is an implementation unlock, not a final model admission. Next work should
build declared split scorecards that fit only training rows, score held-out rows
without refit, and compare this setup-only variant against CFD-realized heat
losses as validation targets only.
