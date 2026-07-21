---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/sampler_preflight_repair.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/raw_f6_endpoint_face_metrics.csv
tags: [pressure-ledger, f6, endpoint-sampler, raw-face, scheduler-handoff]
related:
  - .agent/journal/2026-07-21/f6-endpoint-raw-face-sampler.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/README.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-F6-ENDPOINT-RAW-FACE-SAMPLER
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: status
status: complete
---
# TODO-F6-ENDPOINT-RAW-FACE-SAMPLER Status

## Objective

Implement the narrow raw-face sampler unblock package for F6 endpoint candidates
without launching solver/postprocessing work, mutating native cases, fitting F6,
or admitting component K.

## Outcome

Complete as a scheduler-ready Stage A handoff. The package publishes repaired
preflight state, an eight-row Salt2 medium/fine endpoint-face launch matrix,
blocked coarse rows, raw-output schema rows, ordinary-flow and same-QOI UQ gap
templates, staged-copy runner scripts, and source/script manifests.

This row did not produce raw sampled face metrics. All eight Stage A raw rows
remain `pending_sampler_launch`; all twelve coarse endpoint-face rows remain
blocked until source-path repair proves the retained time and required fields.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-ENDPOINT-RAW-FACE-SAMPLER.md`
- `.agent/journal/2026-07-21/f6-endpoint-raw-face-sampler.md`
- `imports/2026-07-21_f6_endpoint_raw_face_sampler.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/**`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/build_f6_endpoint_raw_face_sampler.py` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/build_f6_endpoint_raw_face_sampler.py work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/test_f6_endpoint_raw_face_sampler.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/test_f6_endpoint_raw_face_sampler.py` passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/run_stage_a_f6_endpoint_sampler.sh` passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch` passed.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. No solver/postprocessing launch, Fluid
edit, external edit, F6 fit, component-K admission, clipped K, hidden global
multiplier, source-property promotion, or generated-index refresh was performed.

Future launch must be claimed under a separate scheduler-authorized board row
and should submit only the generated staged-copy sbatch. After the job lands,
rerun the builder with `--harvest --record-job-id <jobid>` before any UQ or
admission review.
