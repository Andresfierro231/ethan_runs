# TODO-PRESSURE-TERM-LEDGER Status

Date: `2026-07-08`
Role: Implementer / Tester / Writer
Owner: codex

## Scope

Claimed after completing `TODO-OBSERVATION-TABLE-CONTRACT`. This pass
reconciles the existing AGENT-193/197 pressure ledger with the stricter closure
observation contract and hardens the ledger schema for downstream fitting.

Allowed edit paths are the `TODO-PRESSURE-TERM-LEDGER` paths on
`.agent/BOARD.md`.

## Context Read

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md`
- `.agent/journal/2026-07-01/T1-mesh-centerlines-geometry-refix.md`
- `.agent/journal/2026-07-01/3d-closure-into-1d-predictivity-trial.md`
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`
- `.agent/status/2026-07-07_AGENT-193.md`
- `.agent/status/2026-07-07_AGENT-197.md`

## Completed

- Preserved the AGENT-193/197 de-buoyed momentum identity.
- Changed the output package to
  `work_products/2026-07-08_pressure_term_ledger/`, leaving the July 7 ledger as
  historical output.
- Added fit-ready ledger columns:
  - source case root, source window, mesh level, mesh status
  - station start/end labels and non-fitting station count
  - endpoint `p_rgh`, density, velocity, dynamic head, and total-pressure proxy
  - flow-direction `dp_rgh`, density-gradient buoyancy, and inertial terms
  - distributed mechanical-loss gradient
  - development/reset, minor-loss, recirculation, residual-assignment, and
    no-buoyancy-double-counting policy fields
  - fit/validation eligibility fields aligned with the observation contract
- Regenerated:
  - `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
  - `work_products/2026-07-08_pressure_term_ledger/pressure_term_ledger.json`
  - `work_products/2026-07-08_pressure_term_ledger/summary.json`
  - `work_products/2026-07-08_pressure_term_ledger/README.md`
- Extended `tools/analyze/test_pressure_term_ledger.py` to `14` focused tests.

## Key Results

- `18` rows: Salt 2/3/4 Jin × six spans.
- `12` rows fit-eligible; `6` recirculation spans excluded from fitting.
- `max_abs_residual_fraction_main_legs = 0.0` in the regenerated summary.
- `max_f_debuoyed_round_trip_error = 0.0` versus July 1 `f_corrected`.
- Density-gradient buoyancy is reported separately via
  `gh_drho_dxi_pa_m` / `buoyancy_contribution_pa`; it is not fit as friction.

## Validation

- `python tools/analyze/build_pressure_term_ledger.py`: passed and generated
  the July 8 package.
- `python -m pytest tools/analyze/test_pressure_term_ledger.py -q`: passed,
  `14 passed`.
- `python3.11 -m py_compile tools/analyze/build_pressure_term_ledger.py tools/analyze/test_pressure_term_ledger.py`:
  passed.
- `python3.11 tools/analyze/build_pressure_term_ledger.py`: not usable in this
  shell because the external Fluid import path requires `yaml`, which is not
  installed for `/usr/bin/python3.11`. The default `python` has the needed
  dependencies.

## Status

COMPLETE.
