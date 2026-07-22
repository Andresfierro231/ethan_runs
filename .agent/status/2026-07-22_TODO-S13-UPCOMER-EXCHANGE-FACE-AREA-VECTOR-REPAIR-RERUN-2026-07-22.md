---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/summary.json
tags: [s13, upcomer-exchange, face-area-vector, medium-fine, repair]
related:
  - .agent/journal/2026-07-22/s13-upcomer-exchange-face-area-vector-repair-rerun.md
  - imports/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun.json
task: TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22

## Objective

Repair the S13 medium/fine exact-label sampler so generated trusted-wall and
exchange-interface face contracts include face area vector components required
by the exact reductions.

## Outcome

Complete. The completed sampler package failed closed with
`exact_label_qoi_rows=0` and `sampling_error_rows=6`; every
Salt2/Salt3/Salt4 medium/fine reduction reported missing face area vectors.

The current sampler source is ready for a fresh rerun: generated interface,
trusted-wall, and cap face rows are passed through `add_area_vector_columns`,
and `interface_reduction` fails closed if vector columns are absent. This row
added a writer-side regression test proving generated face-contract CSVs
preserve `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.

Decision: `face_vector_repair_source_ready_fresh_slurm_rerun_required`.

## Changes Made

- Claimed this narrow repair row.
- Added writer-side face-vector regression coverage in
  `tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`.
- Published the repair package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun/`.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_medium_fine_exact_label_sampler`:
  passed, `7` tests.
- `python3.11 -m json.tool work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun/summary.json`:
  passed.
- `python3.11 -m json.tool imports/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun.json`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22`:
  passed.

## Guardrails

Native solver outputs are read-only. No registry/admission mutation, scheduler
submission/cancel/requeue/dependency mutation, solver run, OpenFOAM postProcess
mutation, production harvest, source/property or Qwall release/admission,
coefficient admission, final score, S11/S12/S13/S15/S6 trigger,
blocker-register change, generated-index refresh before closeout, or proxy
substitution is allowed.
