---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/f6_status_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/upcomer_onset_classification.csv
  - work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/upcomer_exclusion_and_hybrid_lane.csv
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/next_execution_contract.csv
tags: [recirculation, upcomer, predictive-1d, admission, hybrid-model]
related:
  - .agent/status/2026-07-16_AGENT-467.md
  - .agent/journal/2026-07-16/recirc-feature-admission-and-hybrid-contract.md
task: AGENT-467
date: 2026-07-16
role: Hydraulics/Upcomer-onset/Implementer/Tester/Writer
type: work_product
status: complete
---
# Recirculation Feature Admission And Hybrid Contract

Generated: `2026-07-16T22:25:44+00:00`

## Decision

Current evidence does not admit a predictive recirculation model. It does admit
the coefficient-naming rule: material recirculation invalidates ordinary
single-stream `Nu`, `f_D`, and component `K` fits for the current upcomer and
test-section rows.

## Outputs

- `recirculation_feature_admission_table.csv`
- `hybrid_1d_model_contract.csv`
- `next_extraction_queue.csv`
- `recirculation_decision_table.csv`
- `decision_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Feature/admission rows: `42`.
- Ordinary single-stream fit rows allowed today: `0`.
- Recirculating/effective-lane rows: `42`.
- Queue rows: `10`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, blocker files,
generated index files, OpenFOAM jobs, Fluid source, or external paths were
mutated.
