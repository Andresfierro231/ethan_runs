---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_window_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/same_qoi_temporal_uq_case_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus/production_readiness_gate.csv
tags: [s13, upcomer-exchange, same-qoi-uq, temporal-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-SAME-QOI-NEIGHBOR-UQ-AFTER-TARGET-PLUS-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_same_qoi_neighbor_uq_after_target_plus.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/README.md
task: TODO-S13-UPCOMER-EXCHANGE-SAME-QOI-NEIGHBOR-UQ-AFTER-TARGET-PLUS-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Same-QOI Neighbor UQ After Target-Plus

## Attempted

Ran the first actual S13 same-QOI temporal UQ execution after target-plus rows
became available. The calculation used the complete triplet table from the
target-plus same-QOI harvest and preserved identical labels, formula basis, and
sign convention. A heat-flow matching diagnostic was added after temporal UQ to
compare direct `Q_wall_W`, source-side static heat, and the current
`mdot_exchange * DeltaT_wall_core` scale.

## Observed

All `12` case/QOI rows had finite target-minus, target, and target-plus values.
The conservative uncertainty uses the larger of the absolute target-minus and
target-plus deltas, with half-range and relative percent reported as secondary
diagnostics.

All four requested QOI labels executed successfully. The largest relative
temporal neighbor-window uncertainty was about `0.81 %`, from the Salt4
exchange proxy and residence-time proxy rows. Direct `Q_wall_W` was much more
stable over the retained three-window span.

The heat-flow comparison does not match: direct `Q_wall_W` is about `14 %` of
the source-side static heat-flow fallback, leaving `143-177 W` of source-minus-
wall heat by case. The current exchange `mdot*DeltaT` scale is so small that
matching even direct `Q_wall_W` through it would imply heat-capacity-scale values
of order `2.15e6-6.05e6 J/kg/K`.

## Inferred

The S13 blocker has moved from missing temporal neighbor-window evidence to the
mesh/GCI gate and a physical energy-residual definition. The mesh/GCI row can
now be claimed from a complete temporal UQ input package, but it must still fail
closed if no same-label mesh family exists. The heat-flow mismatch should not be
closed by fitting a multiplier; it needs a same-mask exchange-cell energy
balance with released `cp`/property basis and harvested `T_recirc`/core enthalpy
terms.

## Caveats

This row does not admit any coefficient. The exchange and residence-time rows
remain diagnostic proxies, not production release rows. The target-plus fields
were staged continuation outputs. No source-side heat-flow quantity was
relabeled as `Q_wall_W`. The heat-flow diagnostic is not a production residual
release.

## Next Useful Actions

Claim the S13 Qwall/exchange mesh/GCI UQ gate. It should consume this temporal
UQ package plus the Phase B mesh/GCI evidence matrix and decide whether the four
QOI labels have same-label mesh/GCI support. If not, publish a precise missing
mesh-family blocker and keep production harvest closed. In parallel, prepare the
production energy-residual contract: exact signs, `cp_J_kg_K` source/property
provenance, `T_recirc` definition, and exchange enthalpy term on the same mask
and time basis.
