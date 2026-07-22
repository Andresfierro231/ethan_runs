---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard/branch_specific_fit_mask.csv
  - work_products/2026-07/2026-07-15/2026-07-15_branch_specific_ordinary_pipe_scorecard/ordinary_pipe_candidate_rows.csv
  - work_products/2026-07/2026-07-16/2026-07-16_thermal_parity_resolution_gate/thermal_row_admission_gate.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_punch_list/closure_qoi_blocker_punch_list.csv
tags: [closure-qoi, mesh-gci, internal-nu, leg-specific-models, blocker-narrowing]
related:
  - .agent/blockers.yml
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - operational_notes/maps/geometry-and-mesh-truth.md
task: AGENT-455
date: 2026-07-16
role: Coordinator/cfd-pp/Internal-Nu/Implementer/Tester/Writer
type: work_product
status: complete
---
# Closure-QOI Mesh-GCI Resolution and Leg-Specific Internal-Nu Admission

Generated: `2026-07-16T21:20:34+00:00`

## Decision

`closure-qoi-mesh-gci`: `not_resolved`.

The taxonomy blocker is removed: `test_section_span` is part of
`upcomer_left_vertical`, so test-section rows cannot be treated as a separate
non-upcomer ordinary-pipe/Internal-Nu fit lane. The current scientific blocker
is not just upcomer recirculation; it is the absence of rows that pass all
leg-specific admission gates.

## Gate Results

- Leg-specific Internal-Nu candidates reviewed: `50`.
- Fit-admissible Internal-Nu rows now: `0`.
- Upcomer/test-section rows kept out of single-stream fitting: `27`.
- Closure-QOI/GCI rows reviewed: `25`.
- Current publication-ready Closure-QOI/GCI rows: `0`.
- Mesh/admission rows still unresolved: `13`.

## Methodology and Assumptions

The LitRev theory is applied as a gate sequence, not as a tuning shortcut:
separate source, boundary, wall/layer, radiation, storage, and branch-mixing
residuals before fitting internal convection. Each physical leg receives its own
model lane. A row can fit a leg-specific Nu correlation only when its geometry,
recirculation, sign/heat-balance, residual-owner, and mesh/GCI gates all pass.

## Outputs

- `geometry_taxonomy_correction.csv`
- `leg_specific_nu_model_form_matrix.csv`
- `leg_specific_internal_nu_candidate_rows.csv`
- `upcomer_exclusion_and_hybrid_lane.csv`
- `sign_heat_balance_gate.csv`
- `mesh_gci_gate_for_admitted_candidates.csv`
- `blocker_unblock_decision.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD solver outputs, registry/admission state, scheduler state, or
external `../cfd-modeling-tools/**` files were mutated.
