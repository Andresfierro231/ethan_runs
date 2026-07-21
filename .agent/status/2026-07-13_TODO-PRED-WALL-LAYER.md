# TODO-PRED-WALL-LAYER Status

- date: 2026-07-13
- role: Coordinator / Implementer / Tester / Writer
- task ID: TODO-PRED-WALL-LAYER
- owner: codex
- current state: COMPLETE

## Scope

Claimed the existing wall-layer drive mapping task and generated a repo-local
diagnostic parity package at
`work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/`.

## Results

- Built `tools/analyze/build_wall_layer_drive_mapping.py`.
- Added `tools/analyze/test_wall_layer_drive_mapping.py`.
- Generated 24 role-level drive rows, 72 E0/E1/E2 replay rows, 18 executable
  E0 rows, and 54 blocked rows.
- Joined existing July 8 interface-temperature samples to include
  `T_fwd_bulk_K`, maximum recirculation ratio, and recirculation status where
  the source artifact supports them.
- Added open follow-on board row `TODO-FLUID-EXTERNAL-BC-DICT` for future
  first-class Fluid external boundary dictionary support.

## Scientific State

The CFD is radiation-capable: `rcExternalTemperature` uses emissivity and
`Tsur`, and realized `wallHeatFlux` is total/inseparable. This pass does not
add radiation on top of realized CFD `wallHeatFlux`.

E0 bulk-drive replay overpredicts passive external loss, confirming that the
next parity blocker is not only `h/Ta/Tsur`; it is the missing near-wall shell
or wall-layer drive temperature needed for E1/E2.

## Validation

- `python3.11 tools/analyze/build_wall_layer_drive_mapping.py`
- `python3.11 tools/analyze/test_wall_layer_drive_mapping.py`

`python3.11 -m pytest tools/analyze/test_wall_layer_drive_mapping.py` could not
run because `pytest` is not installed in this environment.

## Next Step

Open a new extraction task to stage derived near-wall shell temperatures for
Salt2/3/4 mainline patches, then rerun this package so E1 wall-shell and E2
blend rows become executable. Forward-bulk and recirculation metadata are
already assembled from the July 8 interface-temperature samples.
