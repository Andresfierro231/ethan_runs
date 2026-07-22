---
provenance:
  - .agent/BLOCKERS.md
  - operational_notes/07-26/20/2026-07-20_FORWARD_PREDICTIVE_BLOCKERS_AND_NEXT_STEPS.md
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_smoke_scenario/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_source_property_gate_infrastructure/README.md
tags: [forward-model, blocker-unlock, runbook, tswfc2, umx1, source-property-gate]
related:
  - .agent/status/2026-07-20_AGENT-556.md
  - .agent/journal/2026-07-20/forward-blocker-unlock-runbook.md
  - imports/2026-07-20_forward_blocker_unlock_runbook.json
task: AGENT-556
date: 2026-07-20
role: Coordinator/Writer
type: work_product
status: complete
---
# Forward Blocker Unlock Runbook

## Result

Decision: `runbook_complete_next_tswfc2_scorecard_ready_to_claim`.

This package implements the coordinator slice of the blocker-unlock plan. It
does not run a Fluid solve, score grid, fit, model selection, scheduler job, or
admission update. It reconciles the current gates and defines the exact
follow-up task contracts.

AGENT-555 was already used by a completed PM10 task, so this runbook uses
AGENT-556 and assigns follow-up contracts to AGENT-557 through AGENT-561.

## Current Gates

- External Fluid follow-up
  `impl-2026-07-20-fluid-umx1-tswfc2-smoke-followup` is completed.
- AGENT-553 TSWFC2 Salt 2 smoke passed with accepted roots, all four nodes, and
  nonzero ledgers.
- AGENT-554 source/property gate tooling is available and must be strict for
  scorecard-like admission packages.
- The wall/test-section blocker remains open until a setup-only candidate
  passes coupled mdot, TP, TW, all-probe, runtime, split, and source/property
  gates.

## Files

- `blocker_unlock_runbook.csv`: ordered blocker-unlock track plan.
- `next_agent_contracts.csv`: exact follow-up task contracts.
- `dependency_gate_matrix.csv`: pass/fail/no-go gates for each follow-up.
- `documentation_contract.csv`: mandatory after-action documentation.
- `source_manifest.csv`: repo evidence used by this coordinator pass.
- `summary.json`: machine-readable decision and gate status.

## Next Action

Claim AGENT-557 and run the bounded TSWFC2 nominal scorecard. Use the AGENT-553
four-node setup as the only candidate. Do not expand into a broad grid, tune
after seeing score-only rows, or report admission from mdot-only improvement.

AGENT-557 may resolve `predictive-wall-test-section-submodels` only if the
candidate passes eligible nominal roots, runtime legality, strict
source/property labels, and coupled thermal-shape gates versus M3 and prior
wall/source candidates. Otherwise it should close as
`not_admitted_no_grid_expansion` or an explicit release-gate block.

## Closeout Standard

Every follow-up agent must leave a status file, journal entry, import manifest,
package README or operational note, source manifest, validation command log,
and relevant map update. The process must be complete enough for another agent
to continue without reading chat logs.
