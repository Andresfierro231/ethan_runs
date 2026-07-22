---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s12_thermal_shape_ownership_candidate/candidate_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/geometry_source_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight/sampler_input_gap_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/low_recirculation_anchor_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table/same_qoi_uq_admission_table.csv
tags: [same-qoi-uq, s12, s13, s14, upcomer, pressure, fail-closed]
related:
  - .agent/status/2026-07-21_TODO-CANDIDATE-UQ-S13-GEOMETRY-RECOVERY-2026-07-21.md
  - .agent/journal/2026-07-21/candidate-uq-s13-geometry-recovery.md
  - imports/2026-07-21_candidate_uq_s13_geometry_recovery.json
task: TODO-CANDIDATE-UQ-S13-GEOMETRY-RECOVERY-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed
---
# Candidate UQ and S13 Geometry Recovery

This package converts the current S12/S13/S14 evidence into a candidate-scoped
same-QOI UQ repair ledger and an S13 geometry-source recovery decision. It does
not admit UQ, release a geometry source, launch a sampler, fit F6, or trigger
S11.

## Decision

- candidate rows reviewed: `6`
- QOI prerequisite rows: `16`
- same-QOI UQ admitted rows: `0`
- S13 geometry source rows reviewed: `33`
- S13 geometry release rows: `0`
- S13 sampler-ready rows: `0`
- S11 unblocked: `false`

S12-HIAX1 remains the best thermal-shape owner, but it cannot be scored until
S13 exchange-state QOIs exist. S13 remains blocked by geometry/source terms,
not by whole-mesh cell fields: Salt2/Salt3/Salt4 `cell_vtk` and volume CSVs are
ready, but exchange interface, recirculation mask, wall/core band, normals,
`Q_wall_W`, source/sink release, thermal contrast, and same-QOI UQ are not
released. S14 pressure/F6 remains a future-anchor lane only; right-leg,
test-section-span, and low-recirculation anchors still lack terminal/source and
same-QOI UQ evidence needed for F3-vs-F6 review.

## Outputs

- `candidate_uq_repair_targets.csv`: leading S12/S13/S14 candidates and their
  current UQ repair status.
- `qoi_prerequisite_matrix.csv`: candidate-QOI gate matrix for finite QOIs,
  geometry/source status, same-window evidence, neighbor windows, mesh/GCI,
  source/property, split, and admission.
- `uq_admission_decision.csv`: fail-closed UQ decision for every leading
  candidate.
- `geometry_source_recovery_decision.csv`: all 33 S13 geometry source rows
  classified as `do_not_use` or `needs_manual_geometry_definition`.
- `s13_sampler_manifest_requirements.csv`: Salt2/Salt3/Salt4 sampler
  requirements showing ready cell/volume lanes and blocked geometry/source/UQ
  lanes.
- `s11_decision.csv`: current S11 gate remains blocked.
- `next_evidence_sequence.csv`: recommended next work order.
- `build_candidate_uq_s13_geometry_recovery.py` and
  `check_candidate_uq_s13_geometry_recovery.py`: reproducible builder and
  acceptance checker.

## Next Evidence Sequence

1. Define a trusted S13 exchange interface and recirculation mask. Existing
   loop `mdot_*` faceZones and the upcomer outlet proxy remain `do_not_use`.
2. Define S13 wall/core band and `Q_wall_W` on top of that recirculation mask.
3. Rerun S13 sampler manifest preflight. It must produce `3/3` sampler-ready
   rows before production harvest.
4. Harvest S13 exchange QOIs and same-QOI UQ, then reassess whether S12-HIAX1
   can become an S11 candidate.
5. Refresh S14 terminal low-recirculation anchors only after watched source
   cases land; preserve the no-fit/no-F6/no-component-K gate until endpoint,
   ordinary-flow, and same-QOI UQ evidence pass.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
sampler/harvest, Fluid source, external repository, blocker register, generated
documentation index, thesis chapter, fitting/model selection, F6/component-K
admission, S11/S15 trigger, or internal-Nu residual absorption was changed.
