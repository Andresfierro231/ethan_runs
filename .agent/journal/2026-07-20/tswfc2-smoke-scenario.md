---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tswfc2_fluid_api_contract/node_geometry_reconciliation.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/summary.json
tags: [forward-model, tswfc2, smoke, thermal-modeling]
related:
  - .agent/status/2026-07-20_AGENT-553.md
  - imports/2026-07-20_tswfc2_smoke_scenario.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-553
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer
type: journal
status: complete
---
# TSWFC2 Smoke Scenario

## Attempted

Implemented the planned TSWFC2 smoke as a dated work-product package rather
than under `tools/analyze/**`, because task preflight reported conflicts with
open broad TODO rows that own `tools/analyze/**`. The package still performs
the same bounded work: write one explicit four-node scenario, parse it through
the Fluid config loader, run only Salt 2 through `solve_case`, and audit roots,
finite outputs, and TSWFC2 ledgers.

## Observed

The first scoped preflight failed because the initial board row included
`tools/analyze/run_tswfc2_smoke_scenario.py` and
`tools/analyze/test_tswfc2_smoke_scenario.py`, overlapping open TODO scopes.
After moving implementation into
`work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/**`,
preflight passed with no conflicts.

The single smoke run passed. Fluid returned `root_status=accepted`,
`accepted_for_validation=True`, pressure and temperature roots bracketed,
`mdot=0.0221909170412141 kg/s`, and temperature periodicity error
`8.847109711496159e-10 K`. The active TSWFC2 ledger has four rows and all four
expected node IDs:
`TSWFC2_N01_pre_test_bracket`,
`TSWFC2_N02_test_section_lower`,
`TSWFC2_N03_test_section_upper`, and
`TSWFC2_N04_post_test_bracket`.
The summed absolute TSWFC2 heat is `43.7432402432455 W` and the max ledger
residual is `0.0 W`.

## Inferred

The Fluid TSWFC2 API is execution-ready for this bounded Salt 2 setup. That is
only a smoke result: it establishes finite accepted roots and nonzero ledgers
for the prepared scenario, not score behavior, calibration value, model
selection, or admission.

## Caveats

No score grid was run. No conductances, bounds, source/property labels, Fluid
source files, native CFD outputs, scheduler state, registry state, or admission
state were changed. The smoke uses no validation record at runtime; Fluid's
native `validation_table.csv` is present because `write_case_report` emits it,
but its measured columns are empty for this run.

## Next Useful Actions

Use this package as the first executable TSWFC2 API smoke evidence. Any next
TSWFC2 scoring, conductance sweep, or final predictive scorecard should be a
separate claimed task with source/property labels and admission guardrails
checked before fit or model selection.
