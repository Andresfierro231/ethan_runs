---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/residual_quantification.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/admission_gate_matrix.csv
tags: [thesis-dossier, s12, thermal-shape, residual-ownership, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s8_wall_ts_residual_atlas/tw5_tw6_residual_atlas.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/exchange_qoi_contract.csv
task: TODO-THESIS-STUDY-S12-THERMAL-SHAPE-OWNERSHIP-CANDIDATE-2026-07-21
date: 2026-07-21
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer
type: work_product
status: complete
---
# S12 Thermal-Shape Ownership Candidate

## Decision

S12 identifies one best physical owner for the dominant TW5/TW6 residual:
`S12-HIAX1`, a heated-incline/upcomer exchange-shape candidate. It is not
released to S11 because no finite candidate score, exchange-state QOI set,
same-QOI UQ, or source/property release exists.

## Counts

- residual rows: `2`
- candidate rows: `3`
- admitted rows: `0`
- S11-ready rows: `0`
- final score values: `0`

## Interpretation

The residual is used as a discovery signal, not as a fit. Prior passive
wall/test-section selectors worsen TW5/TW6 relative to M3, while the residual
signature points to energy-conserving heated-incline/upcomer exchange physics.
That candidate remains a future candidate until S13-style exchange QOIs and
same-QOI UQ exist.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid/external source, blocker register, or generated documentation index was
mutated. No solver, sampler, fit, model selection, S11 trigger, final score, or
residual absorption into internal `Nu` was performed.
