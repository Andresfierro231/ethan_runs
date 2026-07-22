---
provenance:
  - ../cfd-modeling-tools/.agent/BOARD.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/summary.json
tags: [umx1, stratification, forward-predictive, blocked-handoff]
related:
  - .agent/status/2026-07-18_AGENT-548.md
  - .agent/journal/2026-07-18/umx1-stratified-reservoir-blocked-handoff.md
  - imports/2026-07-18_umx1_stratified_reservoir_blocked_handoff.json
task: AGENT-548
date: 2026-07-18
role: Coordinator/Writer/Tester
type: work_product
status: blocked
---

# UMX1 Stratified Reservoir Blocked Handoff

## Result

The UMX1 stratified-reservoir implementation plan cannot safely edit Fluid in
this row because the external Fluid board already has an in-progress TSWFC2 row
owning the same implementation files:

`impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api`

That row claims `solver.py`, `config_loader.py`, `README.md`, and
`tests/test_solver_contracts.py`. AGENT-548 therefore leaves Fluid read-only and
publishes a decision-complete handoff for the next non-overlapping Fluid-edit
row.

## Current Evidence

- AGENT-540: Fluid has a disabled-by-default UMX1 exchange hook and focused
  contract tests.
- AGENT-544: bounded fast-scan smoke completed with runtime legality pass,
  split discipline pass, conservation pass `9/9`, accepted roots `3/9`, and
  exchange candidates worsening all scored probe groups versus disabled
  baseline.
- Current Fluid source: `upcomer_reservoir_heat_sources` is parsed and
  round-tripped, but the source rows are not yet active in the energy update.

## Handoff Contract

Open a new external Fluid-edit row only after the TSWFC2 row is complete or
released. The new row should implement the API in `api_contract.csv`, then use
`implementation_sequence.csv`, `validation_plan.csv`, and
`assumptions_and_decisions.csv` as the minimum acceptance checklist.

For the next session restart sequence, use `NEXT_SESSION_CONTEXT.md`. It records
the exact files to open, active blocker, do-not-do guardrails, and minimum
acceptance signal for making progress.

## Stop Rules

- Do not edit Fluid while the TSWFC2 external row owns the target files.
- Do not launch a UMX1 grid from AGENT-544 outputs.
- Do not admit any UMX1 candidate from this handoff.
- Do not use CFD mdot, realized CFD `wallHeatFlux`, imposed CFD cooler duty, or
  validation TP/TW as runtime inputs.
