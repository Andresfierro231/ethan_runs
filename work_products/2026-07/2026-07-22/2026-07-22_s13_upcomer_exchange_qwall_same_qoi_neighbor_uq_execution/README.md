---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/trusted_wall_Q_wall_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/diagnostic_average_exchange_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/neighbor_window_requirements.csv
tags: [s13, upcomer-exchange, qwall, same-qoi-uq, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_S13_UPCOMER_EXCHANGE_TOMORROW_CONTEXT_HANDOFF.md
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: work_product
status: complete
---
# S13 Qwall Same-QOI Neighbor UQ Execution

Decision: `fail_closed_neighbor_window_uq_missing`.

This package answers one question: do exact target-minus / target /
target-plus rows exist for the requested S13 QOI labels?

- cases inventoried: `3`
- QOI labels inventoried: `4`
- target-window rows present: `12`
- target-minus rows present: `0`
- target-plus rows present: `0`
- same-QOI neighbor UQ-ready labels: `0`
- move to mesh/GCI UQ allowed now: `false`
- production harvest allowed now: `false`

Target-window values exist, including direct trusted-wall `Q_wall_W`, but exact
same-label neighboring windows are absent. This row therefore publishes a clean
fail-closed thesis result and does not run mesh/GCI, sampler, production harvest,
UQ execution, fitting, validation scoring, or admission.
