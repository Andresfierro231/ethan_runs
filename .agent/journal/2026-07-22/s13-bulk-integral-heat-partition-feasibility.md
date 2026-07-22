---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/partition_stability_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/energy_residual_feasibility.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_bulk_integral_heat_partition_feasibility/progression_gate.csv
tags: [journal, s13, predictive-1d, heat-partition, bulk-integral, no-fit]
related:
  - .agent/status/2026-07-22_TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22.md
  - imports/2026-07-22_s13_bulk_integral_heat_partition_feasibility.json
task: TODO-S13-BULK-INTEGRAL-HEAT-PARTITION-FEASIBILITY-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Bulk-Integral Heat-Partition Feasibility

## Attempted

Tested whether the cleanest predictive 1D path is a bulk-integral heat
partition rather than immediate exchange-cell coefficient fitting. The package
uses existing S13 heat-flow diagnostics and no new sampler, solver, UQ, or
fitting run.

## Observed

The direct wall heat fraction of source-side heat is strikingly stable across
Salt2, Salt3, and Salt4: `F_wall` ranges from about `0.13694` to `0.13896`.
This is consistent with earlier evidence that `Q_wall_W` is the only S13
exchange QOI with low medium/fine spread.

The remaining heat fraction is also stable, but it is not an admitted physical
sink. It is a named residual/throughflow/storage lane until throughflow
enthalpy, cp/property basis, and same-basis CV terms are harvested.

## Inferred

The best modeling direction is a no-fit bulk-integral partition first, then a
residual-complete open-CV energy balance. Exchange-cell coefficients should be
deferred. The current exchange enthalpy scale would require nonphysical cp
values to match direct wall or source-side heat, so coefficient fitting would
hide a conservation gap rather than improve the model.

## Caveats

`F_wall` is not admitted as a coefficient. It is a stable diagnostic target and
a reason to prioritize the next residual-complete balance study. Source-side
heat remains a distinct QOI and must not be relabeled as `Q_wall_W`.

## Next Useful Actions

Harvest or reconcile same-window throughflow enthalpy endpoints and row-specific
cp/property provenance. Then compute:

`R_E = Q_source_side_net_static_bc_W - Q_wall_W - throughflow enthalpy - storage - named losses`.

Only after that residual is bounded should the exchange-cell split be reopened.
