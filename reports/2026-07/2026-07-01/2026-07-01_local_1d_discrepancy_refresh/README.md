# Ethan 1D Discrepancy Explainer — Latest Window

Generated: `2026-07-01T16:08:01-05:00`

## Scope

- This package explains the defended local 1D-vs-CFD gaps on the June 23
  latest-window nominal Salt Jin surface.
- Inputs:
  `2026-06-23_ethan_frozen_state_results_latest_window`,
  `2026-06-23_ethan_frozen_state_1d_validation_latest_window`,
  `2026-06-23_ethan_1d_closure_bakeoff_latest_window`.

## Defended latest-window error level

- Mean |energy| mismatch: `11.53%` of heater.
- Mean wall-temperature RMSE: `65.38 K`.
- Mean centerline-temperature RMSE: `64.88 K`.
- Mean mass-flow mismatch: `28.87%` vs frozen CFD.

## Supported explanations

- `upcomer_requires_separate_model`: Upcomer stays on a sensitivity-only fit lane while right_leg/downcomer stays excluded, and the mean upcomer-minus-downcomer HTC contrast remains 91.78 W/m2-K on the defended latest-window cases.
- `heat_partition_not_matched_case_by_case`: The defended 1D rows still miss the frozen CFD heat partition: mean removed-duty gap = -91.46 W, mean ambient gap = 63.53 W, mean |total-loss error| = 11.53% of heater.
- `mass_flow_gap_tracks_hydraulic_underclosure`: Mean defended mass-flow error remains 28.87% vs frozen CFD while the downcomer direct thermal lane is still blocked and the upcomer direct lane is not defended.

## Boundary

- This package explains the current local defended surface only.
- It does not replace the still-stale external June 19 `Fluid` bundle.
- The insulation mismatch note remains a possible setup explanation, not a
  proven dominant cause, until a readable globally matched `1.4 in` Salt
  scenario exists on disk.
