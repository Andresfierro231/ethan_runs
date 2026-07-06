# Representative Salt 2 Transport Comparison

## Scope

This package compares the corrected field-reconstructed Salt 2 trio:
- `val_salt_test_2_coarse_mesh_laminar` on retained times `[8598.0, 8599.0, 8600.0, 8601.0, 8602.0]`
- `viscosity_screening_salt_test_2_jin_coarse_mesh` on retained times `[2428.0, 2429.0, 2430.0, 2431.0]`
- `viscosity_screening_salt_test_2_kirst_coarse_mesh` on retained times `[583.0, 584.0, 585.0, 586.0]`

## Method

- `major_loss_cumulative_timeseries.csv` is reduced into loopwise mean streamwise friction, direct pressure-gradient, effective HTC, thermal resistance, and momentum-resistance proxy curves.
- `boundary_layer_landmark_summary.csv` is reduced into representative landmark comparisons for `delta99_u`, `delta99_t`, and `H12`.
- `branch_thermal_summary.csv` is reduced into branch-local bulk-temperature and effective thermal comparison tables for the six repaired sections plus the derived `upcomer` branch.
- Loopwise alignment follows the per-case `loop_span_order` carried by the Salt-family case-analysis package.

## Assumptions And Limits

- Effective thermal metrics are the primary thermal comparison outputs. They inherit the package masking and thermal sanitization rules from the per-case builder.
- Boundary-layer rows are first-pass wall-to-centerline landmark samples, not a full circumferential or full-span closure model.
- Branch thermal rows reuse validated span bins. The derived `upcomer` branch concatenates `left_lower_leg`, `test_section_span`, and `left_upper_leg` while intentionally skipping corners and junctions.
- The validation case in this corrected trio may be on a later continuation-era retained window than older June 10 validation products; use the package `requested_times_s` values above when citing provenance.
- Any package row filtered out upstream by QC remains absent here; this comparison builder does not backfill missing transport data.

## Artifacts

- `representative_transport_profiles.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_representative_transport_comparison/representative_transport_profiles.csv`
- `representative_boundary_layer_landmarks.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_representative_transport_comparison/representative_boundary_layer_landmarks.csv`
- `representative_branch_thermal_summary.csv`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_representative_transport_comparison/representative_branch_thermal_summary.csv`
- `figures/`: friction/pressure, thermal/resistance, boundary-landmark, and branch-thermal overlays
