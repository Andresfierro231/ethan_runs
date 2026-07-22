---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/leg_specific_internal_nu_candidate_rows.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/mesh_gci_gate_for_admitted_candidates.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/leg_specific_nu_model_form_matrix.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/blocker_unblock_decision.csv
tags: [internal-nu, closure-qoi, mesh-gci, branch-local-admission, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-459
date: 2026-07-16
role: Coordinator/cfd-pp/Mesh-GCI/Internal-Nu/Implementer/Tester/Writer
type: work_product
status: complete
---
# Branch-Local Internal-Nu Unblock

Generated: `2026-07-16T21:54:12+00:00`

## Decision

`closure-qoi-mesh-gci`: `not_resolved`.

This package implements the branch-local unblock plan after AGENT-455. It
restricts final-use GCI review to non-upcomer fit lanes, keeps the test section
inside the upcomer hybrid/onset lane, and evaluates whether any current row can
fit a leg-specific Internal-Nu correlation.

## Results

- Branches reviewed: `5`.
- Final-use non-upcomer GCI rows reviewed: `13`.
- Publication-ready final-use GCI rows: `0`.
- Internal-Nu candidate rows reviewed: `32`.
- Fit-admissible Internal-Nu rows: `0`.
- Targeted unblock queue rows: `5`.

## Interpretation

The current blocker cannot be closed today. The taxonomy and branch lanes are
decision-complete, but the evidence still lacks both an admitted Internal-Nu fit
row and a publication-ready final-use Closure-QOI/GCI row. The next work is
branch-local admission, not global Nu tuning.

## Outputs

- `branch_local_thermal_admission.csv`
- `final_use_closure_qoi_gci.csv`
- `internal_nu_fit_admissible_rows.csv`
- `targeted_extraction_admission_queue.csv`
- `blocker_resolution_decision.csv`
- `source_manifest.csv`
- `summary.json`
