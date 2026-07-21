# TODO-PRED-WALL-SHELL-SAMPLE Status

- date: 2026-07-13
- role: Coordinator / Implementer / Tester / Writer
- task ID: TODO-PRED-WALL-SHELL-SAMPLE
- owner: codex
- current state: COMPLETE

## Scope

Claimed the wall-shell follow-on to unblock the E1/E2 wall-layer parity modes.
The pass derived a first near-wall shell proxy from reconstructed OpenFOAM 13
cases without mutating native solver outputs.

## Results

- Added `tools/analyze/build_wall_shell_temperature_sampling.py`.
- Added `tools/analyze/test_wall_shell_temperature_sampling.py`.
- Generated
  `work_products/2026-07/2026-07-13/2026-07-13_wall_shell_temperature_sampling/`
  with 108 patch rows and 21 segment/role reductions.
- Proxy definition:
  `T_wall_shell_K = mean(T_internal[owner[boundary_face]])`.
- Regenerated the wall-layer package so E1 wall-shell replay is executable for
  21 rows and E2 low-dimensional blend replay is executable for 12 passive
  ambient-wall rows.

## Scientific State

The new E1/E2 execution did not close the passive external heat-loss mismatch.
Mean absolute ambient-wall loss residuals are about 92.0 W for E0 bulk, 89.2 W
for E1 owner-cell wall-shell, and 88.3 W for E2 same-case diagnostic blend.
The fitted E2 beta values saturate at 0 or 1 by segment family, so this should
not be interpreted as a validated wall-layer model.

This is useful evidence: the current mismatch is not fixed merely by replacing
segment bulk temperature with the first owner-cell temperature behind the
boundary face. The next phase should audit the external-boundary formula and
resistance/layer interpretation, then implement first-class 1D external
boundary dictionaries without double-counting CFD radiation.

## Validation

- `python3.11 -m py_compile tools/analyze/build_wall_shell_temperature_sampling.py tools/analyze/test_wall_shell_temperature_sampling.py tools/analyze/build_wall_layer_drive_mapping.py tools/analyze/test_wall_layer_drive_mapping.py`
- `python3.11 tools/analyze/test_wall_shell_temperature_sampling.py`
- `python3.11 tools/analyze/test_wall_layer_drive_mapping.py`

Both direct harnesses passed.

## Next Step

Open or continue `TODO-FLUID-EXTERNAL-BC-DICT` so the 1D model can consume
patch/segment external boundary dictionaries with `h`, `Ta`, `Tsur`,
emissivity, wall/layer metadata, area, and drive-temperature selector fields.
Keep radiation active in the 1D external-boundary model for setup-level parity,
but do not add separate radiation to any mode replaying realized CFD
`wallHeatFlux`, because CFD `wallHeatFlux` already contains inseparable
convective plus radiative heat transfer.
