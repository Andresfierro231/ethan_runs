# Ethan Transient and Axial Package

This package combines transient behavior analysis from native post-processing outputs with latest-time axial wall-transfer reductions from reconstructed `T`, `Nu`, and `wallHeatFlux` fields.

## Important limitations

- `TW10` remains excluded from RMSE scorecards elsewhere; this package still exports the raw `TW10` time history for transparency.
- Metric end times are source dependent. The active `val_salt_test_2` continuation has field and wall-heat data beyond the current probe-history horizon.
- The axial coordinate used here is ordered patch progress from 0 to 1 within each leg, not geometric arc length.
- Pressure-drop evolution is not yet reconstructed transiently here; reuse the existing June 4 section-transport package for latest-time pressure ranking.

## Cases processed

- `val_salt_test_2_coarse_mesh_laminar`: `run_status=running`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`
- `viscosity_screening_salt_test_1_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=not_steady_enough`, `usable_for_steady_state_now=no`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh`: `run_status=completed`, `essential_steadiness_class=not_steady_enough`, `usable_for_steady_state_now=no`
- `viscosity_screening_salt_test_2_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh`: `run_status=completed`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`
- `viscosity_screening_salt_test_3_kirst_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=borderline_but_usable`, `usable_for_steady_state_now=yes_with_caveat`
- `viscosity_screening_salt_test_4_kirst_coarse_mesh`: `run_status=terminated`, `essential_steadiness_class=essentially_steady`, `usable_for_steady_state_now=yes`

## Representative groups

- `salt_test_1`: manuscript representative `none yet`; sensitivity set `viscosity_screening_salt_test_1_jin_coarse_mesh; viscosity_screening_salt_test_1_kirst_coarse_mesh`
- `salt_test_2`: manuscript representative `val_salt_test_2_coarse_mesh_laminar`; sensitivity set `val_salt_test_2_coarse_mesh_laminar; viscosity_screening_salt_test_2_jin_coarse_mesh; viscosity_screening_salt_test_2_kirst_coarse_mesh`
- `salt_test_3`: manuscript representative `viscosity_screening_salt_test_3_jin_coarse_mesh`; sensitivity set `viscosity_screening_salt_test_3_jin_coarse_mesh; viscosity_screening_salt_test_3_kirst_coarse_mesh`
- `salt_test_4`: manuscript representative `viscosity_screening_salt_test_4_jin_coarse_mesh`; sensitivity set `viscosity_screening_salt_test_4_jin_coarse_mesh; viscosity_screening_salt_test_4_kirst_coarse_mesh`

## Pressure-drop context reused here

- `val_salt_test_2_coarse_mesh_laminar`: `upper_leg_abs_delta_p_rgh_pa=36.74926249`, `left_leg_abs_delta_p_rgh_pa=15.473324062`, `right_leg_abs_delta_p_rgh_pa=9.621540102`
- `viscosity_screening_salt_test_3_jin_coarse_mesh`: `upper_leg_abs_delta_p_rgh_pa=38.022483570000006`, `left_leg_abs_delta_p_rgh_pa=15.213591897`, `right_leg_abs_delta_p_rgh_pa=9.653894862000001`
- `viscosity_screening_salt_test_4_jin_coarse_mesh`: `upper_leg_abs_delta_p_rgh_pa=38.42732622`, `left_leg_abs_delta_p_rgh_pa=15.272479906`, `right_leg_abs_delta_p_rgh_pa=11.055311839`

## Output files

- `all_salt_transient_timeseries.csv`: long-form transient metrics for all salt cases.
- `all_salt_transient_last_window.csv`: trailing-window steadiness statistics for all exported metrics.
- `all_salt_axial_patch_heat_timeseries.csv`: long-form patchwise wall-heat histories from `wallHeatFlux.dat`.
- `all_salt_axial_patch_latest.csv`: latest-time patchwise wall-heat rows augmented with area-averaged `T`, `Nu`, and `wallHeatFlux`.
- `all_salt_axial_leg_summary.csv`: aggregated axial summaries by case, leg, and thermal role.
- `representative_transient_summary.csv`: manuscript-facing summary rows for the selected representative and sensitivity cases.
- `figures/png/*_transient_*.png` and `figures/png/*_axial_*.png`: shared-axis comparison plots by base case.
