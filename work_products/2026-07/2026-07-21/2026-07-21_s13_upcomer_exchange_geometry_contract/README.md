---
task: TODO-S13-UPCOMER-EXCHANGE-GEOMETRY-CONTRACT-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed
tags: [upcomer, exchange-cell, geometry-contract, fail-closed, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq
---
# S13 Upcomer Exchange Geometry Contract

This package resolves the current geometry gate conservatively. It publishes
the required interface and wall/core geometry contracts, but releases no
exchange-interface, wall/core, `Q_wall_W`, or harvest lane because the trusted
recirculation volume/interface source is still missing.

## Decision

- cases: `salt_2`, `salt_3`, `salt_4`
- released exchange-interface rows: `0`
- released wall/core rows: `0`
- released `Q_wall_W` rows: `0`
- harvest-ready rows: `0`
- scheduler action: `false`
- native output mutation: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `geometry_source_ledger.csv`
- `interface_geometry_contract.csv`
- `wall_core_band_contract.csv`
- `downstream_surface_vtk_inputs.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Do not substitute loop `mdot_*` faceZones or an upcomer outlet proxy for a
main/recirculation exchange interface. Do not run surface VTK extraction or
exchange-cell harvest until a later row supplies a trusted recirculation cell
volume, interface surface, normal-vector basis, and wall/core band.
