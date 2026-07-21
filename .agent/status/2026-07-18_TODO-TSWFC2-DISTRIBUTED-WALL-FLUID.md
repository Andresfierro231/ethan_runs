---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/summary.json
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [forward-model, wall-fluid-coupling, test-section, fluid-api-contract]
related:
  - .agent/journal/2026-07-18/tswfc2-distributed-wall-fluid-api.md
  - imports/2026-07-18_tswfc2_distributed_wall_fluid_api.json
task: TODO-TSWFC2-DISTRIBUTED-WALL-FLUID
date: 2026-07-18
role: Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TSWFC2-DISTRIBUTED-WALL-FLUID Status

## Objective

Implement the TSWFC2 backup path as a distributed test-section wall/fluid node
API in the Fluid solver, keeping it distinct from the prior single
bulk-to-ambient fallback and preserving temperature-shape scorecard guardrails.

## Changes Made

- Added a disabled-by-default Fluid solver scenario surface:
  `test_section_wall_fluid_mode`, `test_section_wall_fluid_contact_multiplier`,
  and `test_section_wall_fluid_node_rows`.
- Added validation for unsupported modes, bad multipliers, fewer than four
  active rows, unknown parents, invalid normalized fractions, and missing or
  negative setup conductance.
- Added distributed-node ambient-loss replacement on matched spans and
  per-segment TSWFC2 ledgers for node IDs, node count, fluid-to-inner-wall heat,
  wall-conduction heat, external heat, residual, and estimated wall
  temperatures.
- Added config loading/export, focused tests, Fluid README documentation, and a
  Fluid-side journal entry.
- Created
  `work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/`
  with the API change log, node reconciliation, runtime guardrails, validation
  results, next-step handoff, source manifest, README, and summary.

## Validation

- Passed: `python -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py`
- Passed: `python -m pytest tests/test_solver_contracts.py -q -k 'tswfc2 or scenario_config_defaults_match_active_solver_contract'`
- Result: 4 selected tests passed, 45 deselected.
- Extra broad check: `python -m pytest tests/test_solver_contracts.py -q` was
  interrupted after 4:26 with 13 tests passed and no failure summary. It was not
  used as the completion gate.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Ethan registry mutated: no.
- Scheduler action: none.
- Fluid campaign or scorecard launched: no.
- External Fluid edits: yes, limited to the separately claimed Fluid API,
  config, tests, README, and journal paths.
- Ethan `tools/analyze/` edits: none; preflight row avoided those active
  conflict paths.
- Generated docs index refresh: not run during implementation; existing active
  generated-index rows were treated as conflict guardrails.
- Fitting, tuning, model selection, or scientific admission change: none.
- Forbidden runtime inputs introduced: no CFD mdot, realized CFD `wallHeatFlux`,
  imposed CFD cooler duty, or measured TP/TW runtime temperatures.

## Outcome

Complete. The solver now has a dry-validated TSWFC2 distributed wall/fluid API.
The next useful work is a separate smoke-scenario row and later temperature-shape
scorecard; mdot-only improvement is explicitly insufficient.
