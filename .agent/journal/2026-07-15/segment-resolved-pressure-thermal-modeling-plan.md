---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
tags: [journal, forward-predictive-model, pressure-balance, thermal-balance, segment-models]
related:
  - .agent/status/2026-07-15_AGENT-431.md
  - imports/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.json
task: AGENT-431
date: 2026-07-15
role: Coordinator/Writer
type: journal
status: complete
---
# Segment-Resolved Pressure/Thermal Modeling Plan

## Observed Facts

- The user correctly flagged that `dp_drive(mdot)` is misleading if read
  literally: buoyancy drive depends on the temperature/density field and loop
  elevation/position.
- The user also clarified that different loop regions should have different
  pressure and thermal model forms.
- Existing evidence already requires this discipline: PM5/upcomer rows are
  recirculating diagnostics, external-boundary heat loss has segment dictionaries,
  and M3+TS requires a modeled test-section heat-loss term.

## Inferred Interpretation

The next forward model should be segment-resolved and thermally coupled. A
pressure-root solve may still use `mdot` as the root variable, but each trial
`mdot` must imply a segment temperature/density field, and each segment must
evaluate its own drive, loss, and heat terms.

## Changes Made

- Added active coordination row `AGENT-431`.
- Added four future board TODOs for the segment equation contract, pressure
  model scorecard, thermal model scorecard, and coupled M3+TS scorecard.
- Added a dated operational note with expanded equations and admission guardrails.
- Updated the forward-predictive-model map and definitions-first presentation
  outline to replace global shorthand with segment-resolved wording.

## Recommended Next Action

Claim `TODO-PREDICT-SEGMENT-EQUATION-CONTRACT` before implementing new pressure
or thermal scorecards. That task should define model slots by loop region and
prevent future agents from fitting a single global closure across incompatible
segments.
