---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_TP_TW_vs_elevation/plot.py
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_sensor_predictions_experimental.csv
  - reference/geometry_reference.md
tags: [thesis, figures, tp-tw, reference-geometry, experimental-targets, signed-error]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-REFERENCE-GEOMETRY-EXPERIMENTAL-TARGET-PANEL-CORRECTION-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_reference_geometry_experimental_target_panel_correction.json
task: TODO-THESIS-FIGTABLE-REFERENCE-GEOMETRY-EXPERIMENTAL-TARGET-PANEL-CORRECTION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal

## Attempted

Revisited the thesis model-form figure/table panel package after review showed
that the TP/TW target temperatures and elevation basis were wrong. Inspected the
reference TP/TW plot script, the reference geometry note, the master scoreboard,
and the experimental validation target table.

## Observed

The prior package used `target_K` from the master scoreboard as the plotted
temperature target and S7/native sensor y as the plotted elevation. Those values
do not match the reference plot or the experimental Fluid validation table. For
example, Salt2 TW5 is `471.69 K` in the experimental validation target table but
`442.329709555 K` in the master-scoreboard target column.

The reference plot uses absolute probe coordinates shifted by the TP2 coordinate
so TP2 is the zero-elevation datum. The corrected elevations include Salt2 TP1
at `0.9144 m`, TP2 at `0.0 m`, TP6 at `1.227143219056991 m`, and TW5 at
`0.156371609528495 m`.

## Inferred

The master scoreboard is still the right source for M3 predicted temperatures,
legacy mode labels, admission status, and provenance, but its `target_K` column
should not be the plotted experimental target for this thesis figure. The
correct data contract is to plot experimental targets and M3 predictions, while
preserving the scoreboard target as an audit column.

## Changed

Updated the builder to load `F0_current_fluid_sources` rows from
`forward_v0_sensor_predictions_experimental.csv`, validate all 51 Salt2/Salt3/
Salt4 TP/TW sensor targets, and write those as plotted `target_K` values.

Updated the builder to use reference-geometry elevations from the reference
plot's `Y_ABSOLUTE_M` constants shifted by TP2. S7/N4 metadata remains attached
as caveat/projection context, but it is no longer the plotted elevation basis.

Updated the signed-error panel to recompute M3 signed error against experimental
targets and to use a wider, less cramped axis with separate TP/TW x positions
and broken line segments at missing TP2 and TW10.

## Validation

`python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
passed after regeneration. The test now asserts concrete experimental target
values, reference-geometry elevations, TW10 unplotted preservation, and
audit-only scoreboard target columns.

## Next Useful Actions

Use the corrected temperature-vs-elevation panels as the preferred thesis figure
asset for M3 diagnostic shape discussion. Keep the signed-error panel as a
secondary appendix-style diagnostic. Do not use either figure to claim final
predictive accuracy or closure admission.
