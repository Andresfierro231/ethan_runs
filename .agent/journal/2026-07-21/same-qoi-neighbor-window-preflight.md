---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_neighbor_window_preflight/README.md
tags: [journal, same-qoi-uq, neighboring-window]
related:
  - .agent/status/2026-07-21_TODO-SAME-QOI-NEIGHBOR-WINDOW-PREFLIGHT-2026-07-21.md
  - imports/2026-07-21_same_qoi_neighbor_window_preflight.json
task: TODO-SAME-QOI-NEIGHBOR-WINDOW-PREFLIGHT-2026-07-21
date: 2026-07-21
role: cfd-pp/Mesh-GCI/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Same-QOI Neighboring-Window Preflight

## Attempted

Converted the completed Phase A/B/C same-QOI UQ tables into an implementation
queue that separates immediate pressure/F6 preflights from exchange/terminal
harvest gates and thermal/heat-loss policy gates.

## Observed

No row has both accepted neighboring-window evidence and accepted same-QOI
mesh/GCI support. Several rows have retained-time evidence, but that is not
sufficient for admission.

## Inferred

The next useful compute-facing work should start with P1 pressure/F6 rows. The
upcomer exchange rows should wait for Salt2 cell VTK smoke and then for exchange
interface/wall-core geometry release.

## Caveats

This row did not inspect native CFD fields, launch samplers, compute drift, or
change admission state.
