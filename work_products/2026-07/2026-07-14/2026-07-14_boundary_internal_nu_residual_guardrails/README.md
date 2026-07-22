---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
tags: [boundary-modeling, internal-nu, guardrails, thermal-residuals]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/thermal_residual_ownership_guardrails.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_internal_nu_residual_guardrails/boundary_fields_needed_for_upcomer_extraction.csv
task: AGENT-336
date: 2026-07-14
role: BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Boundary/Internal-Nu Residual Guardrails

## Purpose

Internal-Nu confirmed that current thermal closure cannot absorb boundary
residuals: there are `0` fit-admissible internal-Nu rows, and current admitted
upcomer evidence is recirculating. This package converts that decision into
boundary-model guardrails.

## Decision

Heat residuals are owned by their physical lane before any Nu fit is reopened:

- heater/source residuals belong to the heater realized-fraction/source
  contract;
- active cooler residuals belong to cooler/HX UA/effectiveness modeling;
- passive losses belong to wall-layer/external convection dictionaries;
- radiation is metadata embedded in CFD `rcExternalTemperature` `wallHeatFlux`
  during replay and must not be counted again;
- storage belongs to a wall/storage or transient residual ledger;
- branch mixing/recirculation belongs to section-effective admission/naming,
  not single-stream Nu.

## Files

- `thermal_residual_ownership_guardrails.csv`: residual ownership and explicit
  "do not fit this residual into internal Nu" guardrails.
- `boundary_fields_needed_for_upcomer_extraction.csv`: matched boundary and
  Nu/upcomer extraction fields, including wall T, bulk T, wallHeatFlux,
  Tsur/Ta/emissivity, external h/UA, vector-plane metrics, and window/source
  path coordination.
- `summary.json`: compact package status.

## Extraction Coordination

Boundary metrics and Nu metrics must use the same case path, property lane,
segment/patch map, time window, and matched upcomer inlet/mid/outlet planes.
If a field is used to score a boundary residual, the same residual may not be
reintroduced as an internal-Nu fit target under another temperature definition.

## Status

This is a guardrail and extraction-contract package. It does not mutate native
CFD outputs, registry/admission state, scheduler state, generated indexes, or
external Fluid files.

Summary: `7` residual guardrail rows and
`8` extraction-field rows.
