---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/candidate_terminal_preflight.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/pressure_f6_gate_waterfall.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_comparison_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_b_mesh_gci_evidence_matrix/summary.json
tags: [thesis-dossier, s10, pressure, f6, low-recirculation-anchor, same-qoi-uq, negative-result]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s10_pressure_f6_gate_waterfall/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_low_recirc_anchor_harvest/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/README.md
task: TODO-THESIS-STUDY-S10-PRESSURE-F6-LOW-RECIRC-ANCHOR-UQ-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis S10 Pressure/F6 Low-Recirculation Anchor UQ

## Decision

S10 closes as `negative_result_s11_still_blocked`.

The study reviews `11` candidate rows across
low-recirculation pressure anchors, current pressure-corner diagnostics, and F6
endpoint pairs. It releases `0` S11-ready
pressure/F6 candidates.

## Claim Boundary

Current evidence strengthens pressure/F6 non-admission. It does not admit a
component K, cluster K, F6 fit, clipped K, hidden multiplier, or mixed-basis
pressure correction.

## Files

| File | Use |
| --- | --- |
| `s10_candidate_admission_matrix.csv` | Candidate-by-candidate gate decision. |
| `s10_gate_matrix.csv` | Study-level admission gates and S11 effects. |
| `s11_unblock_decision.csv` | Machine-readable S11 decision from S10. |
| `source_manifest.csv` | Source paths and mutation flags. |
| `summary.json` | Machine-readable summary. |

## Guardrails

No native output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler launch, Fluid edit, external edit, fitting,
model selection, component-K/F6 admission, clipped K, hidden multiplier,
generated-index refresh, S11 trigger, or mixed-basis promotion was performed.
