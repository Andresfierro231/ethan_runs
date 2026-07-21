---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/hydraulic_model_form_ladder.csv
  - work_products/2026-07/2026-07-17/2026-07-17_f6_litrev_hydraulic_model_form_ladder/summary.json
tags: [f6, friction, litrev, hydraulic-model-forms, journal]
related:
  - .agent/status/2026-07-17_AGENT-512.md
  - imports/2026-07-17_f6_litrev_hydraulic_model_form_ladder.json
task: AGENT-512
date: 2026-07-17
role: Hydraulics/Literature-synthesis/Implementer/Tester/Writer
type: journal
status: complete
---
# F6 LitRev Hydraulic Model-Form Ladder

Task: `AGENT-512`

## Attempted

Implemented the user's requested plan to rank hydraulic and friction model forms
worth trying based on the current F6 anchor-first evidence and the LitRev
model-form backlog. This was an evidence package only: no scheduler action, CFD
harvest, Fluid edit, blocker mutation, or admission change.

## Observed

The current F6 anchor-first package reports `0` PM5 ordinary anchors, `12` PM5
recirculation diagnostics, and `8` PM10/high-heat rows blocked or unknown
pending terminal harvest. The LitRev backlog identifies F6 `phi(Re)`,
reset/redevelopment losses, component/cluster K, upcomer recirculation/onset
classification, boundary-layer development toggles, property sensitivity, and
future transient/ROM methods with explicit gates.

## Inferred

The immediate research move is still not a fit. The next defensible hydraulic
work is an anchor harvest and gate classification. F6 `phi(Re)` becomes
scoreable only after low-reverse pressure anchors exist. If current terminal
evidence remains recirculating, the recirculation-modeled lane should be named
as a section-effective/onset penalty and scored against `F3_shah_apparent`.
Reset/redevelopment and component/cluster K remain worth preparing, but only
after admitted pressure-basis evidence exists.

## Caveats

Boundary-layer development toggles are diagnostic-ready but not executable as a
coupled ablation because prerequisite scorecards still show no admitted segment
pressure model rows and no ordinary-pipe branch aggregate. The package keeps
transient and ROM rows as future-method notes, not current closure candidates.

## Next Useful Actions

Use `anchor_first_decision_tree.csv` as the operational sequence for the F6
avenue. Use `hydraulic_model_form_ladder.csv` when deciding what to implement
after terminal harvest. Keep `forbidden_shortcuts.csv` attached to any future
scorecard so global multipliers, active `64/Re`, universal K, and ordinary
coefficient labels in recirculation do not re-enter the model.
