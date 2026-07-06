# 1D Model Slide Sequence

Date: `2026-06-23`

This is the focused 1D-modeling subsection for the presentation. It is based
on the current published June 23 local bakeoff and validation stack:

- `reports/2026-06-23_ethan_frozen_state_1d_validation/`
- `reports/2026-06-23_ethan_1d_closure_bakeoff/`

The exact June 23 latest-window freeze refresh is still in flight, so this
section should be presented as the current local June 23 scorecard rather than
the final refreshed external replay result.

## Slide M1: What The Current 1D Model Is Actually Being Asked To Predict

- Figure:
  `reports/2026-06-23_presentation/figures/png/07_salt_heat_loss_partition.png`
- Main claim:
  the current 1D model is being scored against frozen CFD last-window means,
  not directly against experiment
- Bullets:
  - Active solver is `tamu_loop_model_v2` in `predictive_airside_hx` mode.
  - Current defended scored scenario is
    `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
  - Heat-loss contract is `Q_lost = Q_removed + Q_ambient` on both sides.
  - Straight friction is branch-aware; direct `Nu(Re)` is defended only on
    `left_lower_leg`.
  - `upcomer` and `right_leg` are not treated as globally solved direct-closure
    lanes.
- Speaker notes:
  - Start by preventing the wrong comparison frame.
  - Say explicitly that this is CFD-to-1D validation on a pseudo-steady
    surface.
  - Use the heat-loss partition figure to remind the audience that external
    loss bookkeeping still matters to the comparison.

## Slide M2: Overall Predictiveness Is Still Not Good Enough

- Figure:
  `reports/2026-06-23_presentation/figures/png/08_primary_scenario_metric_heatmap.png`
- Main claim:
  even the best full-coverage readable 1D row still misses badly
- Bullets:
  - Best full-coverage readable scenario is
    `ethan_cfd_informed_salt_baseline_ins_1.0in_rad_1`.
  - Mean heater-normalized energy mismatch: `11.27%`.
  - Mean wall-temperature RMSE: `62.79 K`.
  - Mean centerline-temperature RMSE: `62.69 K`.
  - Mean mass-flow mismatch versus CFD: `26.69%`.
  - Result: current defended closure bundle is bounded and useful, but not yet
    predictive enough.
- Speaker notes:
  - This is the main negative-result slide.
  - Do not overcomplicate it with branch stories yet.
  - The takeaway is that the best current readable scenario still misses on all
    four observables we care about.

## Slide M3: Case-By-Case Comparison On The Strict Published Subset

- Figure:
  `reports/2026-06-23_presentation/figures/png/B_primary_best_sensor_parity.png`
- Main claim:
  the 1D model misses each currently published strict comparison case, not just
  one outlier
- Bullets:
  - Strict published comparison subset is:
    `Salt 1 Kirst`, `Salt 2 Kirst`, `Salt 2 Val`.
  - `Salt 1 Kirst`: energy `16.01%`, `T_w` RMSE `65.31 K`,
    `T_p` RMSE `65.24 K`, mdot `25.45%`.
  - `Salt 2 Kirst`: energy `8.92%`, `T_w` RMSE `64.65 K`,
    `T_p` RMSE `64.78 K`, mdot `34.41%`.
  - `Salt 2 Val`: energy `8.89%`, `T_w` RMSE `58.40 K`,
    `T_p` RMSE `58.05 K`, mdot `20.21%`.
  - The parity figure helps show that the temperature miss is systematic rather
    than a one-sensor artifact.
- Speaker notes:
  - Pair this slide with the presentation-local results table.
  - The point is that none of the published strict comparison rows are close.

## Slide M4: Why The 1D Still Misses

- Figure:
  `reports/2026-06-23_presentation/figures/png/09_primary_branch_development.png`
- Main claim:
  the current model is still too uniform for a loop whose branches develop very
  differently
- Bullets:
  - `left_lower_leg` is the only current direct developing-flow `Nu(Re)` lane.
  - `test_section_span` and `left_upper_leg` should stay on `UA'(x)` / `HTC(x)`
    state-surface treatment, not direct `Nu`.
  - `upcomer` is sensitivity-only and likely needs its own buoyancy-aware or
    convection-cell-style submodel.
  - `right_leg` / downcomer remains blocked for direct `Nu` and should stay on
    residual or lumped treatment for now.
  - The readable bundle also lacks a published globally matched `1.4 in` Salt
    scenario, so setup mismatch is still in the error budget.
- Speaker notes:
  - This is the causal slide.
  - Emphasize branch-to-branch development differences and the special role of
    the upcomer.

## Slide M5: What To Show As Setup Documentation And Next Steps

- Figure:
  `reports/2026-06-23_presentation/figures/png/10_current_1d_gap_summary.png`
- Main claim:
  we know what the model is, how it was scored, and what the next bounded fixes
  are
- Bullets:
  - Use the presentation-local setup note to document solver, closures,
    insulation, radiation, and heat-input treatment.
  - Use the presentation-local results tables to show overall scenario ranking,
    strict published case-by-case errors, and heater-to-fluid partition.
  - Immediate next fixes:
    refresh the external `Fluid` bundle,
    test a heater-to-fluid correction,
    and add an upcomer-specific submodel.
  - Current boundary:
    this is a real local negative result, but not yet the final rerun on the
    refreshed external bundle.
- Speaker notes:
  - Close this section by making the path forward concrete.
  - The important point is that the work is now diagnostic, not blind.
