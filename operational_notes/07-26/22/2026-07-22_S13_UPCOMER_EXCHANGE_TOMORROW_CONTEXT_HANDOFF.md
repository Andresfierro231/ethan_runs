---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/trusted_wall_Q_wall_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/summary.json
tags: [s13, upcomer-exchange, qwall, same-qoi-uq, tomorrow-handoff]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-TOMORROW-CONTEXT-HANDOFF-2026-07-22.md
  - operational_notes/07-26/22/2026-07-22_S13_UPCOMER_EXCHANGE_LIMITED_SAMPLED_FIELD_EVIDENCE_SYNTHESIS.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/README.md
task: TODO-S13-UPCOMER-EXCHANGE-TOMORROW-CONTEXT-HANDOFF-2026-07-22
date: 2026-07-22
role: Coordinator / Writer / Reviewer
type: operational_note
status: complete
---
# S13 Upcomer Exchange Tomorrow Context Handoff

## Why This Exists

This note records the current S13 upcomer-exchange context, progress, claim
boundaries, and next task order so the thread can resume without chat logs.
The important state change is that S13 moved from a documented source-side
heat-flow fallback toward a stronger direct target-window `Q_wall_W` path, but
production harvest and coefficient admission are still closed.

## Open First

1. `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/trusted_wall_Q_wall_summary.csv`
3. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/README.md`
4. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/production_readiness_gate.csv`
5. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/same_qoi_uq_matrix.csv`
6. `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/README.md`
7. `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/sampled_field_summary.csv`

## Current State

The exact pressure/Qwall package released target-window inputs for the three
seeded cases:

| Case | Target time/window | `Q_wall_W` | Status |
| --- | ---: | ---: | --- |
| `salt_2` | `7915` | `23.1161370708` | released with tiny NCC patch-label mismatch below tolerance |
| `salt_3` | `7618` | `25.3465488205` | released with tiny NCC patch-label mismatch below tolerance |
| `salt_4` | `10000` | `28.1231837021` | released with tiny NCC patch-label mismatch below tolerance |

The sign convention is fixed: positive `Q_wall_W` adds heat to the seeded
recirculation fluid. The native OpenFOAM wallHeatFlux integral is kept
separately as native outward wall-normal sign, with `Q_wall_W = -native_integral`.

The same exact package also released `3` pressure-basis rows, `233280`
pressure-detail rows, and `116640` trusted-wall heat-flux detail rows. It did
not refresh the production sampler manifest, run harvest, execute same-QOI UQ,
admit coefficients, trigger S11/S12/S13/S15/S6, or absorb residuals into
internal `Nu`.

The source-side conservation/neighbor/UQ gate preserved the fallback label
`Q_source_side_net_static_bc_W` and consumed the exact-Qwall package read-only.
It found `3` source/property conservation rows, `0` conservation release-ready
rows, `4` neighbor-window QOI rows, `0` same-QOI UQ-ready rows, and a
`do_not_run` harvest decision.

The limited sampled-field evidence synthesis produced thesis-ready diagnostic
support only: `3` finite exchange rows, `15` diagnostic-ready gate rows,
`0` production-ready gate rows, and `15` blocked production gate rows.

## Trusted Packages

- Direct heat-flow and pressure basis:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/`
- Source-side fallback contract and same-QOI prerequisites:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_side_heatflow_equivalence_uq_prereq/`
- Source-side conservation, neighbor, and production gate:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/`
- Limited sampled-field extraction:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_limited_sampled_field_scheduler_extraction/`
- Diagnostic sampled-field synthesis:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/`
- Earlier average-field thermal reduction:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_average_field_thermal_reduction/`

## Unresolved Blockers

- Exact same-label neighboring windows are still missing for `Q_wall_W`,
  `mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
  wall/core/bulk thermal contrast.
- Same-QOI UQ remains unavailable: the current evidence does not yet provide a
  target-window plus neighboring-window uncertainty package for the production
  exchange QOIs.
- Mesh/GCI support is still not paired with the exact exchange and heat-flow
  QOIs.
- Source-side fallback support remains incomplete because source/property
  provenance, `cp_J_kg_K`, source validity envelope, pressure/enthalpy residual
  support, and release status are still missing.
- Production harvest, coefficient admission, and S11/S12/S13/S15/S6 triggers
  remain disallowed.

## Tomorrow Task Order

1. Claim `TODO-S13-UPCOMER-EXCHANGE-QWALL-SAME-QOI-NEIGHBOR-UQ-EXECUTION-2026-07-22`
   or the same slug dated tomorrow. Scope it to existing evidence first. Output
   `neighbor_window_inventory.csv`, `same_qoi_uq_matrix.csv`,
   `production_readiness_gate.csv`, `source_manifest.csv`, and `README.md`.
2. In that row, inventory exact target-minus/target/target-plus support for
   `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
   `tau_recirc_proxy_s`, and wall/core/bulk temperature contrast. If exact
   neighboring windows are missing, publish a clean fail-closed negative gate.
3. Claim `TODO-S13-UPCOMER-EXCHANGE-QWALL-MESH-GCI-UQ-GATE-2026-07-22`
   only after the neighboring-window matrix is clear. Pair direct `Q_wall_W`
   and exchange QOIs with mesh/GCI evidence if it exists; otherwise publish the
   smallest remaining mesh/GCI blocker.
4. Claim `TODO-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-GATE-AFTER-QWALL-UQ-2026-07-22`
   only if same-QOI neighboring-window UQ and mesh/GCI support are both ready.
   This row decides whether `TODO-THESIS-STUDY-S13-UPCOMER-EXCHANGE-PRODUCTION-HARVEST-UQ-2026-07-21`
   can safely activate.
5. If those gates stay closed, use the limited sampled-field synthesis and
   direct Qwall values as a thesis diagnostic/negative-result package rather
   than an admitted production harvest.

## Output Contract For The Next Agent

The next execution row should produce a package with:

- `neighbor_window_inventory.csv` with one row per case, window, and exact QOI.
- `same_qoi_uq_matrix.csv` showing target, neighboring-window support, and
  readiness for each production exchange QOI.
- `production_readiness_gate.csv` with a single fail-closed decision and reasons.
- `source_manifest.csv` with exact repo-relative paths and read-only provenance.
- `README.md`, `.agent/status/...`, `.agent/journal/...`, and `imports/...`.

If the row blocks, it should explicitly report `0` production-ready rows,
`production_harvest_allowed=false`, `admission_allowed=false`, and no
S11/S12/S13/S15/S6 trigger.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs.
- Do not relabel `Q_source_side_net_static_bc_W` as `Q_wall_W`.
- Do not absorb missing pressure or heat residuals into internal `Nu`.
- Do not run production harvest, sampler refresh, UQ, admission, model
  selection, or validation scoring without a new board row that explicitly
  grants that action.
- Do not use the diagnostic average-field approach as production evidence.
- Do not edit thesis current files, Fluid/external repositories, registry, or
  admission state from this handoff row.
