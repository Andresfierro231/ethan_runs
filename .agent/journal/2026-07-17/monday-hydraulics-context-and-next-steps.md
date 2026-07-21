---
provenance:
  - operational_notes/07-26/17/2026-07-17_MONDAY_HYDRAULICS_CONTEXT_AND_NEXT_STEPS.md
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md
tags: [handoff, monday-start, hydraulics, pressure-ledger]
related:
  - .agent/status/2026-07-17_AGENT-535.md
  - imports/2026-07-17_monday_hydraulics_context_and_next_steps.json
task: AGENT-535
date: 2026-07-17
role: Hydraulics/Writer
type: journal
status: complete
---
# Monday Hydraulics Context And Next Steps

Task: AGENT-535

## Attempted

Wrote a fresh-agent Monday handoff focused on the hydraulic/F6/two-tap extractor
line after AGENT-523, AGENT-525, and AGENT-530. The note avoids AGENT-534's
active main Monday handoff path and does not edit `START_HERE`.

## Observed

The current hydraulic lane has a clear next data-producing blocker: raw local
feature endpoint pressures and same-window RAF/RMF/SVF are missing for the
three `corner_lower_right` component targets. Existing evidence remains useful
for schema, preserved feature loss, and negative-K blocker diagnosis, but not
for ordinary coefficient admission.

## Inferred

The right Monday move is a raw endpoint sampling contract first, followed only
later by staged-copy postprocessing. Starting with a launch would be premature
because tap labels, pressure/velocity basis, straight-reference policy,
recirculation metrics, and same-QOI uncertainty must be declared up front.

## Contradictions And Caveats

This note is supplemental. AGENT-534 owns the main Monday fresh-agent handoff
and may add scheduler/run-submission context. If the two notes disagree on live
scheduler state, trust the fresher AGENT-534 or AGENT-519 monitor evidence.

## Next Useful Actions

Monday should claim `TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS` or an equivalent
non-overlapping row, build a tested sampling contract from AGENT-530's
`next_raw_postprocessing_queue.csv`, and avoid native case mutation or
coefficient fitting.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
external Fluid files, generated docs index files, or active-agent scoped
artifacts were mutated. No solver/postprocessing launch, fitting, tuning, model
selection, or scientific admission change was performed.
