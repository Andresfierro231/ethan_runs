# modern_runs

`jadyn_runs/modern_runs/` is the local campaign workspace for the
`~/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/` intake.

## Role

- Keep a dated inventory of source visibility and permissions.
- Separate campaign-level documentation from per-case extraction products.
- Define a deterministic staging order before large copies or QoI extraction.
- Preserve exact source paths for every discovered case.

## Current campaign split

- `salt/`: 8 cases, organized as a viscosity-screening sweep over tests `1-4`
  with `jin` and `kirst` salt-property variants.
- `water/`: 8 cases, organized as tests `1-4` with `laminar` and
  `kOmegaSSTLM` turbulence-model variants.

## Current state on 2026-06-01

- Inventory pass completed.
- Source permissions are still changing because an external `chmod` pass is in
  progress.
- All 8 salt cases are readable enough for extraction planning.
- 2 water laminar cases are fully readable, 3 water cases are partially
  readable, and 3 water cases remain blocked in this snapshot.

## Next use

- Use `2026-06-01_source_inventory/` as the canonical intake snapshot for this
  batch.
- Re-run the same inventory after permissions settle before registering every
  case into the extraction pipeline.
