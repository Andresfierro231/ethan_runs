---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/no_solver_api_contract.csv
  - operational_notes/07-26/17/2026-07-17_WEEKEND_NEXT_MODEL_HANDOFF_PLAN.md
tags: [forward-model, upcomer-mixing, handoff, no-solver]
related:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/README.md
  - .agent/status/2026-07-18_AGENT-537.md
task: AGENT-537
date: 2026-07-18
role: Implementer/Tester/Writer
type: operational_note
status: complete
---
# UMX1 API Contract Audit

## Start Here

Open `work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/README.md` first, then
`work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/no_solver_api_contract.csv` and
`work_products/2026-07/2026-07-18/2026-07-18_umx1_api_contract_audit/scenario_config_field_audit.csv`.

## Result

The inspected Fluid checkout does not have a real upcomer
mixing/stratification hook. Stop before UMX1 solver scoring.

## Output Contract

The required next external Fluid implementation is a no-op-default
energy-conserving exchange API: an explicit upcomer mixing mode, one exchange
multiplier, declared parent segments, reservoir heat-source routing, an energy
ledger, and probe metadata that distinguishes main stream, reservoir, and wall
states.

## Do Not Do

Do not fake UMX1 with external-boundary role rows, parent HTC/friction
multipliers, heater-source weights, diagnostic Ri tables, or posthoc sensor
correction. Do not use Salt3 or blind rows for model-form selection.
