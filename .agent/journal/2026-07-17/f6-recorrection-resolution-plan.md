---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_friction_re_correction_unblock/f6_candidate_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_recorrection_resolution_plan/summary.json
tags: [f6, friction, recirculation, journal]
related:
  - .agent/status/2026-07-17_AGENT-501.md
  - imports/2026-07-17_f6_recorrection_resolution_plan.json
task: AGENT-501
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# F6 Re-Correction Resolution Plan

Task: `AGENT-501`

## Attempted

Implemented the requested plan to address `f6-friction-re-correction` without
launching or harvesting new CFD. The work created a follow-on package that
turns the AGENT-487 decision into a row-level gate matrix, explicit decision
tree, promotion scorecard, next-action queue, and recommended further studies.

## Observed

The existing PM5 candidate inventory has 12 rows. Each row has material reverse
flow by the ordinary F6 gate because `RAF` or `RMF` is at least `0.01`; the
observed rows include reverse area fractions around `0.37` to `0.79` and
reverse mass fractions around `0.50`. The AGENT-493 PM10 package still reports
4 blocked/non-terminal PM10 cases, and the AGENT-485 high-heat monitor still
reports 4 running/not-harvest-ready cases in the cited package.

## Inferred

PM5 rows classify as recirculation diagnostics because they contain useful
regime information but violate the single-stream assumption needed for ordinary
`f_D`, F6, or component `K` fitting. The scientifically honest action is to
keep `F3_shah_apparent` as production, preserve PM5 as diagnostic evidence, and
wait for either low-reverse-flow anchors or a complete named recirculation
closure evidence package.

## Caveats

This task did not query live scheduler state, harvest terminal outputs, mutate
native CFD files, update `.agent/blockers.yml`, or refresh generated indexes.
The PM10 and high-heat statuses are the statuses recorded by their existing
read-only packages, not fresh scheduler evidence.

## Next Useful Actions

Harvest PM10 and high-heat runs only after terminal completion in a separately
claimed extraction task. If those rows do not provide `RAF < 0.01` and
`RMF < 0.01`, prioritize the Q x insulation onset-bracketing matrix and then
score only named recirculation/onset closures against `F3_shah_apparent` with
validation/holdout separation and uncertainty.
