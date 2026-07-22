---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/topology_cv_case_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/source_sink_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
tags: [s13, upcomer-exchange, diagnostic-proxy, roi-average, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/diagnostic_roi_average_bridge.csv
task: TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_diagnostic_only
---
# S13 Diagnostic ROI-Average Bridge

This package computes a diagnostic-only ROI-average fallback from the blocked
dominant reverse-flow component. It is intended to preserve useful scale
information while keeping S13 production harvest, UQ, fitting, S11/S15/S6, and
exchange-cell admission disabled.

Decision: `complete_diagnostic_only_no_release`.

- cases processed: `3`
- diagnostic proxy rows: `3`
- proxy support rows: `15`
- admission rows released: `0`
- surface extraction allowed: `false`
- harvest/UQ allowed: `false`

The proxy uses volume-weighted ROI `U`, `T`, and `rho`, topology diagnostic
interface area, and static source/sink terms. `Q_wall_W` remains unavailable
because no trusted wall/core band or wallHeatFlux integration is released.
Effective indicators such as `q_net_per_V_W_m3` and
`q_net_over_mdot_proxy_J_kg` are not coefficients and must not be fitted.
