---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_suggested_model_form_diagnostic_tests/tested_model_form_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_unlock_gate_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_same_qoi_harvest/same_qoi_neighbor_triplet_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
tags: [model-form, d3, wall-shape, axial-mixing, same-qoi, thesis]
related:
  - .agent/status/2026-07-22_TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/mf-d3-wall-shape-axial-mixing-gate.md
task: TODO-MF-D3-WALL-SHAPE-AXIAL-MIXING-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# D3 Wall-Shape / Axial-Mixing Gate

This package tests whether the D3 wall-index diagnostic improvement can be
explained by source-bounded wall/core exchange, axial mixing, or sensor
projection evidence.

## Decision

D3 is supported as a diagnostic wall-shape signal only. S13 now has same-QOI
target/minus/plus triplets ready for four QOI labels, but same-QOI UQ,
production use, source/property release, and admission remain unexecuted.

## Outputs

- `wall_index_residual_shape_decomposition.csv`
- `wall_shape_case_summary.csv`
- `s12_s13_evidence_crosswalk.csv`
- `same_qoi_uq_requirement_table.csv`
- `candidate_gate.csv`
- `publication_claim_boundary.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
