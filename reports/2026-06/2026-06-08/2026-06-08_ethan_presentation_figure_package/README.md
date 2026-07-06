# Ethan Presentation Figure Package

Generated: `2026-06-08T13:44:25-05:00`

This package repackages the June 4-8 Ethan analysis products into a compact presentation-oriented figure set.

## Figure set

- `representative_branch_pressure_drop`
- `jin_vs_kirst_delta_dashboard`
- `representative_heat_balance_partition`
- `late_window_steadiness_dashboard`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh_temperature_slice`
- `viscosity_screening_salt_test_1_kirst_coarse_mesh_velocity_slice`
- `val_salt_test_2_coarse_mesh_laminar_temperature_slice`
- `val_salt_test_2_coarse_mesh_laminar_velocity_slice`
- `viscosity_screening_salt_test_3_jin_coarse_mesh_temperature_slice`
- `viscosity_screening_salt_test_3_jin_coarse_mesh_velocity_slice`
- `viscosity_screening_salt_test_4_jin_coarse_mesh_temperature_slice`
- `viscosity_screening_salt_test_4_jin_coarse_mesh_velocity_slice`

## Representative cases

- `salt_test_2` -> `val_salt_test_2_coarse_mesh_laminar`
- `salt_test_3` -> `viscosity_screening_salt_test_3_jin_coarse_mesh`
- `salt_test_4` -> `viscosity_screening_salt_test_4_jin_coarse_mesh`

## Inputs reused

- `reports/2026-06-04_all_salt_behavior_package/representative_case_selection.csv`
- `reports/2026-06-04_all_salt_behavior_package/jin_vs_kirst_summary.csv`
- `reports/2026-06-04_all_salt_behavior_package/all_salt_case_status.csv`
- `reports/2026-06-04_ethan_section_transport_package/section_pressure_drops.csv`
- `reports/2026-06-04_ethan_section_transport_package/representative_section_summary.csv`
- `reports/2026-06-04_ethan_transient_axial_package/all_salt_transient_last_window.csv`
- `reports/2026-06-04_ethan_transient_axial_package/all_salt_axial_leg_summary.csv`

## Notes

- The branch-pressure figure uses latest-time section `|Δp_rgh|` rankings, not full transient `Δp_rgh(t)` histories.
- The reused June 4 transient-axial package already provides `Nu(x)` and `q''(x)` style plots; it does not yet provide a separately derived `HTC(x)` curve.
- The slice figure set now carries the individual stamped temperature and velocity files directly, avoiding blurry composite PDFs.
- Salt 1 is included in the steadiness dashboard as a caution row, not as a steady-state representative.
