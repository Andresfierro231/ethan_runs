---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/RUNNING.md
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [status, s13, sampler-repair, face-area-vector, smoke-passed]
related:
  - .agent/journal/2026-07-22/s13-medium-fine-sampler-face-area-repair.md
  - imports/2026-07-22_s13_medium_fine_sampler_face_area_repair.json
task: TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Scheduler
type: status
status: complete
---
# TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22

## Objective

Repair the S13 medium/fine exact-label sampler blocker where generated
exchange-interface rows lacked face-area-vector components, causing all six
medium/fine reductions to fail before QOI sampling.

## Current Outcome

Status: `complete`, smoke-first enforced and passed.

The source-level sampler tests now pass the face-area-vector contract locally.
The sampler has explicit one-case/window controls: `--case-id`, `--mesh-level`,
and `--max-windows`. Full six-case reruns `3310996` and `3311004` were
cancelled to enforce the smoke-first requirement. A clean one-case/window smoke
was submitted as Slurm job `3311109`; it completed `0:0` on `c318-018` from
`2026-07-22T11:44:59` to `2026-07-22T11:49:50`.

The clean smoke package produced `4` exact-label QOI rows and `0` sampling
errors. Its generated `faces/salt_2_medium_exchange_interface_faces.csv`
contains `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2` before
interface reduction. Production harvest and admission remain closed because
full medium/fine six-case rows and same-label mesh/GCI are separate follow-on
gates.

## Changes Made

- Ran local unit tests for
  `tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`.
- Ran a no-heavy dry preflight into
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/preflight/`.
- Updated the repair `RUNNING.md` with current scheduler/log/output checks.
- Added this status, journal, and import manifest for handoff.
- Patched the sampler with `--case-id`, `--mesh-level`, and `--max-windows`
  controls.
- Added tests for filtered one-case/window smoke mode.
- Added a clean smoke package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/`.
- Cancelled full six-case jobs `3310996` and `3311004` before smoke completion.
- Submitted smoke job `3311109`.
- Inspected clean smoke outputs after terminal completion.

## Validation

- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_medium_fine_exact_label_sampler`
  passed: `7` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py --out work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/preflight`
  passed with decision `preflight_ready_heavy_execution_not_run`.
- `squeue -j 3310996 -o "%i|%j|%T|%M|%N|%Z|%o"` showed the existing sampler
  rerun `RUNNING` on `c318-019`.
- `scancel 3310996 3311004` completed.
- `sacct -j 3310996,3311004 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`
  showed both full reruns `CANCELLED`.
- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py`
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_medium_fine_exact_label_sampler`
  passed: `9` tests.
- `bash -n work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/run_smoke_salt2_medium_one_window.sbatch`
  passed.
- `ssh login3 sbatch .../run_smoke_salt2_medium_one_window.sbatch` submitted
  batch job `3311109`.
- `squeue -j 3311109` returned no active queue row after completion.
- `sacct -j 3311109 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList`
  showed job and batch step `COMPLETED`, exit code `0:0`, elapsed `00:04:51`,
  node `c318-018`, start `2026-07-22T11:44:59`, end
  `2026-07-22T11:49:50`.
- `cat .../smoke_salt2_medium_one_window/summary.json` showed decision
  `terminal_exact_label_rows_sampled_mesh_gci_fail_closed_time_equivalence_missing`,
  `exact_label_qoi_rows=4`, `sampling_error_rows=0`, and
  `native_solver_outputs_mutated=false`.
- `head -5 .../faces/salt_2_medium_exchange_interface_faces.csv` showed
  `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.
- `head -20 .../medium_fine_exact_label_qoi_rows.csv` showed exact labels for
  `Q_wall_W`, `mdot_exchange_positive_outward_proxy_kg_s`,
  `tau_recirc_proxy_s`, and `wall_core_bulk_temperature_contrast_K`.
- `wc -l .../medium_fine_exact_label_qoi_rows.csv .../medium_fine_terminal_window_reductions.csv .../sampling_error_log.csv`
  showed `5`, `2`, and `1` lines respectively: four QOI data rows, one
  terminal reduction data row, and zero sampling-error data rows.
- `tail -60 .../logs/slurm-3311109.err` was empty.
- `python3 tools/docs/build_repo_index.py` completed: indexed `2913` docs,
  `14` board rows, and `15` blockers.
- `git diff --check` passed after stripping trailing whitespace from generated
  `.agent/catalog.csv`.

## Assumptions

- Full six-case rerun should be claimed as a separate row using the smoke-passed
  sampler contract.
- Mesh/GCI disposition must remain a separate row after terminal exact-label
  rows exist.

## Caveats

The smoke was only one case, one mesh, and one window. It proves the sampler
contract and one terminal reduction path, not same-label mesh/GCI or production
admission.

## Guardrails

No duplicate scheduler submission, native-output mutation,
registry/admission mutation, OpenFOAM solver/postProcess mutation, production
harvest, Qwall/source/property release, coefficient admission, final-score
claim, S11/S12/S13/S15/S6 trigger, generated-index refresh, proxy substitution,
or residual absorption into internal `Nu` occurred in this repair/smoke row.

Scheduler cancellation did occur for jobs `3310996` and `3311004` specifically
to enforce the user-requested smoke-before-full-rerun sequencing.
