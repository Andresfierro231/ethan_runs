---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/target_plus_qoi_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_window_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/production_readiness_gate.csv
tags: [s13, upcomer-exchange, target-plus, same-qoi-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/README.md
task: TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-SAME-QOI-HARVEST-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Target-Plus Same-QOI Harvest

## Attempted

Harvested target-plus samples from the staged Salt2/Salt3/Salt4 continuation
windows generated earlier today. The builder reused the trusted exact-Qwall and
neighbor-window sampling code so the target-plus rows use the same QOI labels,
geometry basis, formulas, and sign conventions as the existing target and
target-minus rows.

## Observed

All three staged target-plus windows contained the required `U`, `T`, `rho`,
and `wallHeatFlux` fields. The harvest produced `12` target-plus QOI rows and
joined them with `12` existing target-minus/target rows.

All four QOI labels now have complete Salt2/Salt3/Salt4 triplets:

- `Q_wall_W`
- `mdot_exchange_positive_outward_proxy_kg_s`
- `tau_recirc_proxy_s`
- `wall_core_bulk_temperature_contrast_K`

## Inferred

The next S13 blocker is not missing target-plus data. Same-QOI neighbor-window
UQ can now be executed from the complete triplet matrix. Production harvest is
still closed because same-QOI UQ and mesh/GCI UQ have not passed.

## Caveats

The target-plus rows are sampled from staged continuation outputs, not native
source-case outputs. This row did not run a solver, sampler, production
harvest, UQ calculation, mesh/GCI calculation, admission, thesis edit, registry
edit, or blocker-register change. `Q_wall_W` remains a trusted wall
`wallHeatFlux` integral row, not a source-side relabel.

## Next Useful Actions

Claim a separate same-QOI neighbor-window UQ execution row. It should consume
`same_qoi_neighbor_window_rows.csv`, compute window-to-window uncertainty for
the four labels, emit a fail-closed UQ table, and only then decide whether the
mesh/GCI UQ row can start. Production harvest remains a later gate.
