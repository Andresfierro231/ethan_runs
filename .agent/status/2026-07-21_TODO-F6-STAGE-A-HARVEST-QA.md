---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/qa_gate_status.csv
tags: [f6, endpoint-sampler, harvest-qa, raw-face, no-admission]
related:
  - .agent/journal/2026-07-21/f6-stage-a-harvest-qa.md
  - imports/2026-07-21_f6_stage_a_harvest_qa.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/raw_f6_endpoint_face_metrics.csv
task: TODO-F6-STAGE-A-HARVEST-QA
date: 2026-07-21
role: cfd-pp / Hydraulics / Tester / Writer
type: status
status: complete
---
# TODO-F6-STAGE-A-HARVEST-QA Status

## Objective

QA the Stage A F6 endpoint raw-face harvest from job `3308082`, classify each
endpoint pair, and preserve no-admission guardrails.

## Outcome

Complete. The QA package confirms `8/8` endpoint face rows sampled with present
VTK surfaces and finite required reductions. All `4/4` endpoint pairs are
classified `recirc_diagnostic` because every pair fails the ordinary-flow gate
from material RAF/RMF. There are `0` ordinary candidates, `0` sample failures,
and `0` orientation failures.

No F6 fit or component-K admission is supported by this Stage A evidence.
Medium/fine consistency is diagnostic only until the `12` blocked coarse rows
are repaired or formally closed.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-STAGE-A-HARVEST-QA.md`
- `.agent/journal/2026-07-21/f6-stage-a-harvest-qa.md`
- `imports/2026-07-21_f6_stage_a_harvest_qa.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/build_f6_stage_a_harvest_qa.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/test_f6_stage_a_harvest_qa.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_face_qa.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/endpoint_pair_qa.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/medium_fine_consistency.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/qa_gate_status.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/summary.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/build_f6_stage_a_harvest_qa.py` initially failed because the repo root was resolved one parent too high; the script was corrected and rerun.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/build_f6_stage_a_harvest_qa.py` passed after repair.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/build_f6_stage_a_harvest_qa.py work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/test_f6_stage_a_harvest_qa.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/test_f6_stage_a_harvest_qa.py` passed with 4 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing launch, Fluid/external edit,
fitting/tuning/model selection, F6 fit, component-K admission, clipped K, hidden
global multiplier, blocker-register change, or generated-index refresh was
performed.

The next scoped task is `TODO-F6-COARSE-PATH-UQ-REPAIR`, followed by
`TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE` only after ordinary-flow and UQ evidence
can be evaluated.
