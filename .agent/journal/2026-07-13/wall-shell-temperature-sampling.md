# Wall-Shell Temperature Sampling

- date: 2026-07-13
- agent role: Coordinator / Implementer / Tester / Writer
- task ID: TODO-PRED-WALL-SHELL-SAMPLE
- branch or worktree: existing dirty worktree; unrelated prior changes left untouched

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/segment_reduction_inputs.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/README.md`
- `tmp/2026-06-30_claude_action_items/recon_salt2_of13/7915/T`
- `tmp/2026-06-30_claude_action_items/recon_salt2_of13/constant/polyMesh/owner`
- `tmp/2026-06-30_claude_action_items/recon_salt2_of13/constant/polyMesh/boundary`
- corresponding Salt3 and Salt4 reconstructed case files under
  `tmp/2026-06-30_claude_action_items/recon_salt*_of13/`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_TODO-PRED-WALL-SHELL-SAMPLE.md`
- `.agent/journal/2026-07-13/wall-shell-temperature-sampling.md`
- `imports/2026-07-13_wall_shell_temperature_sampling.json`
- `tools/analyze/build_wall_shell_temperature_sampling.py`
- `tools/analyze/test_wall_shell_temperature_sampling.py`
- `tools/analyze/build_wall_layer_drive_mapping.py`
- `tools/analyze/test_wall_layer_drive_mapping.py`
- `work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling/**`
- regenerated
  `work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/**`

## Commands Run

- `python3.11 tools/analyze/build_wall_shell_temperature_sampling.py`
- `python3.11 tools/analyze/build_wall_layer_drive_mapping.py`
- `python3.11 -m py_compile tools/analyze/build_wall_shell_temperature_sampling.py tools/analyze/test_wall_shell_temperature_sampling.py tools/analyze/build_wall_layer_drive_mapping.py tools/analyze/test_wall_layer_drive_mapping.py`
- `python3.11 tools/analyze/test_wall_shell_temperature_sampling.py`
- `python3.11 tools/analyze/test_wall_layer_drive_mapping.py`

## Observed Output

The sampler produced 108 supported patch rows and 21 segment/role reductions.
All supported rows come from reconstructed OF13 cases and use the same
definition:

`T_wall_shell_K = mean(T_internal[owner[boundary_face]])`

The regenerated wall-layer package now has:

- 24 drive rows.
- 72 replay rows.
- 51 executable parity rows.
- 21 blocked rows.
- E0 executable rows: 18.
- E1 executable rows: 21.
- E2 executable rows: 12, limited to passive ambient-wall families.

## Interpretation

This pass removes the mechanical blocker that kept E1 and E2 from running, but
it does not make E1/E2 scientifically successful. The owner-cell wall-shell
proxy gives only a small improvement on passive ambient-wall external-loss
residuals:

- E0 bulk ambient-wall mean absolute residual: about 92.0 W.
- E1 owner-cell wall-shell ambient-wall mean absolute residual: about 89.2 W.
- E2 diagnostic blend ambient-wall mean absolute residual: about 88.3 W.

The E2 same-case beta fit saturates at beta 0 or beta 1 by segment family. That
means the current two-temperature blend is diagnostic only and should not be
used as a validated closure or thesis-strength model. The result points toward
an external-boundary formulation/resistance audit rather than a simple
bulk-versus-owner-cell temperature substitution.

## Radiation Handling

The authoritative current CFD boundary conclusion remains AGENT-287:
`rcExternalTemperature` uses emissivity and `Tsur`, and CFD `wallHeatFlux` is a
total/inseparable heat-flux output. Therefore:

- Setup-level 1D parity should include radiative heat loss if it is recreating
  the CFD boundary condition from `h`, `Ta`, `Tsur`, and emissivity.
- Realized-flux replay modes must not add a separate radiation term on top of
  CFD `wallHeatFlux`.

## Incomplete Lines Of Investigation

- The sampled proxy is the first internal owner cell behind each boundary face,
  not a true solved shell-center or outer-surface temperature.
- The package does not obtain a separate OpenFOAM `qr` field.
- Cooler rows remain source/sink rows without passive external `hA`.
- Junction E2 remains blocked where path-bulk temperature is unavailable.
- The next scientific audit needs the exact `rcExternalTemperature` formula or
  a tiny OF13 microcase varying only emissivity and `Tsur`.

## Next Steps

1. Implement `TODO-FLUID-EXTERNAL-BC-DICT` so the 1D solver can ingest
   patch/segment external BC dictionaries and choose explicit drive-temperature
   selectors.
2. Add a formula-level audit of `rcExternalTemperature`, preferably source-code
   backed or microcase backed, to pin down how wall/layer resistance combines
   with convection and radiation.
3. Produce a paper-facing parity table that reports E0/E1/E2 side by side with
   residuals and states that the owner-cell proxy did not explain the heat-loss
   gap.
