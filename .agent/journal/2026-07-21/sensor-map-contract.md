---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_sensor_map_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/sensor_coordinate_ledger.csv
tags: [sensor-map, thesis, score-only]
related:
  - .agent/status/2026-07-21_TODO-PRED-SENSOR-MAP.md
  - imports/2026-07-21_sensor_map_contract.json
task: TODO-PRED-SENSOR-MAP
date: 2026-07-21
role: Writer/Implementer/Reviewer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Sensor Map Contract

## Attempted

Consolidated the completed S7 TP/TW sensor-map evidence into the canonical
`TODO-PRED-SENSOR-MAP` row without reopening extraction or scoring.

## Observed

The S7 package already classified `17` sensor rows, mapped `TP2`, bounded `15`
rows, and excluded `TW10`. The score-only policy forbids runtime, fit, and
model-selection use of TP/TW temperatures.

## Inferred

The useful next thesis use is caption/prose discipline: TP/TW rows can diagnose
post-solve residuals, but energy balance and branch heat parity remain the
primary thermal evidence.

## Caveats

Most coordinates are still approximate or mixed-provenance. Exact experimental
instrument-location claims remain unavailable.

## Next Useful Actions

Use `TP2` only as a score-only projected target, keep bounded sensors as
diagnostic context, and exclude `TW10` until a heat-exchanger shell state is
explicitly admitted.
