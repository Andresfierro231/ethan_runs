---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/heat_flow_match_diagnostics.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/qoi_mesh_disposition_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_coarse_equivalence_open_cv_heatflow_contract/open_cv_use_policy.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/field_release_contract.csv
tags: [work-product, s13, predictive-1d, heat-partition, bulk-integral, no-fit]
related:
  - .agent/status/2026-07-22_TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22.md
  - .agent/journal/2026-07-22/s13-bulk-integral-heat-partition-feasibility.md
task: TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Bulk-Integral Heat-Partition Feasibility

Decision: `bulk_integral_heat_partition_feasible_diagnostic_no_fit_residual_next`.

This package keeps the predictive 1D target conservative: averaged states may
drive future formulas, but `Q_wall_W`, source-side heat flow, exchange enthalpy
scale, and energy residual remain integral outputs.

The highest-value direction is a no-fit bulk heat partition first:
`Q_wall_model = F_wall * Q_source_side_net_static_bc_W`, with residual ownership
kept explicit. Current `F_wall` is stable across Salt2/Salt3/Salt4, but it is
not admitted as a coefficient because source/property, same-basis energy
residual, and formal release gates remain closed.
