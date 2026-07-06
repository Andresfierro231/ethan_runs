# Salt 2 Behavior Package

This package compares the three Salt 2 3D CFD rows on shared axes and summarizes their late-window behavior.

## Scope

- `val_salt_test_2_coarse_mesh_laminar` is the native validation/continuation case and is still running.
- `viscosity_screening_salt_test_2_jin_coarse_mesh` is the staged Jin branch.
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` is the staged Kirst branch.

## Explicit validation convention

- `TW10` is intentionally excluded from RMSE-based wall metrics and combined temperature RMSE in this package and in the direct-validation package.
- Raw `TW10` error is still retained in the direct-validation CSV for transparency, but it is not used to score wall RMSE or combined RMSE.

## Data availability note

- The active `val_salt_test_2` continuation tree currently carries mdot, TP, and wall-temperature probe outputs through `1724 s`, while `wallHeatFlux` extends through about `3291 s`.
- Because of that mismatch, mdot and probe last-window statistics for `val_salt_test_2` reflect the late pre-continuation window, while ambient-loss and section-heat statistics reflect the active continuation tail.
- The generated `salt2_setup_comparison.csv` now records metric-specific end times so that this distinction is explicit.

## Key findings so far

- `val_salt_test_2` still has the best Salt 2 bulk-probe agreement: TP RMSE `2.573896609361759` K vs staged Jin `3.3697945750128784` K and staged Kirst `4.4221360873972575` K.
- `val_salt_test_2` also has the best Salt 2 mass-flow agreement: mdot absolute error `18.951017976190467`% vs staged Jin `21.65710934523809`% and staged Kirst `27.121653571428574`%.
- Under the corrected ambient-loss basis, the three Salt 2 rows are relatively close to one another on derived ambient loss: val `20.574219228738393`%, Jin `20.945467128832053`%, Kirst `20.43851841298395`% low relative to the Ethan-linked `qambient_total_W` reference.
- The strongest current explanation for the better `val_salt_test_2` behavior is the combined setup difference: thicker insulation, slightly lower cooler `h`, hotter start, Jin-type viscosity, and longer runtime.

## Recommended Salt 2 defaults for subsequent runs

- Use the `val_salt_test_2` Salt 2 setup as the default basis for future Salt 2 runs.
- Carry forward the hotter start, the thicker insulation, and the slightly lower cooler `h`.
- Keep the Jin-style viscosity branch as the starting point when mdot matching matters.
- `Cp` in `val_salt_test_2` is effectively constant `1423.47 J/kg-K`.

## Figures

- `figures/png/salt2_mdot_compare.png`: mean absolute mdot on shared axes.
- `figures/png/salt2_tp_compare.png`: `TPmean`, `TP1`, `TP4`, and `TP6` on shared axes.
- `figures/png/salt2_tw_and_ambient_compare.png`: selected wall stations (`TW5`, `TW9`) plus derived ambient-loss proxy on shared axes.
- `figures/png/salt2_section_heat_compare.png`: downcomer, heater, upcomer, test-section, and cooling-branch section totals on shared axes.

## Last-window summary

- Late-window statistics use the last `50` samples of each metric independently.
- Use `salt2_last_window_summary.csv` for mean/std/slope comparisons and `salt2_behavior_timeseries.csv` for direct follow-on analysis.

## Suggested next analysis step

- Extend this same script to compare section-wise drift rates and to derive a stricter steady-state audit from last-window slopes rather than from the coded convergence flag alone.

