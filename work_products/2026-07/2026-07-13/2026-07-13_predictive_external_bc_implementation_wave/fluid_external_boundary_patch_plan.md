---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
tags: [forward-model, predictive-1d, external-boundary, fluid]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md
task: AGENT-297
date: 2026-07-13
role: Implementer/Writer
type: work_product
status: complete
---
# Fluid External Boundary Patch Plan

## Goal

Add an `external_boundary_table` outer-boundary mode to
`../cfd-modeling-tools/tamu_first_order_model/Fluid` that consumes
`cfd_external_boundary_dictionary.csv`.

## Current Fluid Implementation Map

- `tamu_loop_model_v2/solver.py`: `ScenarioConfig` carries `radiation_on`,
  `ambient_loss_model`, `outer_closure_mode`, and per-parent outer multipliers.
- `tamu_loop_model_v2/config_loader.py`: `_scenario_from_mapping()` parses
  scenario fields; `CampaignPlan` already has the pattern for external tables.
- `tamu_loop_model_v2/ethan_coupling.py`: current fixed external-loss replay
  loader for `external_prescribed_segment_loss`.
- `tamu_loop_model_v2/solver.py`: `wall_and_insulation_resistances_per_length()`
  computes internal HTC, wall/insulation/external convection, optional
  linearized radiation, and wall/surface temperatures.
- `tamu_loop_model_v2/solver.py`: `ambient_loss_for_segment()` dispatches
  adiabatic, fixed prescribed loss, HX-zero ambient, or internal resistance
  network losses.
- `tamu_loop_model_v2/solver.py`: `_outer_closure_multipliers_for_segment()`
  currently supports only `baseline` and `per_parent_multiplier`.
- `tamu_loop_model_v2/solver.py` and `reporting.py`: `SegmentState`,
  `_segment_dataframe()`, and `write_case_report()` emit segment-state
  diagnostics.

## Minimal Edit Points

1. Add `ambient_loss_model: external_boundary_table` and do not overload
   `external_prescribed_segment_loss`, which is fixed realized-loss replay.
2. Extend the Fluid scenario/config object with:
   - `outer_closure_mode: external_boundary_table`
   - `external_boundary_table_path`
   - `external_boundary_drive_selector`
3. Add a small loader, preferably `external_boundary.py`, keyed by case plus
   segment/parent/role.
4. Extend `solve_case()`, `pressure_residual()`,
   `solve_temperature_periodicity()`, `march_temperatures()`, and
   `ambient_loss_for_segment()` to pass an optional boundary table alongside
   existing `prescribed_segment_losses_W`.
5. Refactor `wall_and_insulation_resistances_per_length()` to accept optional
   boundary overrides: `h`, `Ta`, `Tsur`, emissivity, added layer resistance,
   and drive-temperature selector.
6. For setup parity, compute passive external loss from `area`, `h`, `Ta`,
   `Tsur`, emissivity, and wall/layer metadata.
7. For realized-flux replay, consume realized `wallHeatFlux` as total heat
   transfer and do not add radiation again.
8. Write segment-state diagnostics that separate convective external loss,
   radiative external loss, imposed source/sink duty, realized replay duty, and
   residual; include `external_Ta_K`, `external_Tsur_K`,
   `external_emissivity`, `table_h_ext_W_m2K`, and boundary source/mode.

## Required Tests

- emissivity `0` removes radiative heat loss;
- changing `Tsur` changes radiative heat loss;
- realized-flux replay does not add radiation;
- missing provenance/path/unit fields fail closed;
- existing `internal_model` and `external_prescribed_segment_loss` modes remain
  unchanged.

## Current Constraint

This `ethan_runs` sandbox has write permission only in `ethan_runs` and `/tmp`,
so this package stops at a Fluid-ready contract and exact patch plan.
