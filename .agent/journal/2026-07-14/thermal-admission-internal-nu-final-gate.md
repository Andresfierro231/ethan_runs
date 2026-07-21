---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
tags: [journal, thermal-closure, internal-nu, admission-gate]
related:
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-319
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Thermal Admission / Internal Nu Final Gate

Observed: AGENT-309's refreshed admission table has `16` rows: `0`
fit-eligible, `11` validation-only, `5` blocked. Lower-leg has five
validation-only rows and one blocked Nu row; upcomer has six validation-only
rows; downcomer has four blocked rows.

Decision: forward-v1 cannot fit internal Nu from these rows. Nu/HTC/UA remain
diagnostics and cannot absorb heater, cooler, passive loss, wall storage,
junction, recirculation, or radiation residuals.

Radiation policy remains unchanged: CFD `rcExternalTemperature` includes
radiation in total `wallHeatFlux`; no separate exported `qr` term exists.
