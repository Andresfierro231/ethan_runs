# Exact-File Implementation Plan

## Scope

Implement Phase C in the external Fluid repo only after the Phase C row is
updated with exact paths and external write approval is granted.

## Files To Claim

1. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/external_boundary.py`
   - Add the parser/API module.
   - Public functions:
     - `load_external_boundary_dictionary(path, *, case_id, segment_map, source_label=None)`.
     - `external_boundary_rows_to_scenario_role_rows(records, segment_map)`.
     - `validate_external_boundary_records(records)`.
   - Public dataclass:
     - `ExternalBoundaryRecord`.
   - Parser source of truth:
     - `fluid_external_boundary_runtime_dictionary.csv` fields from this package's source contract.

2. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
   - Add optional scenario YAML fields:
     - `external_boundary_dictionary_path`
     - `external_boundary_dictionary_case_id`
     - `external_boundary_segment_map`
   - Resolve paths relative to `FLUID_ROOT`.
   - Convert loaded dictionary rows into `external_boundary_role_rows`.
   - Preserve existing inline `external_boundary_role_rows`; either append loaded rows after explicit validation or reject duplicates with an actionable error.

3. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
   - Add `_validate_external_boundary_contract(scenario, segments)`.
   - Call it from `solve_case` near `_validate_upcomer_exchange_contract`, `_validate_axial_mixing_contract`, and `_validate_tswfc2_contract`.
   - Validate known parent segments, supported modes, finite nonnegative conductance/area/coverage, supported drive selectors, and no forbidden runtime fields.
   - Extend `_external_boundary_role_loss_for_segment` to separate convective and radiative role contributions or expose explicit lane fields in diagnostics if lane-level reporting is added.

4. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
   - Document that measured validation temperatures, realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, and residual fills are forbidden runtime inputs.
   - Document replay total heat as diagnostic-only and mutually exclusive with predictive radiation/convection.

5. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_external_boundary_contract.py`
   - New parser/API tests. Keep them independent from external large output roots.
   - Use temporary CSV fixtures under `tempfile.TemporaryDirectory`.

6. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py`
   - Update only if new `ScenarioConfig` defaults or existing contract assertions change.

## Files Not To Claim By Default

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/scenarios.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/campaigns.yaml`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/outputs_tamu_loop_v2_resumable/**`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/**`

These are not needed for the first parser/API implementation and are already
dirty in the external repo.

## Acceptance For Phase C

- Parser imports predictive rows and blocked/document-only rows without
  fabricating missing fields.
- Predictive rows produce Fluid role rows with setup-only fields.
- Forbidden runtime fields are rejected by name and by policy labels.
- `pytest tests/test_external_boundary_contract.py tests/test_solver_contracts.py`
  passes from `../cfd-modeling-tools/tamu_first_order_model/Fluid` if the
  external worktree state is coordinated.
- No solver/postprocessing/campaign run is required for Phase C.
