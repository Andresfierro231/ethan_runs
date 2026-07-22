---
provenance:
  - tools/analyze/build_1d_sensor_projection_operator_tp_tw_wall_bulk.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/summary.json
task: TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22
date: 2026-07-22
role: Sensor-map / Thermal-modeling / Forward-pred / Writer / Tester
type: journal
status: complete
tags: [journal, sensor-map, projection-operator, tp, tw, thermal-development]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk
---

# 1D sensor projection operator for TP/TW wall/bulk

## Attempted

Consumed the N4 sensor/QOI projection table, D2 TP/TW projection gate, TP/TW
elevation panels, signed-error shape package, and master model-form scoreboard.
Built a sensor-by-sensor operator table, runtime legality matrix, writer-ready
equations, and a small SVG operator map.

## Observed

The existing N4 policy already marks every observed TP/TW temperature as
score-only, with `runtime_temperature_allowed=false`, `fit_allowed=false`, and
`model_selection_allowed=false`. TP sensors map naturally to 1D bulk/fluid state
at segment/fraction or junction marker. TW sensors map to 1D wall state, except
TW10, which remains excluded because the active-HX shell state is absent.

## Inferred

The measurement operator is now clear enough for thesis writing and future model
implementation: compare TP against a projected bulk/fluid state first, then
diagnose TW as a wall-response layer after the TP projection is physically
released. D2 supports the promise of this path, but it is still diagnostic.

## Contradictions or Caveats

The D2 empirical projection improves TP/TW transfer RMSE, but it is not a
released thermal-development correction. The future equation with
`Delta_T_dev_i` remains blocked until it has physical/source-bounded attribution,
same-QOI UQ, and source/property release.

## Next Useful Actions

Use this projection operator as the measurement contract for a physical
bulk-to-TP thermal-development offset proof. Do not use observed validation
temperatures as runtime inputs, and do not correct TW until the TP/bulk layer is
released.
