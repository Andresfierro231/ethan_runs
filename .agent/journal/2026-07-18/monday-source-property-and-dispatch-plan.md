---
provenance:
  - operational_notes/07-26/18/2026-07-18_MONDAY_SOURCE_PROPERTY_AND_AGENT_DISPATCH.md
  - work_products/2026-07/2026-07-18/2026-07-18_source_property_label_enforcement/summary.json
  - .agent/BLOCKERS.md
tags: [monday-handoff, coordination, source-property-labels, scheduler-readonly]
related:
  - .agent/status/2026-07-18_AGENT-549.md
  - imports/2026-07-18_monday_source_property_and_dispatch_plan.json
task: AGENT-549
date: 2026-07-18
role: Coordinator/Writer
type: journal
status: complete
---
# Monday Source/Property And Dispatch Plan

Task: AGENT-549

## Attempted

Documented the user's end-of-day coordination request: what jobs/tasks should be
distributed to agents on Monday, how to keep making progress, how to prevent
future missing source/property labels, and whether anything should be launched
before leaving for the weekend.

## Observed

The generated state still reports four open scientific blockers:
two-tap `corner_lower_right` material reverse flow, predictive wall/test-section
submodels, upcomer-onset data sparsity, and F6 friction/Re correction. AGENT-546
created the current label enforcement evidence: 1,110 fit/admission candidate
rows scanned, 1,028 original rows missing at least one required label, and 0
enforced rows with blank labels.

The read-only scheduler snapshot showed existing long-running work already in
flight: `3293924`, `3299610`, `3299620`, dependency-held `3295438`, and dev job
`3302317`. The board also shows active TSWFC2/external Fluid ownership. Those
conditions make a new uncoordinated weekend launch risky.

## Inferred

The most useful Monday work is not another solver launch; it is converting the
AGENT-546 enforcement audit into permanent repo structure, then using that gate
for Salt1, perturbation/external rows, and future predictive/F6/wall scorecards.
The dispatch note therefore prioritizes infrastructure and label refresh before
new scorecard/admission claims.

## Caveats

The scheduler snapshot is point-in-time and should be rechecked Monday. The
note does not cancel, submit, requeue, or harvest anything. It also does not
decide the active TSWFC2/Fluid row; Monday agents must read that row's closeout
or live handoff before claiming overlapping Fluid source files.

## Next Useful Actions

- Monday coordinator: open the dispatch note immediately after standard
  startup files.
- Assign the source/property gate infrastructure agent first.
- Assign Salt1 and perturbation/external label refresh agents in parallel after
  the infrastructure gate is clear.
- Recheck `squeue` and AGENT-519 before any harvest or new launch.

## Guardrails

No native solver outputs, registry/admission state, scheduler state, Fluid
source, external repositories, fitting, tuning, model selection, active task
artifacts, or scientific admission state were changed.
