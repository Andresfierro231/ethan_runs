---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/diagnostic_roi_average_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/proxy_admission_support_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/diagnostic_roi_average_bridge.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge/no_mutation_guardrails.csv
tags: [journal, s13, upcomer-exchange, diagnostic-proxy, roi-average, no-admission]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_diagnostic_roi_average_bridge.json
task: TODO-S13-UPCOMER-EXCHANGE-DIAGNOSTIC-ROI-AVERAGE-BRIDGE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Diagnostic ROI-Average Bridge

## Attempted

Closed a diagnostic-only bridge from existing blocked S13 evidence. The package
carries a dominant-component ROI-average bridge that combines selected mask
cells, cell volumes, VTK `T`/`rho`, topology diagnostic interface area, and
static source/sink terms.

## Observed

The dominant-component bridge gives Salt2/Salt3/Salt4 proxy exchange mass
flows of `0.0805548458516`, `0.0964918191233`, and `0.109435101294 kg/s`.
The corresponding residence proxies are `1.38090988886`, `1.18344032993`, and
`1.04676755296 s`; static net heat proxies are `166.349260094`,
`183.730361326`, and `205.373184962 W`. Trends are internally consistent:
proxy exchange mass flow and reverse-region temperature rise with case
intensity while proxy residence time falls. `Q_wall_W` remains unavailable and
every row carries a non-admission label.

## Inferred

The bridge preserves useful scale information for writing and future method
design, but it does not unlock S13 production harvest. The ROI masks remain
geometrically blocked and must not be treated as released exchange cells.

## Contradictions Or Caveats

The dominant-component basis is still geometrically blocked and is not a
face-integrated mass flux. The effective source indicators are not coefficients
and cannot be fitted.

## Next Useful Actions

1. Define a geometry-backed right-leg/upcomer seed before any new CV release
   attempt.
2. Keep S13 production harvest and same-window UQ disabled until source-bounded
   geometry releases.
3. Use this package only as diagnostic scale context in thesis/report prose.
