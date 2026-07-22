---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/next_raw_postprocessing_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/two_tap_component_repair_output.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/tap_centerline_length_table.csv
  - operational_notes/07-26/17/2026-07-17_MONDAY_HYDRAULICS_CONTEXT_AND_NEXT_STEPS.md
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS.md
  - .agent/journal/2026-07-18/two-tap-component-raw-endpoints.md
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/README.md
task: TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Raw Endpoint Plan

Generated: `2026-07-18T18:03:59+00:00`

## Decision

The AGENT-530 raw postprocessing queue is converted into an exact sampling
contract for the three `corner_lower_right` Salt2/Salt3/Salt4 rows. This is a
plan only: no OpenFOAM sampling, scheduler action, registry mutation, Fluid
edit, F6 fit, or component-K admission was performed.

## Outputs

- `target_feature_taps.csv`
- `pressure_surface_sampling_contract.csv`
- `basis_field_contract.csv`
- `recirculation_metric_contract.csv`
- `same_qoi_uncertainty_contract.csv`
- `launch_readiness_gate.csv`
- `raw_endpoint_plan_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Target rows: `3`.
- Endpoint surface rows: `6`.
- Basis field rows: `8`.
- Recirculation contract rows: `3`.
- Same-QOI uncertainty rows: `3`.
- Ordinary admissions: `0`.

## Required Endpoint Contract

For each target, sample `corner_lower_right` from upstream
`lower_leg__s04` / `ncc_pipeleg_lower_09_fitting_end` to downstream
`right_leg__s00` / `ncc_pipeleg_right_01_lower_start` at the same existing
time windows: Salt2 `7915`, Salt3 `7618`, Salt4 `10000`.

Each endpoint must emit `p`, `p_rgh`, `U`, `T_or_rho`, flux/area/normal data,
bulk velocity, local density, RAF, RMF, and SVF. The downstream extractor can
use the result only if endpoint labels are finite and the pressure, kinetic,
straight-reference, recirculation, and same-QOI UQ gates pass.

## Guardrails

Do not infer missing endpoint pressure fields from proxy losses. Do not clip the
negative current `K_local` values. Do not use this component endpoint plan to
fit F6 or admit component K; a future staged-copy postprocessing row and a new
extractor/admission review are required.
