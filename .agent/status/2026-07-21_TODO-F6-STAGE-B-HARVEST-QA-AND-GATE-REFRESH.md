---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/f6_gate_refresh.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/blocker_delta.csv
tags: [f6, stage-b-qa, gate-refresh, recirculation, no-admission]
related:
  - .agent/journal/2026-07-21/f6-stage-b-harvest-qa-and-gate-refresh.md
  - imports/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/summary.json
task: TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: status
status: complete
---
# TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH Status

## Objective

Merge Stage A medium/fine and Stage B coarse F6 harvested diagnostics into a
single QA/gate-refresh package, preserving the static-pressure blocker and
no-admission guardrails.

## Outcome

Complete. The package represents `20/20` endpoint faces and `10/10` endpoint
pairs:

- Stage A: `8` medium/fine faces and `4` Salt2 pairs.
- Stage B: `12` coarse faces and `6` Salt2/Salt3/Salt4 pairs.

All `20` faces are sampled. All `10` endpoint pairs are diagnostic. The
coarse-VTK-output blocker is resolved, but ordinary-flow remains failed,
coarse static `p` remains missing for `12` endpoint faces, same-QOI mesh/UQ
remains blocked, F3 comparison remains `not_evaluated_no_ordinary_candidate`,
and admission remains closed.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-STAGE-B-HARVEST-QA-AND-GATE-REFRESH.md`
- `.agent/journal/2026-07-21/f6-stage-b-harvest-qa-and-gate-refresh.md`
- `imports/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/build_f6_stage_b_harvest_qa_and_gate_refresh.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/test_f6_stage_b_harvest_qa_and_gate_refresh.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_face_qa.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/stage_a_b_pair_qa.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/f6_gate_refresh.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/blocker_delta.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/summary.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/build_f6_stage_b_harvest_qa_and_gate_refresh.py` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/build_f6_stage_b_harvest_qa_and_gate_refresh.py work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/test_f6_stage_b_harvest_qa_and_gate_refresh.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_stage_b_harvest_qa_and_gate_refresh/test_f6_stage_b_harvest_qa_and_gate_refresh.py` passed with 5 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing/sampler launch,
Fluid/external edit, static-pressure reconstruction, fitting/tuning/model
selection, F6 fit, component-K admission, cluster-K admission, clipped K, hidden
global multiplier, blocker-register change, or generated-index refresh was
performed.

Next rows queued on the board: `TODO-F6-STATIC-P-BASIS-RECONSTRUCTION-AUDIT`
and `TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE`. The existing S10 low-recirc
study row remains the right place to search for ordinary-flow anchors.
