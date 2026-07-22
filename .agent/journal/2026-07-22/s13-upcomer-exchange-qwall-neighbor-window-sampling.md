---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/neighbor_time_selection.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_neighbor_window_rows.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_uq_matrix.csv
tags: [s13, upcomer-exchange, qwall, neighbor-window, same-qoi-uq]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling.json
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Qwall Neighbor-Window Sampling

## Attempted

Built a narrow sampler that reads existing collated OpenFOAM fields and the
trusted S13 geometry manifests to fill the immediate target-minus window for
four exact S13 QOI labels: `Q_wall_W`,
`mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
`wall_core_bulk_temperature_contrast_K`.

## Observed

The stored native windows immediately before the targets are available:
Salt2 `7914`, Salt3 `7617`, and Salt4 `9999`. The sampler produced target-minus
rows for all `12` requested case/QOI combinations and joined them to the
existing `12` target rows.

No target-plus rows exist in the current native source tree. Salt2 target
`7915`, Salt3 target `7618`, and Salt4 target `10000` are each the latest
stored `processors64` time directory.

## Inferred

This is a useful partial unlock, but it is not enough for same-QOI neighbor UQ.
The scientific gate still fails closed because one-sided target-minus evidence
cannot replace the required target-minus / target / target-plus window triplet.

## Caveats

The row did not run OpenFOAM, launch a scheduler job, run production harvest,
execute UQ, admit a coefficient, release source/property evidence, edit thesis
current files, or mutate native outputs or registry/admission state. The user
typed `wall_core_bulk_temperature_contrast_L`; this package treats that as the
established `_K` label.

## Next Useful Actions

Find or generate later target-plus windows for Salt2/Salt3/Salt4 with the same
QOI labels, formulas, sign conventions, and geometry basis. After that, rerun
same-QOI neighbor UQ. Mesh/GCI UQ and production harvest should remain closed
until the target-plus gap is resolved.
