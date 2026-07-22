# Corner Pressure Drop Summary

Generated: `2026-06-25T17:43:39-05:00`

## Purpose

This package summarizes hydrostatic-corrected endpoint pressures across the
named loop corners using existing `feature_minor_loss_timeseries.csv` case-analysis
products.

## Artifacts

- `selected_case_packages.csv`: one chosen case-analysis package root per source_id
- `corner_pressure_drop_window_summary.csv`: window-averaged corner endpoint pressures and deltas
- `corner_pressure_drop_summary.json`: machine-readable run metadata

## Scope

- selected source_ids: `13`
- corner features present: `corner_lower_left, corner_lower_right, corner_upper_left, corner_upper_right`
- requested windows: `5, 10, 20` retained times

## Sign convention

- `mean_delta_p_rgh_pa = average(end_p_rgh - start_p_rgh)`
- `mean_pressure_drop_start_to_end_rgh_pa = average(start_p_rgh - end_p_rgh)`

The second quantity is included so the start-to-end pressure-drop direction is
explicit rather than inferred from a sign flip.
