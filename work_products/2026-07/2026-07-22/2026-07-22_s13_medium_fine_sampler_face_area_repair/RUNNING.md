---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch
tags: [s13, sampler-repair, slurm, medium-fine, face-area-vector]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22.md
  - .agent/journal/2026-07-22/s13-medium-fine-sampler-face-area-repair.md
task: TODO-S13-MEDIUM-FINE-SAMPLER-FACE-AREA-REPAIR-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Scheduler
type: handoff
status: complete
---
# S13 Medium/Fine Sampler Face-Area Repair Handoff

## Job

- Superseded full-run jobs: `3310996`, `3311004`
- Clean smoke job: `3311109`
- Clean smoke package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/`

Jobs `3310996` and `3311004` were canceled to enforce the requirement that a
one-case/window smoke pass before any full six-case rerun. Smoke job `3311109`
completed `0:0` on `c318-018` from `2026-07-22T11:44:59` to
`2026-07-22T11:49:50`.

## Repair Under Test

The sampler now derives selected face area vectors from each medium/fine
`constant/polyMesh/faces` plus `points`, writes `area_vector_x/y/z_m2` into
generated face contracts, and uses those vectors directly in the task-local
interface reduction. This avoids the prior coarse-mesh face-vector lookup that
failed for medium/fine face ids.

## Completion Signal

The clean smoke package has:

- `summary.json`: `exact_label_qoi_rows=4`, `sampling_error_rows=0`,
  `terminal_window_reduction_rows=1`, `native_solver_outputs_mutated=false`.
- `faces/salt_2_medium_exchange_interface_faces.csv`: includes
  `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.
- `medium_fine_exact_label_qoi_rows.csv`: includes `Q_wall_W`,
  `mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
  `wall_core_bulk_temperature_contrast_K`.
- `logs/slurm-3311109.err`: empty at closeout.

Success for this row means the sampler contract is repaired and smoke-tested.
Mesh/GCI and production harvest remain separate next rows after a full six-case
rerun produces complete medium/fine exact-label rows.

## Forbidden Actions

Do not use partial outputs from canceled jobs `3310996` or `3311004` as
production, mesh/GCI, or admission evidence. Do not run mesh/GCI disposition,
harvest, fit coefficients, release Qwall/source-property rows, mutate native
OpenFOAM outputs, edit registry/admission state, trigger S11/S12/S13/S15/S6, or
replace exact labels with endpoint/probe/profile proxies.

## 2026-07-22 11:11 CDT Monitor Update

Codex observed job `3310996` already running; no additional sampler was
submitted. `squeue -j 3310996 -o "%i|%j|%T|%M|%N|%Z|%o"` reported:

`3310996|s13_mf_sampler|RUNNING|3:48|c318-019|/home1/09748/andresfierro231|/scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch`

Local validation before this monitor update:

- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_medium_fine_exact_label_sampler`
  passed: `7` tests.
- Dry preflight to
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/preflight/`
  reported `source_preflight_ready_rows=6`, `execute_mode=false`, and
  `decision=preflight_ready_heavy_execution_not_run`.

The running job still writes to the original sampler package. At the monitor
check, `slurm-3310996.out` and `slurm-3310996.err` were empty, and the existing
`salt_2_medium_exchange_interface_faces.csv` header in that package still lacked
the `area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2` columns,
which means the job had not yet replaced that face contract at the time of the
check.

## 2026-07-22 Smoke-First Closeout

After smoke-first sequencing was required, canceled `3310996` and `3311004`.
`3311004` had already emitted partial Salt2 medium/fine face files with
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`, but that package
is superseded because it was canceled mid-run.

Submitted and inspected the clean one-case/window smoke `3311109`. It passed
with four exact-label QOI rows and zero sampling errors, proving the repaired
face-area-vector contract before any full six-case rerun.
