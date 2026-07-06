# Salt Pressure-Closure Breakout

Generated: `2026-06-23T12:15:55-05:00`

## Purpose

- Replace the unreadable all-case straight-section pressure-closure scatter with one figure per Salt family.
- Keep each figure to at most three cases and five straight spans.
- Use one consistent hydraulic comparison basis across all spans: hydro-corrected `p` loss, endpoint `p_rgh` loss, and their residual.

## Source

- Reuses the published June 17 pressure / HTC / boundary-layer package at `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-17_ethan_pressure_htc_boundarylayer_package`.
- No CFD extraction was reopened for this breakout.

## Reading Notes

- Each figure is one Salt family only.
- Top panel: hydro-corrected pressure loss from wall `p` plus the buoyancy integral.
- Middle panel: endpoint `p_rgh` pressure loss, used because it exists on all five straight Salt spans.
- Bottom panel: closure residual between those two quantities.
- Span headers include the authored TP endpoints for the full span.

## Figure Inventory

- `Salt 1`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_pressure_closure_breakout/figures/png/salt1_pressure_closure_breakout.png`
- `Salt 2`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_pressure_closure_breakout/figures/png/salt2_pressure_closure_breakout.png`
- `Salt 3`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_pressure_closure_breakout/figures/png/salt3_pressure_closure_breakout.png`
- `Salt 4`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_pressure_closure_breakout/figures/png/salt4_pressure_closure_breakout.png`

## Metadata Tables

- `figure_index.csv`
- `span_label_map.csv`
- `pressure_closure_breakout_rows.csv`
- `summary.json`

## Span Coverage

- Straight spans represented: `left_lower_leg, left_upper_leg, lower_leg, right_leg, upper_leg`.

