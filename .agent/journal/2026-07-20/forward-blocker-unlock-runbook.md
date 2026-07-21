---
provenance:
  - .agent/BLOCKERS.md
  - .agent/BOARD.md
  - ../cfd-modeling-tools/.agent/BOARD.md
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/summary.json
tags: [forward-model, blocker-unlock, coordination, runbook]
related:
  - .agent/status/2026-07-20_AGENT-556.md
  - imports/2026-07-20_forward_blocker_unlock_runbook.json
  - work_products/2026-07/2026-07-20/2026-07-20_forward_blocker_unlock_runbook/README.md
task: AGENT-556
date: 2026-07-20
role: Coordinator/Writer
type: journal
status: complete
---
# Forward Blocker Unlock Runbook

## Attempted

Converted the user-approved blocker-unlock plan into a durable coordinator
package. The task intentionally stayed documentation/coordination-only: no
Fluid solve, score grid, fit, model selection, scheduler action, registry
mutation, or blocker-register edit.

## Observed

AGENT-555 was already claimed and completed for PM10 glossary/current-state
documentation. The forward blocker-unlock coordinator therefore moved to
AGENT-556, and follow-up contracts shifted to AGENT-557 through AGENT-561.

The external Fluid row
`impl-2026-07-20-fluid-umx1-tswfc2-smoke-followup` is now completed. That
changes the gate from the earlier plan: the next TSWFC2 bounded scorecard is no
longer waiting on an in-progress Fluid row. AGENT-553 already proved the
four-node Salt 2 TSWFC2 smoke can run with accepted finite roots and nonzero
ledgers. AGENT-554 added source/property gate tooling that future scorecard
tasks should run in strict mode.

## Inferred

The highest-progress next executable task is AGENT-557: a bounded TSWFC2
nominal scorecard using the AGENT-553 four-node setup as the only candidate.
The scorecard must be able to stop cleanly as not admitted or release-gate
blocked. It must not expand into a broad grid or claim admission from mdot-only
improvement.

UMX1 should be handled as a separate intake/review task because its Fluid row
completed after the earlier blocker note, but Ethan-side score/admission status
has not been reviewed. Upcomer onset and F6/two-tap remain evidence-design or
staging tracks until they have non-recirculating/near-onset anchors and same-QOI
UQ.

## Caveats

This task does not resolve any blocker. It makes the next work decision-complete
and records the fact that the external Fluid gate has moved from active to
completed. `.agent/blockers.yml` remains read-only under this row.

## Next Useful Actions

Claim AGENT-557 with the scope in `next_agent_contracts.csv`. Run preflight
before editing. Use strict runtime-input and source/property gates. Close the
task with status, journal, import manifest, package README, source manifest,
scorecard/admission artifacts, and a forward-map update.
