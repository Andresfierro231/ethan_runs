---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_model_use_decision.json
tags: [pressure-ledger, minor-loss, source-envelope, same-qoi-uq]
related:
  - .agent/journal/2026-07-21/pressure-corner-comparison-admission-review.md
  - imports/2026-07-21_pressure_corner_comparison_admission_review.json
task: TODO-PRESSURE-CORNER-COMPARISON-ADMISSION-REVIEW
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: status
status: complete
---

# TODO-PRESSURE-CORNER-COMPARISON-ADMISSION-REVIEW

## Objective

Compare the frozen July 21 pressure-corner result against later pressure-basis,
recirculation, source-envelope, and same-QOI uncertainty evidence. Decide the
allowed model-use label per row without admitting any coefficient unless all
predeclared gates pass.

## Changes Made

- Created `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/`.
- Added `build_pressure_corner_comparison_admission_review.py` and
  `test_pressure_corner_comparison_admission_review.py`.
- Published `pressure_corner_comparison_matrix.csv` with 3 reviewed
  `corner_lower_right` rows.
- Published `pressure_corner_gate_review.csv` with 24 row/gate decisions.
- Published `pressure_corner_model_use_decision.json`,
  `publication_delta_note.md`, `source_manifest.csv`, `summary.json`, and the
  package `README.md`.

## Outcome

The July 21 publication freeze is confirmed. All three Salt2/Salt3/Salt4
`corner_lower_right` rows remain `section_effective` pressure-residual /
pressure-recovery diagnostics. Counts: 3 rows reviewed, 24 gate rows,
3 `section_effective` labels, 0 `component_K` rows, 0 `cluster_K` rows, and
0 F6 rows.

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/build_pressure_corner_comparison_admission_review.py` — passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/build_pressure_corner_comparison_admission_review.py work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/test_pressure_corner_comparison_admission_review.py` — passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/test_pressure_corner_comparison_admission_review.py` — passed.

## Guardrails

No native CFD/OpenFOAM outputs were mutated. No registry/admission state was
changed. No scheduler action, solver/postprocessing launch, Fluid edit, external
edit, fitting, tuning, model selection, F6 fit, component-`K` admission,
cluster-`K` admission, clipped `K`, hidden global multiplier, blocker-register
edit, or generated-index refresh was performed.

## Remaining Blockers / Next Useful Action

Component or cluster pressure-loss admission still needs an ordinary
low-reverse same-topology anchor, same-QOI time/mesh uncertainty, same-basis
straight/developing reference, source-envelope geometry recovery, and explicit
component isolation. F6 remains a separate endpoint-pressure lane.
