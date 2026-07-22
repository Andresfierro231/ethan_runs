---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_from_seeded_cv/surface_vtk_validation.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/field_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/qwall_contract.csv
tags: [s13, upcomer-exchange, sampled-field-contract, qwall-contract]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-CONTRACT-FROM-SEEDED-VTK-2026-07-21.md
task: TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-CONTRACT-FROM-SEEDED-VTK-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_contract_limited_extraction_open
---
# S13 Sampled-Field and Q_wall Contract from Seeded VTK

This package defines the next exact extraction contract after the seeded
geometry-only VTK release. It does not run a sampler, harvest QOIs, integrate
`Q_wall_W`, fit coefficients, or trigger S11/S12/S15/S6.

Decision: `open_limited_scheduler_sampled_field_extraction`.

- cases: `3`
- source files ready: `21/21`
- geometry mappings ready: `6/6`
- limited sampled-field lanes open: `12`
- scheduler-authorized sampled-field rows open: `3`
- `Q_wall_W` released rows: `0`
- sampler refresh allowed: `false`
- production harvest allowed: `false`
- S11/S12/S15/S6 trigger: `false`

## Contract

The next executable row may sample interface `U/T/rho` and wall/core `T` from
the released seeded surfaces. It must report missing `wallHeatFlux`, `p/p_rgh`,
`mu/nu`, and `cp_J_kg_K` as blockers rather than silently substituting other
quantities.

`sampled_field_scheduler_decision.csv` is the authoritative next-row decision:
the limited field-sampling row is open for all three cases, while `Q_wall_W`,
residual closure, sampler refresh, production harvest, UQ, and admission remain
closed. `s13_unlock_impact.csv` and `s12_unlock_impact.csv` record the per-case
unlock status for Salt2/Salt3/Salt4.

## Guardrails

`q_net_W` is static source/sink context, not `Q_wall_W`. The geometry-only VTKs
are not sampler-ready outputs. No production harvest, same-QOI UQ, coefficient
admission, source/property release, freeze, or score trigger is released here.
