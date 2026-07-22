---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
  - work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/setup_candidate_summary.csv
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/case_mode_error_matrix.csv
tags: [forward-model, m3ts, test-section, coupled-score, runtime-legal]
related:
  - .agent/blockers.yml
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-470
date: 2026-07-16
role: Forward-pred/BC-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# M3+TS Frozen Candidate Coupled Score

Generated: `2026-07-16T22:50:03+00:00`

## Decision

`predictive-wall-test-section-submodels`: `keep_open`.

This package runs the frozen role-row M3+TS scenario score path and then applies
admission gates. Runtime inputs remain setup-only; realized CFD wallHeatFlux,
CFD mdot, imposed CFD cooler duty, and validation/holdout temperatures are not
runtime inputs.

## Results

- Coupled score rows: `9`.
- Coupled run status: `9` rows `timeout_after_45s`.
- Admission candidates reviewed: `3`.
- Admitted candidates: `0`.
- Interpretation: the frozen candidates remain runtime-legal, but no coupled
  Fluid score completed, so the wall/test-section blocker stays open.

## Outputs

- `m3ts_coupled_scorecard.csv`
- `m3ts_admission_review.csv`
- `m2_m3_delta_summary.csv`
- `runtime_input_audit.csv`
- `blocker_decision.csv`
- `source_manifest.csv`
- `summary.json`
