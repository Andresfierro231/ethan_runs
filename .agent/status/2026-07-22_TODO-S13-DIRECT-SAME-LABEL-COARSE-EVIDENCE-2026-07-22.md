---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/case_qoi_direct_coarse_admission_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/direct_coarse_extraction_action_contract.csv
tags: [status, s13, recirculation, coarse-equivalence, mesh-gci, fail-closed]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/README.md
  - .agent/journal/2026-07-22/s13-direct-same-label-coarse-evidence.md
  - imports/2026-07-22_s13_direct_same_label_coarse_evidence.json
task: TODO-S13-DIRECT-SAME-LABEL-COARSE-EVIDENCE-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-DIRECT-SAME-LABEL-COARSE-EVIDENCE-2026-07-22

## Objective

Attempt direct same-label coarse evidence admission from existing
topology-derived S13 artifacts: coarse CV, exchange interface, wall/core band,
face areas/normals, field/property basis, and same-window role matching the
medium/fine exact-label rows.

## Outcome

Decision:
`s13_direct_coarse_geometry_ready_sampled_same_window_admission_blocked`.

Existing evidence is strong enough to preserve the seeded coarse geometry as
extraction input evidence:

- Case rows: `3`.
- Evidence lane rows: `24`.
- Topology/geometry-ready case/QOI rows: `12`.
- Current-coarse same-QOI triplet-ready rows: `12`.

Direct admission is still blocked:

- Direct same-label coarse admitted rows: `0`.
- Field/property basis-ready rows: `0`.
- Same-window medium/fine role-ready rows: `0`.
- Endpoint residual-basis-ready rows: `0`.
- Formal GCI allowed rows: `0`.
- Same-QOI UQ rerun allowed rows: `0`.

## Changes Made

- Added builder:
  `tools/analyze/build_s13_direct_same_label_coarse_evidence.py`.
- Added tests:
  `tools/analyze/test_s13_direct_same_label_coarse_evidence.py`.
- Published work product:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_direct_same_label_coarse_evidence/`.
- Published lane evidence matrix, per-case/QOI admission matrix, direct coarse
  extraction action contract, source manifest, guardrails, summary, and README.

## Validation

- `python3.11 tools/analyze/build_s13_direct_same_label_coarse_evidence.py`: passed.
- `python3.11 -m py_compile tools/analyze/build_s13_direct_same_label_coarse_evidence.py tools/analyze/test_s13_direct_same_label_coarse_evidence.py`: passed.
- `python3.11 -m unittest tools.analyze.test_s13_direct_same_label_coarse_evidence`: `5` tests passed.

## Remaining Blockers

- Geometry-only coarse VTKs do not contain sampled U/T/rho/wallHeatFlux field
  evidence and must not be treated as sampled QOI evidence.
- `Q_wall_W` and source/property release remain false for direct coarse
  admission.
- Coarse target windows (`7914-7916`, `7617-7619`, `9999-10001`) are not
  admitted as same-window equivalents to the medium/fine terminal exact-label
  windows.
- Endpoint residual masks remain candidate face IDs only; released area
  vectors, owner cells, endpoint normals, and positive throughflow convention
  are missing.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, source/property or Qwall release, production harvest, formal GCI
run/admission, same-QOI UQ rerun, coefficient fitting/admission,
validation/holdout/external-test scoring, candidate freeze, final-score claim,
S11/S12/S13/S15/S6 trigger, endpoint proxy substitution, hidden multiplier,
residual absorption into internal Nu, blocker-register source change,
generated-index refresh, deletion, staging, commit, or runtime-leakage
relaxation occurred.
