# Wall-Layer Drive Mapping

- date: 2026-07-13
- agent role: Coordinator / Implementer / Tester / Writer
- task ID: TODO-PRED-WALL-LAYER
- branch or worktree: existing dirty worktree; unrelated prior changes left untouched

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/README.md`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/cfd_thermal_boundary_contract.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/span_heat_residuals.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/interface_temperature_samples.csv`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_TODO-PRED-WALL-LAYER.md`
- `.agent/journal/2026-07-13/wall-layer-drive-mapping.md`
- `imports/2026-07-13_wall_layer_drive_mapping.json`
- `tools/analyze/build_wall_layer_drive_mapping.py`
- `tools/analyze/test_wall_layer_drive_mapping.py`
- `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/**`

## Commands Run

- `python3.11 tools/analyze/build_wall_layer_drive_mapping.py`
- `python3.11 tools/analyze/test_wall_layer_drive_mapping.py`
- `python3.11 -m pytest tools/analyze/test_wall_layer_drive_mapping.py`

The `pytest` command failed because `pytest` is not installed. The direct test
harness passed.

## Results

The new package assembles AGENT-263 patch/role/segment boundary rows with July 8
bulk, forward-bulk, recirculation, and wall-temperature support. It writes:

- `external_bc_drive_table.csv`
- `external_bc_replay_modes.csv`
- `section_heat_parity.csv`
- `wall_layer_selector_candidates.csv`
- `blocked_rows.csv`
- `run_metadata.json`
- `README.md`

The final run produced 24 drive rows, 72 replay rows, 18 executable E0 rows,
and 54 blocked rows.

## Observed Output

E0 bulk-drive replay is executable for 18 rows. The passive ambient-wall rows
show large positive loss residuals when segment bulk temperature is used as the
external drive. For example, Salt2 cooling-branch ambient-wall E0 predicts
about 74.9 W external loss against 12.37 W realized CFD external loss, and
Salt4 downcomer ambient-wall E0 predicts about 187.5 W against 28.12 W realized
CFD loss.

## Interpretation

The result supports the current parity ladder: matching `h`, `Ta`, `Tsur`,
emissivity, and patch area is not sufficient if the 1D model drives the
external boundary with segment bulk temperature. Existing `T_fwd_bulk` and
recirculation metadata are now carried forward, but the missing evidence is
still a near-wall shell or other wall-layer drive temperature. E1 and E2 are
therefore blocked by missing `T_wall_shell`, not by a fitted scalar.

The radiation conclusion is carried forward from AGENT-277/287: Ethan CFD has
radiative heat loss through `rcExternalTemperature`, and the available
`wallHeatFlux` is total/inseparable. This package does not double-count
radiation when using realized CFD flux.

## Incomplete Lines Of Investigation

- No new OpenFOAM field sampling was performed on the login node.
- `T_wall_shell` remains unavailable in the assembled artifacts.
- Junction E0 rows remain blocked by missing path bulk temperature.
- Cooler rows remain source/sink documentation rows, not passive hA fit rows.

## Next Steps

1. Stage or extract near-wall shell temperatures for Salt2/3/4 mainline
   `rcExternalTemperature` patches.
2. Rerun `build_wall_layer_drive_mapping.py` so E1 and E2 rows are executable.
3. Keep `TODO-FLUID-EXTERNAL-BC-DICT` open for future first-class Fluid support
   of external boundary dictionaries.
