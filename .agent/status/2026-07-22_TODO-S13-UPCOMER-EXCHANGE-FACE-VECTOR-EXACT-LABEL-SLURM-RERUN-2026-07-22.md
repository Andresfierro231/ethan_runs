---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun/summary.json
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [s13, upcomer-exchange, slurm, exact-label, face-vector, superseded]
related:
  - .agent/journal/2026-07-22/s13-upcomer-exchange-face-vector-exact-label-slurm-rerun.md
  - imports/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun.json
task: TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22
date: 2026-07-22
role: Scheduler/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-FACE-VECTOR-EXACT-LABEL-SLURM-RERUN-2026-07-22

## Objective

Submit exactly one fresh S13 medium/fine exact-label sampler rerun from the
current face-vector-ready source, writing to a new task-owned output package.
This row was superseded when the user required a one-case/window smoke before
any full six-case Slurm rerun.

## Outcome So Far

Complete/canceled superseded handoff. Slurm job `3311004` was submitted
through `login3`, started on `c318-012` at `2026-07-22T11:14:17`, and was
canceled at `2026-07-22T11:42:10` to enforce the smoke-first requirement.

The canceled package produced partial Salt2 medium/fine face files before
cancellation. Those files are not admissible production evidence. They do,
however, confirm the repaired writer now emits `area_vector_x_m2`,
`area_vector_y_m2`, and `area_vector_z_m2` in generated
`*_exchange_interface_faces.csv` rows before interface reduction.

The clean smoke gate moved to
`TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22` as Slurm job
`3311109`.

## Changes Made

- Claimed this scheduler rerun row.
- Created task-owned output/log directory and Slurm wrapper.
- Submitted exactly one Slurm job: `3311004`.
- Canceled `3311004` after the user required one-case/window smoke before any
  full six-case rerun.
- Marked this package as superseded/non-admissible and transferred the active
  smoke gate to job `3311109`.

## Validation

- `bash -n work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun/run_face_vector_exact_label_sampler.sbatch`:
  passed.
- `python3.11 -m json.tool imports/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun.json`:
  passed before submission.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_medium_fine_exact_label_sampler`:
  passed, `7` tests.
- `ssh login3 sbatch .../run_face_vector_exact_label_sampler.sbatch`: submitted
  batch job `3311004`.
- `squeue -j 3311004`: job `3311004` pending for `Resources`.
- `sacct -j 3311004 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`:
  job `3311004` `PENDING`, exit code `0:0`, no node assigned.
- later `squeue -j 3311004`: job `3311004` `RUNNING` on `c318-012`.
- later `sacct -j 3311004 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`:
  job `3311004` and batch step `RUNNING`, start `2026-07-22T11:14:17`,
  node `c318-012`.
- `sacct -j 3311004 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`:
  job `3311004` and batch step `CANCELLED`, exit code `0:15`, end
  `2026-07-22T11:42:10`, node `c318-012`.
- `head -5 work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_face_vector_exact_label_slurm_rerun/faces/salt_2_medium_exchange_interface_faces.csv`:
  header includes `area_vector_x_m2`, `area_vector_y_m2`, and
  `area_vector_z_m2`.

## Superseded Handoff

Do not consume this package for production harvest, admission, or mesh/GCI.
It was canceled before full completion and exists only as scheduler/provenance
evidence for the superseded full-rerun attempt.

The active next step is to monitor clean smoke job `3311109` in
`work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/`.

## Guardrails

Native solver outputs are read-only. No registry/admission mutation,
OpenFOAM solver or postProcess mutation, production harvest, mesh/GCI
disposition, Qwall/source-property release, coefficient admission, final score,
or S11/S12/S13/S15/S6 trigger occurred from this row. The scheduler cancellation
was limited to superseding `3311004` under the smoke-first requirement.
