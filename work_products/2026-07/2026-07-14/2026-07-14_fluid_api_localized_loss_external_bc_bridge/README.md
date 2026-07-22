---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/fluid_external_boundary_patch_plan.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
tags: [fluid, external-boundary, localized-loss, hydraulic]
task: AGENT-318
date: 2026-07-14
role: Implementer/Tester/Writer
status: complete
---
# Fluid API Localized Loss And External Boundary Bridge

## Implemented

- Added config parsing and scenario record export for:
  - `friction_form`
  - `friction_multiplier_by_parent_segment`
  - `ri_table`
  - `external_boundary_h_by_parent_segment`
  - `external_boundary_ambient_temperature_by_parent_segment`
  - `external_boundary_surroundings_temperature_by_parent_segment`
  - `external_boundary_emissivity_by_parent_segment`
  - `external_boundary_source_by_parent_segment`
  - `external_boundary_drive_selector_by_parent_segment`
- Extended `outer_closure_mode` to allow `external_boundary_table`.
- Wired per-parent external boundary h/Ta/Tsur/emissivity overrides into
  `wall_and_insulation_resistances_per_length()` for passive setup-parity mode.
- Propagated external-boundary source/drive/Ta/Tsur/emissivity/h diagnostics
  into segment state and segment CSV output.
- Added config-loader support for `localized_fixed_k_by_segment` in minor-loss
  presets. The solver already applied localized fixed K per resolved segment or
  distributed parent fraction; this makes the path YAML-reachable.
- Documented the new knobs in the Fluid README.

## Boundaries

- This is API support and focused unit coverage, not a full campaign rerun.
- No native CFD solver outputs were mutated.
- The realized CFD `wallHeatFlux` replay policy remains separate: do not add
  radiation again to realized-flux replay rows.
- External-boundary fields are opt-in; default scenarios preserve old behavior.
- Localized K is separate from legacy bend K and from the major-loss multiplier.
  No one global multiplier was introduced or exported.

## Tests

- `python3.11 -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py`
- `python -m unittest tests.test_solver_contracts.SolverContractTests.test_config_loader_parses_friction_and_external_boundary_fields tests.test_solver_contracts.SolverContractTests.test_minor_loss_preset_parses_localized_fixed_k tests.test_solver_contracts.SolverContractTests.test_external_boundary_override_changes_target_segment_only tests.test_solver_contracts.SolverContractTests.test_scenario_config_defaults_match_active_solver_contract`

The broader `python -m unittest tests.test_solver_contracts` was started and
interrupted after progressing through many existing solve-case tests without
observed failure; it was in the pre-existing slow profile-descriptor solve path
when interrupted.
