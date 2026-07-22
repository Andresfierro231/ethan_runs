---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/api_contract.csv
  - ../cfd-modeling-tools/.agent/BOARD.md
tags: [umx1, next-session, stratification, blocked-handoff]
related:
  - .agent/status/2026-07-18_AGENT-548.md
  - .agent/journal/2026-07-18/umx1-stratified-reservoir-blocked-handoff.md
  - imports/2026-07-18_umx1_stratified_reservoir_blocked_handoff.json
task: AGENT-548
date: 2026-07-18
role: Coordinator/Writer
type: operational_note
status: blocked
---

# UMX1 Next Session Context

## Start Here

Open these files in this order:

1. `work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/README.md`
2. `work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/blocker_evidence.csv`
3. `work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/api_contract.csv`
4. `work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/implementation_sequence.csv`
5. `work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/validation_plan.csv`
6. `work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/summary.json`
7. `../cfd-modeling-tools/.agent/BOARD.md`

## Current State

UMX1 has a real Fluid exchange hook from AGENT-540 and a no-admission fast-scan
smoke package from AGENT-544. The smoke package showed runtime legality and
conservation are not the blockers: conservation passed `9/9`. The blockers are
accepted roots (`3/9`) and probe behavior: both fixed exchange candidates
worsened all scored probe groups versus the disabled baseline.

The next scientific move is not another multiplier grid. It is a richer
setup-only stratified reservoir/source state, because current Fluid parses
`upcomer_reservoir_heat_sources` but does not apply those rows in the reservoir
energy update.

## Active Blocker

Do not edit Fluid until the external Fluid board row
`impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api` completes or releases
the target files. That row owns the exact files UMX1 would need:

- `tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py`
- `tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
- `tamu_first_order_model/Fluid/tests/test_solver_contracts.py`

Also avoid reusing task ID `AGENT-547`; it is already assigned to F6 pressure
planning. Use the next open unique ID and claim both Ethan and external Fluid
rows before editing.

## Next Exact Steps

1. Check `../cfd-modeling-tools/.agent/BOARD.md` for the TSWFC2 external row.
2. If it is still active, stop after updating this handoff or writing a short
   monitor note; do not touch Fluid.
3. If it is complete or released, claim a new UMX1 Fluid-edit row in both
   boards with explicit ownership of the four Fluid files above plus new Ethan
   status/journal/import/work-product paths.
4. Run Ethan preflight for the new row.
5. Implement `api_contract.csv` exactly: active setup-only reservoir source
   rows, new reservoir ledger fields, default no-op compatibility, and explicit
   validation failures for malformed rows.
6. Run the focused Fluid unit/compile checks from `validation_plan.csv`.
7. Only after Fluid tests pass, create the new UMX1S dry/smoke scorer package.
8. Run dry validation before any bounded smoke.
9. If bounded smoke runs, keep it Salt2/Salt3/Salt4 nominal only and
   no-admission.
10. Close with status, journal, import manifest, map update, and `finish_task`.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs.
- Do not edit registry or admission state.
- Do not launch OpenFOAM.
- Do not run a full UMX1 grid.
- Do not use CFD mdot, realized CFD `wallHeatFlux`, imposed CFD cooler duty, or
  validation TP/TW as runtime inputs.
- Do not relax accepted-root or temperature-periodicity gates just to make the
  smoke pass.
- Do not combine UMX1 and TSWFC2 in one Fluid patch unless a later coordinator
  explicitly assigns that integration row.

## Minimal Acceptance For Next Progress

The next session makes real progress if it either:

- confirms the external Fluid blocker is gone and lands focused Fluid tests for
  active reservoir source rows, or
- confirms the blocker remains and records that current state without mutating
  Fluid.
