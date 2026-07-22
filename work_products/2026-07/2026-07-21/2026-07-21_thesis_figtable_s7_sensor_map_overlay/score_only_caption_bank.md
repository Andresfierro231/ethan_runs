---
provenance:
  created_by: codex
  date: 2026-07-21
tags: [thesis, S7, sensor-map, score-only-targets]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/README.md
---

# Caption Bank

## TP/TW Sensor Overlay

The overlay marks each TP/TW location as mapped, bounded, or excluded. TP2 is the only mapped projected anchor; provisional TP/TW placements are bounded to 1D segments; TW10 is excluded because the active heat-exchanger shell state is absent.

## Score-Only Target Caveat

TP/TW temperature targets are shown only after solve for scoring or diagnostics. They are forbidden as runtime inputs, never fit coefficient values, and cannot select model forms.

## Bounded Coordinate Caveat

Bounded sensors should be labeled by path segment or junction state rather than claimed as exact experimental coordinate measurements.
