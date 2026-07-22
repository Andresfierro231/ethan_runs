# Wall-Layer Drive Mapping

Generated: `2026-07-13T21:45:52+00:00`
Task: `TODO-PRED-WALL-LAYER`

## Purpose

This package advances the CFD-to-1D external-boundary parity ladder after the
AGENT-263 patch-role table and AGENT-287 radiation correction. It assembles the
available segment bulk and wall-temperature evidence, computes an E0 bulk-drive
external-loss diagnostic, and records why E1/E2 wall-shell modes are not yet
publication-ready.

## Radiation Policy

Ethan CFD should be described as radiation-capable. The admitted Salt
`rcExternalTemperature` rows use emissivity and `Tsur`, and AGENT-277/287 show
those inputs affect total `wallHeatFlux`. The available CFD output has no
separate `qr` ledger, so realized `wallHeatFlux` is a total heat flux. This
package therefore never adds a separate radiation term on top of realized CFD
`wallHeatFlux`.

For the approximate E0 external-BC replay, the table reports convection plus a
Stefan-Boltzmann radiation term using AGENT-263 `h`, `Ta`, `Tsur`, emissivity,
and area. That replay is explicitly marked approximate because the exact
`rcExternalTemperature` source formula is not encoded in the current Fluid API.

## Outputs

- `external_bc_drive_table.csv`: role-level CFD boundary rows joined to
  available bulk, forward-bulk, recirculation, and wall drive temperatures.
- `external_bc_replay_modes.csv`: E0/E1/E2 replay rows with executable/block
  status.
- `section_heat_parity.csv`: E0 loss residuals against realized CFD total
  `wallHeatFlux`.
- `wall_layer_selector_candidates.csv`: inverse-drive and selector diagnostics.
- `blocked_rows.csv`: missing evidence or fit-status blockers for E1/E2 parity.
- `run_metadata.json`: provenance, source paths, command, and row counts.

## Key Counts

- Drive rows: `24`
- Replay rows: `72`
- E0 executable rows: `18`
- Blocked rows: `21`

## Scientific Reading Order

Read `external_bc_drive_table.csv` first to confirm the CFD boundary role,
`hA`, ambient/surroundings temperature, emissivity, realized flux, imposed heat,
and available drive temperatures. Then read `section_heat_parity.csv` for the
bulk-drive residual. E1 rows use the available wall-shell proxy when present.
E2 rows use diagnostic same-family beta fits only for passive rows and remain
blocked for source/sink rows.

## Interpretation

The current forward progress is enough to document the parity boundary:

- patch/role/segment external inputs are assembled from authoritative CFD
  artifacts;
- radiation is treated as present and inseparable in realized CFD flux;
- E0 bulk-drive replay is quantified with paired forward-bulk/recirculation
  metadata where existing interface samples support it;
- E1 wall-shell replay is executable where `T_wall_shell_K` is present;
- E2 blend replay is diagnostic and restricted to low-dimensional passive
  section-family beta fits.

Do not use source/sink roles (`heater`, `cooler`, `test_section`) to fit passive
external `hA`. Keep those terms separated from ambient-wall parity.
