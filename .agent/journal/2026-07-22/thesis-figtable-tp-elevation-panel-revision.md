---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/figure_ready_signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_TP_TW_vs_elevation/plot.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/tp_temperature_elevation_panel_points.csv
tags: [thesis, figures, tp-elevation, revision, m3]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-TP-ELEVATION-PANEL-REVISION-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_tp_elevation_panel_revision.json
task: TODO-THESIS-FIGTABLE-TP-ELEVATION-PANEL-REVISION-2026-07-22
date: 2026-07-22
role: Figures / Writer / Reviewer / Tester
type: journal
status: complete
---
# Journal: TP Elevation Panel Revision

## Attempted

Responded to the user review that
`figures/svg/m3_signed_sensor_error_shape.svg` was too cramped and visually
misleading because missing predictions made sensors appear absent. Reworked the
package around temperature versus elevation rather than signed error versus
sensor index.

## Observed

The master scoreboard contains target temperatures for all TP1-TP6 rows, but
M3 prediction values are unavailable for TP2 in Salt2, Salt3, and Salt4. The
prior signed-error figure filtered finite predictions only, so TP2 disappeared.
That was bad for a thesis figure because the physical sensor chain looked
incomplete.

## Inferred

The scientifically honest figure is a complete TP target curve with an
explicit M3 prediction gap. This preserves the evidence that M3 remains legacy
diagnostic context and avoids implying a complete TP1-TP6 predictive curve.

## Caveats

The new figures still show legacy M3 comparison values only. They are not final
predictions, not validation/holdout/external-test scores, and not closure
admissions.

## Next Useful Actions

Use the three `m3_tp_temperature_vs_elevation_salt_*.svg` files as the figure
handoff. A later redesign can either remove the old signed-error SVG from the
package or replace it with a more spacious residual-by-elevation appendix
figure, but the current primary thesis figures should be the TP elevation
exports.
