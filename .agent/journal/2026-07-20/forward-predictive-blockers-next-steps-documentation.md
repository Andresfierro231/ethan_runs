---
provenance:
  - .agent/BLOCKERS.md
  - operational_notes/maps/forward-predictive-model.md
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/README.md
tags: [forward-model, blocker-synthesis, next-steps, documentation]
related:
  - .agent/status/2026-07-20_AGENT-552.md
  - imports/2026-07-20_forward_predictive_blockers_next_steps_documentation.json
  - operational_notes/07-26/20/2026-07-20_FORWARD_PREDICTIVE_BLOCKERS_AND_NEXT_STEPS.md
task: AGENT-552
date: 2026-07-20
role: Writer/Coordinator
type: journal
status: complete
---
# Forward Predictive Blockers / Next-Steps Documentation

## Attempted

Converted the user-facing blocker and next-step summary into durable repo
documentation. The work was intentionally documentation-only and used the
generated blocker state, forward predictive topic map, and July 18 synthesis
packages as evidence.

## Observed

The broad heater/cooler/wall blocker is superseded. Heater and cooler/HX are
bounded enough to stop treating them as the main blocker. The live
forward-model blockers are narrower: wall/test-section/passive-boundary thermal
shape, upcomer stratification and onset sparsity, F6/two-tap pressure
anchoring, and source/property label enforcement.

The July 18 UMX1 smoke package is not grid-ready: conservation passes but
accepted roots fail for most rows, and exchange candidates worsen probe scores.
The correct next action is a Fluid API/root contract row, not another broad
UMX1 score grid.

## Inferred

The highest-progress next path is UMX1 API/root repair because the persistent
TP/TW failure pattern looks like local thermal shape and upcomer
mixing/stratification, not a scalar passive-loss deficiency. TSWFC2 should be
kept as the secondary wall/test-section path, provided it stays distinct from
the failed one-node wall/fluid fallback.

## Caveats

This task did not change `.agent/blockers.yml`, scientific admission state,
model selection, scheduler state, native solver outputs, or Fluid source. It
does not admit final forward-v1.

## Next Useful Actions

Open
`operational_notes/07-26/20/2026-07-20_FORWARD_PREDICTIVE_BLOCKERS_AND_NEXT_STEPS.md`
before launching new forward predictive work. Then choose from the documented
order: UMX1 API/root repair, TSWFC2 secondary path, upcomer onset anchor design,
F6/two-tap pressure anchors, and source/property label refresh.
