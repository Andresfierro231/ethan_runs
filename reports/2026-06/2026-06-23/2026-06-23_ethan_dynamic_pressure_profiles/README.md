# Ethan Dynamic Pressure Profiles

Generated: `2026-06-23T10:48:40-05:00`

## What This Package Answers

- `p_rgh` is available in the preserved streamwise-bin artifacts, but it is **not** dynamic pressure.
- In this workspace, `p_rgh` means pressure with the hydrostatic head removed.
- True dynamic pressure is derived here as `q_dyn = 0.5 * rho_bulk * U_bulk^2` using the preserved streamwise-bin `rho_bulk_kg_m3` and `bulk_velocity_m_s` fields.
- This package publishes `q_dyn(s)` as a function of distance through each repaired major leg for every case present in the June 17 pressure / HTC / boundary-layer package index.

## Relationship To The Later Overlay Package

- This package is the `q_dyn(s)`-only view.
- The paired overlay requested later in the day lives at `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_prgh_vs_dynamic_profiles`.
- Use that later package when you want `p_rgh(s)` shown alongside `q_dyn(s)` on the same span plot.

## Scope

- cases processed: `13`
- families present: `salt, water`
- maximum reported dynamic pressure: `2.305 Pa`

## Primary Artifacts

- `dynamic_pressure_profile_rows.csv`
- `dynamic_pressure_profile_summary.csv`
- `summary.json`
- `figures/png/*_dynamic_pressure_by_leg.png` plus matching `svg` / `pdf`

## Method Boundary

- `q_dyn` here is a postprocessed bulk surrogate built from the preserved case-analysis bin reductions.
- It uses the same reduced `rho_bulk_kg_m3` and `bulk_velocity_m_s` already used elsewhere in the hydraulic packages.
- It is therefore appropriate for the current repo’s internal hydraulic comparisons, but it is not a direct raw-cell field integral or a separate solver output.
- The visible sawtooth in some legs is a bin-reduction artifact: adjacent streamwise bins can reuse two or a few discrete bulk-velocity values, so `q_dyn = 0.5 rho U^2` flips between those levels instead of tracing a visually smooth field sample.
