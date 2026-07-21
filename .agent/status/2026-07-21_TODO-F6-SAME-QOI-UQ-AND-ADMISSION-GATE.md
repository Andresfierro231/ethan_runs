---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f6_candidate_admission_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/gate_rollup.csv
tags: [f6, same-qoi-uq, admission-gate, diagnostic, no-admission]
related:
  - .agent/journal/2026-07-21/f6-same-qoi-uq-and-admission-gate.md
  - imports/2026-07-21_f6_same_qoi_uq_and_admission_gate.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/README.md
task: TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE
date: 2026-07-21
role: Hydraulics / Reviewer / Tester / Writer
type: status
status: complete
---
# TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE Status

## Objective

Combine current F6 harvested raw-face metrics, ordinary-flow gates, coarse
source/UQ repair status, same-QOI UQ context, and F3 comparison readiness into
a row-by-row admission decision table.

## Outcome

Complete. The package emits `12` decision rows:

- `4` Stage A medium/fine endpoint-pair rows from current harvested raw faces.
- `6` coarse mesh/UQ context rows from the repaired coarse path package.
- `2` historical same-QOI F6 UQ context rows from the LitRev execution package.

All `12` rows are labeled `diagnostic`, with explicit reasons. The gate rollup
is: raw face sampling `pass`, ordinary-flow `fail`, coarse static-pressure
basis `blocked`, same-QOI mesh/UQ `blocked`, F3 comparison
`not_evaluated_no_ordinary_candidate`, and admission `closed`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE.md`
- `.agent/journal/2026-07-21/f6-same-qoi-uq-and-admission-gate.md`
- `imports/2026-07-21_f6_same_qoi_uq_and_admission_gate.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/build_f6_same_qoi_uq_and_admission_gate.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/test_f6_same_qoi_uq_and_admission_gate.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f6_candidate_admission_decision.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/gate_rollup.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/f3_comparison_status.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/summary.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/build_f6_same_qoi_uq_and_admission_gate.py` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/build_f6_same_qoi_uq_and_admission_gate.py work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/test_f6_same_qoi_uq_and_admission_gate.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/test_f6_same_qoi_uq_and_admission_gate.py` passed with 4 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing launch, Fluid/external edit,
fitting/tuning/model selection, F6 fit, component-K admission, cluster-K
admission, clipped K, hidden global multiplier, blocker-register change, or
generated-index refresh was performed.

The next practical unblocker is `TODO-F6-COARSE-VTK-SAMPLER-SUBMIT`, followed
only later by pressure-basis reconstruction if a task explicitly defines how
`p_rgh` becomes an admissible static-pressure basis.
