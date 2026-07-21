---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [forward-model, wall-fluid-coupling, test-section, fluid-api-contract]
related:
  - .agent/status/2026-07-18_TODO-TSWFC2-DISTRIBUTED-WALL-FLUID.md
  - imports/2026-07-18_tswfc2_distributed_wall_fluid_api.json
task: TODO-TSWFC2-DISTRIBUTED-WALL-FLUID
date: 2026-07-18
role: Implementer/Tester/Writer
type: journal
status: complete
---
# TSWFC2 Distributed Wall/Fluid API

## Attempted

Implemented the backup/parallel TSWFC2 path in the Fluid solver as a
disabled-by-default scenario API. The implementation target was a dry contract
and code contract only: no solver campaign, scorecard, fit, or admission.

## Observed

The prior dry contract already required four distributed wall/test-section nodes
and setup-only inputs. Its node table, however, placed the test-section subnodes
under `left_upper_vertical`. The Fluid geometry exposes `test_section` as its
own parent, so the implementation and new handoff reconcile the nodes as lower
upcomer bracket, lower test-section, upper test-section, and upper upcomer
bracket.

The external Fluid tree already contained related UMX1/external-boundary work in
the same files. Those unrelated dirty changes were left in place and not
reverted.

## Inferred

TSWFC2 now differs from the failed single bulk-to-ambient fallback in two ways:
it requires at least four node rows, and it emits wall-temperature and heat-path
ledgers for matched spans. That is enough for a later scorecard to judge
temperature-shape improvement rather than only mass-flow movement.

## Validation

- `python -m py_compile tamu_loop_model_v2/solver.py tamu_loop_model_v2/config_loader.py tests/test_solver_contracts.py` passed.
- `python -m pytest tests/test_solver_contracts.py -q -k 'tswfc2 or scenario_config_defaults_match_active_solver_contract'` passed: 4 selected tests, 45 deselected.
- A broader `python -m pytest tests/test_solver_contracts.py -q` check was
  interrupted after 4:26 with 13 tests passed and no failure summary. The
  focused dry-contract tests remain the recorded completion gate.

## Caveats

No explicit scenario YAML row or smoke campaign was added. The next row should
declare bounded setup conductances, run one or two smoke cases, and then build a
scorecard that reports TP/TW/all-probe shape metrics before any grid expansion.

## Guardrails

No native solver outputs, registry/admission state, scheduler state, fitted
coefficients, Fluid campaign outputs, scorecard, or forbidden runtime inputs
were changed.
