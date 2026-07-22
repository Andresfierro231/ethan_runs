---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/branch_local_thermal_admission.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/internal_nu_fit_admissible_rows.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/final_use_closure_qoi_gci.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/targeted_extraction_admission_queue.csv
  - work_products/2026-07/2026-07-16/2026-07-16_downcomer_internal_nu_unlock_and_blocker_roadmap/future_studies_and_blockers.csv
tags: [internal-nu, heater, closure-qoi, mesh-gci, source-sign, blocker-roadmap]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-468
date: 2026-07-16
role: Coordinator/Thermal-modeling/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Lower-Leg Source/Sign/GCI Admission

Generated: `2026-07-16T22:28:03+00:00`

## Decision

`closure-qoi-mesh-gci`: `not_resolved_heater_narrowed`.

The heater lower leg is reviewed at source/sign/heat-balance and same-QOI
mesh/GCI level, but no row is admitted. Current evidence still has zero
source/sign heat-balance pass rows, zero branch-local recirculation pass rows,
and zero publication-ready heater same-QOI GCI rows.

## Results

- Heater branch candidate rows reviewed: `7`.
- Heater Nu-equivalent candidate rows reviewed: `2`.
- Heater fit-admissible rows: `0`.
- Heater final-use GCI rows reviewed: `6`.
- Heater publication-ready same-QOI GCI rows: `0`.
- Next extraction/admission rows: `4`.

## Method

This package replays existing AGENT-459 gate vectors and final-use GCI rows for
`heater_lower_leg`. It admits a heater row only when source ownership,
residual-owner, sign/heat-balance, recirculation, and same-QOI publication-GCI
gates all pass. No native CFD output, registry state, scheduler state, or
external Fluid file is changed.

## Outputs

- `heater_source_sign_heat_balance_gate.csv`
- `heater_same_qoi_mesh_gci_gate.csv`
- `heater_internal_nu_candidate_admission.csv`
- `gci_results_admitted_only.csv`
- `closure_qoi_blocker_delta.csv`
- `next_extraction_queue.csv`
- `blocker_decision.csv`
- `closure_qoi_resolution_decision.md`
- `source_manifest.csv`
- `summary.json`
