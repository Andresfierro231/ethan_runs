---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_cfd_anchor_matrix/upcomer_onset_anchor_matrix.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/evidence_gap_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/anchor_inventory.csv
  - work_products/2026-07/2026-07-17/2026-07-17_upcomer_onset_data_sparsity_progress/same_window_field_gap_table.csv
tags: [upcomer, onset, cfd-anchor, postprocessing-request, provenance]
related:
  - .agent/status/2026-07-17_TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING.md
  - .agent/journal/2026-07-17/upcomer-onset-anchor-request-hardening.md
task: TODO-UPCOMER-ONSET-ANCHOR-REQUEST-HARDENING
date: 2026-07-17
role: Coordinator/Implementer/Tester/Writer
type: work_product
status: complete
---
# Upcomer Onset CFD Anchor Request Hardening

## Decision

This package converts the completed upcomer-onset design into an exact CFD/postprocessing request. It does not launch CFD, mutate native solver outputs, or change admission state.

## Required Outputs

- `target_re_thermal_drive_matrix.csv`: target Re and thermal-drive matrix for near-onset, non-recirculating, transition, and recirculating-side anchors.
- `same_window_field_request.csv`: wall/bulk, pressure, heat, and property fields that must be extracted from the same retained window.
- `pm5_pm10_extraction_request.csv`: PM5/PM10 reverse-flow, pressure, heat, and nondimensional extraction contract.
- `mesh_time_uncertainty_requirements.csv`: mesh/time gates required before rows can become main evidence or training data.
- `launch_gate_checklist.csv`: pre-launch gates for a future scheduler/staging task; this package itself is non-launching.
- `misuse_guardrails.csv`: forbidden interpretations that would contaminate upcomer-onset or 1D closure work.
- `blocker_attack_map.csv`: how the request attacks `upcomer-onset-data-sparsity` without claiming it is resolved.

## Counts

- Target matrix rows: `12`.
- Same-window field rows: `10`.
- PM5/PM10 request rows: `35`.
- Mesh/time uncertainty rows: `5`.
- Scheduler action: `False`.

## 1D Mapping

PM5 and PM10 define the upcomer pipe-element endpoints for the 1D model. Junction, corner, and stub heat/pressure terms must remain separate local branches until admitted evidence proves they can be collapsed without biasing onset.
