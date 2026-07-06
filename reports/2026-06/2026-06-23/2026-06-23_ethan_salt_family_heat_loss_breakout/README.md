# Salt-Family Heat-Loss Breakout

Generated: `2026-06-23T12:27:31-05:00`

## Purpose

- Replace the dense all-Salt overlay with one figure per Salt family.
- Separate `net total`, `intended transfer`, and `parasitic loss` into different subplot rows.
- Make the plotted span chunks and their TP endpoint labels explicit without repeating the same labels on every subplot.

## Source

- Reuses the published June 15 field-transport campaign package at `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-15_ethan_field_transport_campaign`.
- No CFD extraction was reopened for this breakout.

## Reading Notes

- Each family figure uses solid case-colored lines only; there are no dashed or dotted role encodings.
- Left column: local signed wall heat per length `q'(s)`.
- Right column: cumulative signed wall heat `Q(s)`.
- Rows: `net total`, `intended transfer only`, `parasitic loss only`.
- A shared span guide at the top of each figure shows the full authored span and TP endpoints once for the whole canvas.
- Grey span blocks inside the plots mark the visible plotted chunk for each repaired span.
- Grey gaps between blocks indicate omitted corners, junctions, or masked / unpublished bins.

## Figure Inventory

- `Salt 1`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_family_heat_loss_breakout/figures/png/salt1_heat_loss_breakout.png`
- `Salt 2`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_family_heat_loss_breakout/figures/png/salt2_heat_loss_breakout.png`
- `Salt 3`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_family_heat_loss_breakout/figures/png/salt3_heat_loss_breakout.png`
- `Salt 4`: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/reports/2026-06-23_ethan_salt_family_heat_loss_breakout/figures/png/salt4_heat_loss_breakout.png`

## Metadata Tables

- `figure_index.csv`
- `span_chunk_map.csv`
- `summary.json`

## Span Chunks

- Spans represented: `left_lower_leg, left_upper_leg, lower_leg, right_leg, test_section_span, upper_leg`.

