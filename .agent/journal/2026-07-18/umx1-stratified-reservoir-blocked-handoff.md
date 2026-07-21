---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/summary.json
tags: [umx1, stratification, journal, blocked-handoff]
related:
  - .agent/status/2026-07-18_AGENT-548.md
  - imports/2026-07-18_umx1_stratified_reservoir_blocked_handoff.json
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_stratified_reservoir_blocked_handoff/api_contract.csv
task: AGENT-548
date: 2026-07-18
role: Coordinator/Writer/Tester
type: journal
status: blocked
supersedes: []
superseded_by:
---

# UMX1 Stratified Reservoir Blocked Handoff Journal

Task: `AGENT-548`

## Observed

AGENT-540 confirms Fluid has a real UMX1 exchange hook. AGENT-544 confirms the
hook is usable for a no-admission smoke scorer: runtime legality, split
discipline, and conservation pass, but accepted roots pass only `3/9` and the
fixed exchange candidates worsen all scored probe groups versus disabled
baseline.

Current Fluid code parses `upcomer_reservoir_heat_sources`, but those rows are
not active in the reservoir energy update. Implementing the requested
stratified/source state requires editing Fluid `solver.py`, `config_loader.py`,
README, and focused tests.

The external Fluid board currently has in-progress row
`impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api` owning those exact
files for TSWFC2. The Ethan board also has active TSWFC2 and two-tap rows, so
AGENT-548 was narrowed to documentation/handoff only.

## Attempted

I claimed AGENT-548, ran preflight, and wrote a blocked handoff package instead
of editing Fluid. The package freezes the proposed UMX1 stratified-reservoir API
contract, validation plan, implementation order, blocker evidence, and
assumptions/decisions. I later added `NEXT_SESSION_CONTEXT.md` so the next
agent can restart from a short ordered file list and explicit do-not-do list
without reconstructing the chat context.

## Inferred

The correct next engineering move is not to force a concurrent Fluid patch. The
right sequence is to wait for the TSWFC2 external Fluid row to finish or release
the files, then open a new non-overlapping Fluid-edit row for UMX1. That row can
implement active setup-only reservoir source rows without changing default UMX
behavior and without rerunning a broad score grid.

## Contradictions And Caveats

- This is a blocked handoff, not a Fluid implementation.
- The proposed source-row contract is decision-complete but unverified in Fluid.
- No solver or smoke run was launched from this row.
- No blocker was added to `.agent/blockers.yml` because AGENT-548 did not claim
  that file and the immediate blocker is active file ownership, not a scientific
  result change.

## Next Useful Actions

- Let `impl-2026-07-18-fluid-tswfc2-distributed-wall-fluid-api` finish or release
  Fluid `solver.py`, `config_loader.py`, README, and tests.
- Claim a new UMX1 Fluid-edit row with a unique ID and the exact files named in
  this package.
- Implement `api_contract.csv`, run `validation_plan.csv`, then decide whether a
  bounded no-admission smoke is legal.
