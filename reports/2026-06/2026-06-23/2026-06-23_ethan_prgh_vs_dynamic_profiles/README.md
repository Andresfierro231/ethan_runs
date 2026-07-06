# Ethan p_rgh Versus Dynamic Pressure Profiles

Generated: `2026-06-23T11:05:55-05:00`

## What These Curves Mean

- `p_rgh(s)` is the hydrostatic-corrected pressure field reduced along each repaired leg.
- `q_dyn(s) = 0.5 * rho_bulk(s) * U_bulk(s)^2` is the local kinetic pressure scale, not the pressure field itself.
- Overlaying them does **not** mean they should match pointwise.
- Instead:
  - use `p_rgh(s)` to inspect streamwise pressure-drop shape and sign
  - use `q_dyn(s)` to judge the size of local loss scales relative to the available velocity head

## Developing-Flow Interpretation

- In a fully developed straight segment, `p_rgh(s)` tends toward a more nearly linear streamwise drop and `q_dyn(s)` tends to vary more slowly with `s`.
- In a developing segment, the wall shear and bulk-speed surrogate can still evolve with distance, so both the `p_rgh` slope and `q_dyn` level can move with `s`.
- Bends, corners, transitions, and the test section can reset or disturb development; after those features, the downstream straight may show a redevelopment zone rather than an immediately settled friction trend.
- That is why this package should be read together with the existing direct/shear friction and boundary-layer products rather than as a standalone loss model.
- Some `q_dyn(s)` traces still look visibly jagged because the preserved streamwise-bin reduction can alternate between a few discrete `bulk_velocity_m_s` values from bin to bin. That sawtooth is a reduction artifact of the coarse retained bins, not evidence that the underlying pressure field itself is oscillating at that visual frequency.

## Scope

- cases processed: `13`
- maximum reported dynamic pressure: `2.305 Pa`
- mean absolute retained-time end-to-start `p_rgh` change by span: `12.335 Pa`

## Primary Artifacts

- `prgh_vs_dynamic_profile_rows.csv`
- `prgh_vs_dynamic_profile_summary.csv`
- `figure_index.csv`
- `summary.json`
- `figures/png/*_prgh_vs_dynamic_by_leg.png` plus matching `svg` / `pdf`

## How The Mean Curves Are Built

- The faint lines in each panel are the individual retained-time traces read
  directly from `major_loss_cumulative_timeseries.csv`.
- The dark mean curves are not spanwise moving averages and they are not
  smoothed splines.
- For each case, each span, and each `bin_index`, the builder groups together
  all retained-time rows that share that same `(span_name, bin_index)` pair.
- At that fixed bin location:
  - plotted `x` position = arithmetic mean of `s_mid_m` over the retained-time
    rows in that bin
  - mean `p_rgh` curve value = arithmetic mean of
    `p_rgh_wall_area_avg_pa` over those retained-time rows
  - mean `q_dyn` curve value = arithmetic mean of `dynamic_pressure_pa` over
    those retained-time rows
  - shaded band = retained-time min and max at that same `(span_name,
    bin_index)` group
- In other words, the figure mean is a retained-time ensemble mean evaluated
  bin-by-bin, not a smoothing pass along `s`.

## How The Summary Mean Is Built

- The reported `mean absolute retained-time end-to-start p_rgh change by span`
  is a separate scalar summary, not the same operation as the plotted dark
  curve.
- For each retained time and each span, the builder:
  - sorts the span rows by `bin_index`
  - finds the first finite `p_rgh_wall_area_avg_pa` row in that retained-time
    span
  - finds the last finite `p_rgh_wall_area_avg_pa` row in that retained-time
    span
  - computes `end p_rgh - start p_rgh`
  - takes the absolute value
- The README summary value is then the arithmetic mean of those per-time,
  per-span absolute end-to-start changes over the package.

## Major / Minor Loss Context

- The straight-leg major-loss path is already much more mature than the corner/bend minor-loss path.
- Major-loss interpretation uses the preserved streamwise `p_rgh` gradients, direct/shear Darcy comparisons, and boundary-layer context on repaired major spans.
- Minor-loss interpretation at bends and corners is still a defended patch-endpoint decomposition plus adjacent-straight reference, not a continuous feature-volume field integral.
