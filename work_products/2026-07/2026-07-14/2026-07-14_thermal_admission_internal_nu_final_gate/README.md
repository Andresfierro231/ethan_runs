---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/thermal_admission_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/sign_convention_table.csv
tags: [thermal-closure, internal-nu, admission-gate, forward-model]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-319
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Thermal Admission / Internal Nu Final Gate

This package freezes the thermal fit policy for final forward-v1 scoring.
It consumes the refreshed AGENT-309 admission rows and does not mutate native CFD outputs.

## Decision

- Fit-admissible rows: `0`.
- Validation-only rows: `11`.
- Blocked rows: `5`.
- Internal Nu fitting for forward-v1: `no`.
- Forward-v1 may use only baseline/literature/default internal Nu behavior unless a later gate admits a specific row.

## Segment Decisions

- `downcomer`: `blocked`, fit rows `0`, validation-only `0`, blocked `4`
- `lower_leg`: `mixed_validation_only_and_blocked`, fit rows `0`, validation-only `5`, blocked `1`
- `upcomer`: `validation_only`, fit rows `0`, validation-only `6`, blocked `0`

## Guardrails

- Sign: positive wallHeatFlux/segment duty heats fluid; positive enthalpy_change increases fluid bulk enthalpy; HTC/UA/Nu are positive diagnostics, not heat-source directions.
- Radiation: CFD rcExternalTemperature wallHeatFlux includes radiation where that BC is used; no separate exported qr term exists; do not add a separate radiation residual to internal Nu.
- Nu: internal Nu may not absorb heater, cooler, passive loss, wall storage, junction, recirculation, or radiation residuals.

## Files

- `thermal_admission_internal_nu_final_gate.csv`
- `segment_thermal_fit_summary.csv`
- `sign_radiation_nu_policy.csv`
- `source_manifest.csv`
- `summary.json`
