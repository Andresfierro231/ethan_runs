---
provenance:
  task: TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21
  sources:
    - work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/sensor_tp2_tw10_policy_refresh.csv
    - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_projected_sensor_registry.csv
tags:
  - thesis
  - sensor-map
  - handoff
related:
  - .agent/status/2026-07-21_TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21.md
---
# Thesis Study S7 Sensor Map TP/TW Contract

Task: TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21

## Attempted

I implemented the S7 package as a reproducible work-product-local build/check pair because preflight showed broad open `tools/analyze/` ownership from future S8-S11 and same-QOI rows. I used the existing sensor-policy refresh, TP2 projected registry, sensor-level error rows, TP2 evidence, staged Salt2 TP/TW probe locations, and S6 split-role shell as read-only inputs.

## Observed

The primary policy has 17 TP/TW rows. TP2 is restored to aggregate scoring after projection/source-segment/finite-prediction gates, while TW10 remains excluded because the current 1D model does not emit an active heat-exchanger shell state. The projected registry provides provisional coordinates, not exact experimental measurements; the staged native TP/TW probe file provides coordinate centroids for cross-checking but does not supersede the provisional status.

## Inferred

The thesis-safe interpretation is to treat TP/TW positions as score-location metadata and to keep temperature values as post-solve targets only. TP2 can be mapped to the right-downcomer/bottom-horizontal junction for score reporting. Most other sensors are bounded rather than exact because the coordinate source remains provisional. TW10 must stay excluded until an explicit shell-state model or permanent exclusion policy is produced.

## Caveats

The package does not claim final predictive accuracy and does not admit any closure coefficient. It also does not edit Fluid sensor files or external repositories. Temperature-probe residual claims should remain secondary to energy balance and branch heat parity.

## Next Useful Actions

Use this package as the source for the S7 figure/table overlay row. If stronger coordinate claims are needed, open a new row to obtain or audit exact experimental sensor-survey evidence. If TW10 is needed in a future aggregate score, first add or prove an active heat-exchanger shell output in the 1D model under a separate row.
