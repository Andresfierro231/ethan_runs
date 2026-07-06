# Plot And Term Guide

This document explains the main plots in `reports/2026-06-04_ethan_transient_axial_package/`, the quantities on those plots, and how they should be used in a scientific and numerical analysis.

## Global terms

- `TP1..TP6`: bulk-fluid temperature probes sampled in the loop.
- `TW1..TW11`: wall-temperature stations. `TW10` is exported for transparency but remains excluded from RMSE scorecards elsewhere.
- `|mdot| mean`: mean absolute loop mass flow from the monitored face zones.
- `Ambient proxy`: derived ambient-like loss reconstructed from `wallHeatFlux.dat`, including passive loss channels and cooling-branch excess beyond the operating-point cooler duty.
- `Net total Q`: signed all-wall total from `total_Q.dat`. A small late-time value means the residual enthalpy imbalance is small.
- `Ordered patch progress`: normalized patch index from 0 to 1 within a leg. It preserves patch ordering but is not a geometric arc length.
- `Nu`: patch-averaged Nusselt number from the reconstructed latest-time field when `foamPostProcess` could read `T` and `Nu` cleanly.

## Plot guide

### `metric_coverage_end_times.png`

Shows the latest available time for each primary transient metric by case. It reveals where continued wallHeatFlux data exist beyond probe histories.

Terms:
- `TP mean` is the mean of the six bulk temperature probes `TP1..TP6`.
- `Ambient proxy` is the derived ambient-like loss from wallHeatFlux accounting.
- `Net total Q` is the signed all-wall total from `total_Q.dat`; small late values indicate a small residual enthalpy imbalance.

### `salt_test_*_transient_tail.png`

Late-window tail comparison for mass flow, bulk temperature, ambient-loss proxy, and net heat balance. Use this for numerical steadiness rather than full-transient storytelling.

Terms:
- The x-axis is truncated to the last 80 samples available for each case and metric.
- The corresponding late-window slopes are summarized numerically in `case_audit_summary.csv`.

### `salt_test_*_axial_temperature_profile.png`

Latest-time ordered-patch wall-temperature profile along each leg when reconstructed `T` was readable.

Terms:
- `Ordered patch progress` is a normalized patch index from 0 to 1 within a leg; it is not a geometric arc length.
- Missing curves mean the case fell back to q-only axial reporting because `foamPostProcess` could not read reconstructed `T` cleanly.

