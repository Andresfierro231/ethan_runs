# ROM Post-Processing Correctness Validation

Date: `2026-07-01`
Task: `AGENT-165`
Role: Coordinator / Implementer / Writer

## Request

Implement the plan for validating ROM and post-processing correctness without
waiting on long OpenFOAM compute.

## Coordination

This task intentionally avoids AGENT-162-owned extractor files. It consumes
existing work products and publishes a new validation package.

## Planned Outputs

- reusable builder script in `tools/analyze/`
- focused unit tests
- dated `work_products` tables
- dated report package

## Work Completed

Added `tools/analyze/build_rom_postprocessing_correctness_validation.py`, which
consumes existing outputs only:

- `work_products/2026-07-01_claude_mesh_centerlines/**/mesh_stations.json`
- `work_products/2026-07-01_claude_section_mean_pressure/section_mean_pressure_*.json`
- `work_products/2026-07-01_claude_segment_friction/segment_friction.json`
- `work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.json`

Generated:

- `geometry_reference.csv`
- `pressure_friction_audit.csv`
- `thermal_sign_identity_audit.csv`
- `closure_observations.csv`
- `model_form_specs_seed.json`
- `summary.json`
- report `README.md`

The pressure/friction audit explicitly marks rows with negative apparent
friction as `not_direct_friction` and requiring variable-density buoyancy
correction before fitting. Thermal rows include `UA' = hP` identity error and a
sign-convention audit class.

## Follow-Up Extension: Resistance Mental Model

After the first implementation, Ethan asked whether the package considered the
mental model for different resistances, friction, flow development, and
buoyancy. Extended the builder and regenerated outputs so the mental model is
first-class data, not only report prose.

Added columns:

- pressure/geometry/observation taxonomy:
  `resistance_class`, `physics_role`, `development_state`, `buoyancy_role`,
  `closure_admissibility`
- thermal taxonomy:
  `thermal_resistance_class`, `rom_energy_role`, `nu_admissibility`

Added `resistance_taxonomy_catalog.json` with 8 reusable categories:

- `buoyancy_drive`
- `distributed_wall_friction_candidate`
- `minor_loss_or_development_region`
- `reversible_acceleration_area_change_diagnostic`
- `buoyancy_contaminated_apparent_resistance`
- `recirculation_cell_effective_resistance`
- `thermal_resistance_UAprime`
- `unresolved_residual`

The report now includes a `Loop Resistance Mental Model` section with the ROM
pressure-balance decomposition and the thermal-resistance analogue.

## Validation

Planned:

- unit tests for pure helper functions;
- run the builder on existing July/June outputs;
- inspect generated summary and report.

Completed:

- `python3.11 -m pytest ...` failed because `pytest` is not installed for
  `python3.11`.
- `python3 -m pytest tools/analyze/test_rom_postprocessing_correctness_validation.py -q`
  passed: 12 tests after taxonomy extension.
- `python3 tools/analyze/build_rom_postprocessing_correctness_validation.py`
  succeeded.
- Generated counts: 90 geometry rows, 36 pressure/friction rows, 9 thermal rows,
  333 closure-observation rows, 6 model-form specs, 8 resistance-taxonomy classes.
- Taxonomy distributions:
  - pressure rows: 12 `buoyancy_contaminated_apparent_resistance`, 6
    `distributed_wall_friction_candidate`, 18
    `reversible_acceleration_area_change_diagnostic`
  - thermal rows: 3 `thermal_resistance_UAprime`, 3
    `recirculation_cell_effective_thermal_resistance`, 3
    `thermal_resistance_unavailable`

No OpenFOAM, Slurm, or heavy solver commands were run.
