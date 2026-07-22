---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_dry_contract/node_geometry_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/next_model_contract.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [forward-model, wall-fluid-coupling, test-section, fluid-api-contract]
related:
  - .agent/status/2026-07-18_TODO-TSWFC2-DISTRIBUTED-WALL-FLUID.md
  - .agent/journal/2026-07-18/tswfc2-distributed-wall-fluid-api.md
  - imports/2026-07-18_tswfc2_distributed_wall_fluid_api.json
task: TODO-TSWFC2-DISTRIBUTED-WALL-FLUID
date: 2026-07-18
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# TSWFC2 Fluid API Contract

Generated: `2026-07-18T16:36:26-05:00`

## Decision

The Fluid solver now exposes a disabled-by-default TSWFC2 API:
`test_section_wall_fluid_mode = distributed_wall_fluid_nodes_v1`.

This is an implementation of the dry-contract path, not a scored campaign or an
admitted model. The hook differs from the prior single bulk-to-ambient fallback
by using distributed setup nodes with separate fluid, inner-wall, outer-wall,
external-boundary, and heat-ledger fields on matched wall/test-section spans.

## Outputs

- `fluid_api_change_log.csv`
- `node_geometry_reconciliation.csv`
- `runtime_guardrail_audit.csv`
- `validation_results.csv`
- `next_step_handoff.csv`
- `source_manifest.csv`
- `summary.json`

## Acceptance Signal

Future dry contracts and scorecards must evaluate temperature-shape improvement:
`TP` RMSE, `TW` RMSE, all-probe RMSE, and declared shape probes such as TW5,
TW6, TP5, TP6, and TW8. A candidate that only improves mass flow remains a
no-go.

## Guardrails

No OpenFOAM native outputs, registry/admission state, Fluid campaign outputs,
scorecard, scheduler state, fitted coefficients, CFD mdot runtime inputs,
realized CFD `wallHeatFlux` inputs, imposed CFD cooler-duty inputs, or measured
TP/TW runtime inputs were introduced.
