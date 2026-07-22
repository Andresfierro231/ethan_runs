---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/branch_local_thermal_admission.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/internal_nu_fit_admissible_rows.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/final_use_closure_qoi_gci.csv
  - work_products/2026-07/2026-07-16/2026-07-16_branch_local_internal_nu_unblock/targeted_extraction_admission_queue.csv
  - operational_notes/maps/literature-synthesis-and-gates.md
tags: [internal-nu, downcomer, closure-qoi, mesh-gci, litrev-gates, blocker-roadmap]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-466
date: 2026-07-16
role: Coordinator/Thermal-modeling/Internal-Nu/Mesh-GCI/Implementer/Tester/Writer
type: work_product
status: complete
---
# Downcomer Internal-Nu Unlock And Blocker Roadmap

Generated: `2026-07-16T22:18:14+00:00`

## Decision

`closure-qoi-mesh-gci`: `not_resolved_downcomer_narrowed`.

The downcomer is still the best first non-upcomer candidate for ordinary
Internal-Nu admission, but current evidence does not admit a fit. The downcomer
row is blocked by unresolved sign/heat-balance, missing low-recirculation
admission evidence, and missing publication-ready same-QOI mesh/GCI.

## Results

- Downcomer Internal-Nu candidate rows reviewed: `1`.
- Downcomer fit-admissible rows: `0`.
- Future studies documented: `12`.
- Open blockers covered by future studies: `4` / `4`.

## Method

This package applies the LitRev branchwise closure discipline: no global
Nu/f/UA tuning, no source/boundary/storage residual absorption into Internal Nu,
and no single-stream coefficient export until CFD-validity and mesh/GCI gates
pass. It uses existing AGENT-455/459/461/464 evidence only and mutates no native
CFD solver output.

## Outputs

- `downcomer_admission_gate.csv`
- `downcomer_policy_decision.csv`
- `litrev_gate_application.csv`
- `future_studies_and_blockers.csv`
- `blocker_resolution_decision.csv`
- `source_manifest.csv`
- `summary.json`
