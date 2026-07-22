---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_upcomer_matched_plane_relaunch_package/parsed
tags: [pm10, pressure, residual-target, upcomer, recirculation]
date: 2026-07-20
type: work_product
status: active
---
# PM10 Same-Window Residual Targets

This package derives same-window PM10 pressure targets from the matched-plane
VTK samples already produced by the PM10 extraction path. The target is a
partial pressure residual:

`p_rgh(outlet) - p_rgh(inlet) - (q_dynamic(outlet) - q_dynamic(inlet))`

It is diagnostic-only because straight/development component isolation and
mesh/time uncertainty are still missing. It is suitable for PM10
recirculation-aware residual ranking, but not for ordinary pipe fitting,
component `K`, model-selection admission, or runtime-input use.
