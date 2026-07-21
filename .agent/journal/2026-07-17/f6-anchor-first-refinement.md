---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/summary.json
  - work_products/2026-07/2026-07-17/2026-07-17_f6_anchor_first_refinement/f6_lane_decision.csv
tags: [f6, friction, recirculation, anchor-first, journal]
related:
  - .agent/status/2026-07-17_AGENT-505.md
  - imports/2026-07-17_f6_anchor_first_refinement.json
task: AGENT-505
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# F6 Anchor-First Refinement

Task: `AGENT-505`

## Attempted

Implemented the anchor-first refinement plan for `f6-friction-re-correction`.
The work did not harvest native CFD or launch new jobs. It converted the
current F6 evidence into an explicit next-step package with terminal readiness,
anchor gates, lane decisions, pressure residual status, and recommended next CFD
runs.

## Observed

PM5 still has `12` recirculation diagnostic rows and `0` ordinary F6 anchors.
PM10 contributes `4` future-holdout rows but recorded readiness is blocked.
High-heat contributes `4` candidate anchor rows but recorded readiness is
running/not terminal. The optional read-only scheduler refresh from this shell
returned unknown states for jobs `3293924`, `3295438`, `3299610`, and `3299620`,
so no row was marked terminal-ready by this task.

## Inferred

The immediate research path is not another fit. It is terminal evidence
triage. If high-heat harvest yields `RAF < 0.01` and `RMF < 0.01` with
same-window pressure evidence, ordinary F6 can be scored. If not, the Salt3
high-Re/high-insulation and low-Q/low-insulation sentinels should bracket the
onset envelope before the full small `Q x insulation` matrix is launched.

## Caveats

This task did not update `.agent/blockers.yml`, generated indexes, registry
state, native solver outputs, or external Fluid code. The scheduler status table
is a read-only observation attempt, not a terminal admission result.

## Next Useful Actions

When scheduler access is reliable or the owning run packages report terminal
jobs, claim a separate harvest task. Harvest high-heat first, apply the full
output contract, and only then decide whether to score ordinary F6 or proceed
to the Salt3 onset matrix.
