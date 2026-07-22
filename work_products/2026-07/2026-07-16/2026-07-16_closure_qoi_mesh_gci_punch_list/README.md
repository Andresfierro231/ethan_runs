---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_closure_mesh_gate_refresh/refreshed_qoi_mesh_gate_status.csv
  - work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/closure_qoi_admission_decisions.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pressure_ladder_unlock_sbatch/station_pressure_ladder.csv
tags: [mesh-gci, closure-qoi, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/mesh-gci-and-uncertainty.md
task: AGENT-450
date: 2026-07-16
role: Coordinator/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Closure-QOI Mesh-GCI Punch List

Generated: `2026-07-16T20:38:27.878046+00:00`

## Result

This package narrows `closure-qoi-mesh-gci`; it does not resolve it.

- QOI rows reviewed: `25`
- Admitted-only candidates now: `0`
- Extraction/reconciliation queue rows: `19`
- Admission-only queue rows: `6`
- Bucket counts: `{'downcomer_policy_blocked': 1, 'gci_failed_no_resolution_without_reextract_or_remesh': 14, 'missing_triplet_extraction_or_reconciliation_required': 5, 'thermal_admission_review_required': 5}`

## Pressure Diagnostic Context

July 15 pressure diagnostics are available, but remain coarse diagnostic
evidence. Station pressure rows with reverse-area proxy below `0.01`:
`0`;
rows at or above `0.20`:
`330`.

## Outputs

- `closure_qoi_blocker_punch_list.csv`
- `admitted_only_candidate_matrix.csv`
- `extraction_queue_candidates.csv`
- `admission_only_candidates.csv`
- `closure_qoi_narrowing_decision.md`
- `source_manifest.csv`
- `summary.json`
