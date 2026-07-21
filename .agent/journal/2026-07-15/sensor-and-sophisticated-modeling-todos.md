---
task: AGENT-432
date: 2026-07-15
role: Coordinator/Writer
type: journal
status: complete
tags: [sensor-map, forward-model, upcomer, boundary-layer]
related:
  - .agent/BOARD.md
  - operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md
---
# Sensor and Sophisticated Modeling TODOs

## Observed facts

- AGENT-405 sensor policy currently excludes TP2 because the provisional Fluid
  coordinate is off the current 1D path, while native CFD TP2/notes bind it to
  the right-downcomer/bottom-horizontal junction.
- The same policy excludes TW10 because it is a cooling-jacket shell surrogate
  and the current forward modes do not emit a finite active-HX shell
  temperature.
- Current upcomer evidence is recirculating, so fitted single-stream `Nu`,
  `f_D`, and `K` labels are invalid for those rows.
- Segment-resolved pressure and thermal model rows already exist, but boundary
  layer development and a hybrid upcomer representation needed explicit board
  TODOs.

## Interpretation

The correct next modeling direction is more sophisticated, not just more
fitted. TP2 should be recovered as a validation/scoring output because it maps
to a physical junction on the 1D path. TW10 should stay excluded until the model
has a shell-state output. Upcomer recirculation should be modeled as a
pipe-throughflow plus convection-cell exchange problem, and hydraulic/thermal
boundary-layer development should be quantified by segment.

## Actions

- Added active coordination row `AGENT-432`.
- Added board TODO `TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE`.
- Added board TODO `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL`.
- Added board TODO `TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD`.
- Wrote the dated decision note and linked it from forward-model and
  thermal/internal-Nu maps.
- Updated the presentation outline text only; no PowerPoint artifacts were
  created.

## Recommended next action

Claim `TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE` first, because sensor count and
aggregate RMSE definitions should be stable before the coupled M3+TS and
boundary-layer scorecards are compared.
