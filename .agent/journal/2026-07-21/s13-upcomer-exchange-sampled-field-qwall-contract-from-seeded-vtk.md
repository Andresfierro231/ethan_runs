---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk/downstream_gate.csv
tags: [journal, s13, upcomer-exchange, sampled-field-contract]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-CONTRACT-FROM-SEEDED-VTK-2026-07-21.md
  - imports/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk.json
task: TODO-S13-UPCOMER-EXCHANGE-SAMPLED-FIELD-QWALL-CONTRACT-FROM-SEEDED-VTK-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: journal
status: complete
---
# S13 Sampled-Field Qwall Contract From Seeded VTK

Observed: seeded geometry VTKs and whole-mesh `U`, `T`, and `rho` fields are
available for all three Salt cases.

Observed: `Q_wall_W`, wallHeatFlux, pressure basis, cp/property basis, sampled
surface arrays, and same-QOI UQ are still absent.

Observed: the contract package verified `21/21` source-file rows and `6/6`
face-to-cell mapping rows. It opened `12` limited sampled-field lanes and `3`
scheduler-authorized limited sampled-field rows for interface `U/T/rho` and
wall/core `T` support.

Inferred: the next useful row is a scheduler-authorized limited sampled-field
extraction. It can advance S13 evidence without claiming `Q_wall_W`, production
sampler readiness, production harvest, or coefficient admission.

Caveat: no extraction, sampler refresh, harvest, UQ, fitting, coefficient
admission, or downstream trigger was run.
