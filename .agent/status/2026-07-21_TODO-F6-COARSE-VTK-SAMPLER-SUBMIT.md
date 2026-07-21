---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_raw_face_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_pair_diagnostics.csv
tags: [f6, coarse-vtk, raw-face, scheduler, no-admission]
related:
  - .agent/journal/2026-07-21/f6-coarse-vtk-sampler-submit.md
  - imports/2026-07-21_f6_coarse_vtk_sampler_submit.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/summary.json
task: TODO-F6-COARSE-VTK-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: status
status: complete
---
# TODO-F6-COARSE-VTK-SAMPLER-SUBMIT Status

## Objective

Build and submit the Stage B coarse VTK face-area/recirculation sampler for the
12 repaired F6 coarse endpoint rows using available `p_rgh`, `U`, `rho`, and
`T`; preserve the missing-static-`p` blocker and no-admission guardrails.

## Outcome

Complete. The Stage B sampler was built, locally validated, submitted once as
Slurm job `3308382`, and completed successfully with exit `0:0` in `00:01:04`
on `c318-016`.

All `12/12` expected coarse VTK endpoint surfaces landed and were harvested into
diagnostic tables. All 12 raw-face rows still have
`static_pressure_basis_status=blocked_missing_static_p`, with blank static
`p_mean_pa`. All 6 endpoint pairs are `coarse_pair_sampled_diagnostic`; no F6,
component-K, cluster-K, clipped-K, or global-multiplier admission was made.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-COARSE-VTK-SAMPLER-SUBMIT.md`
- `.agent/journal/2026-07-21/f6-coarse-vtk-sampler-submit.md`
- `imports/2026-07-21_f6_coarse_vtk_sampler_submit.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/RUNNING.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/build_f6_coarse_vtk_sampler_submit.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/test_f6_coarse_vtk_sampler_submit.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/stage_b_coarse_endpoint_face_matrix.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_raw_face_metrics.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_pair_diagnostics.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/coarse_static_pressure_blocker.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/script_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/summary.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/scripts/**`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/**`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/build_f6_coarse_vtk_sampler_submit.py` passed before submission.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/scripts/run_stage_b_f6_coarse_vtk_sampler.sh` passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/scripts/submit_stage_b_f6_coarse_vtk_sampler.sbatch` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/build_f6_coarse_vtk_sampler_submit.py work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/test_f6_coarse_vtk_sampler_submit.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/test_f6_coarse_vtk_sampler_submit.py` passed with 5 tests.
- `ssh login3.ls6.tacc.utexas.edu "sacct -j 3308382 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList"` reported `COMPLETED 0:0`.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/build_f6_coarse_vtk_sampler_submit.py --harvest --submitted --record-job-id 3308382` passed after terminal completion.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. The sampler used staged/symlinked
working cases under `tmp/2026-07-21_f6_coarse_vtk_sampler_submit/`. Registry and
admission state were not mutated. Static pressure was not reconstructed from
`p_rgh`. No Fluid/external edit, fitting/tuning/model selection, F6 fit,
component-K admission, cluster-K admission, clipped K, hidden global multiplier,
blocker-register change, or generated-index refresh was performed.

Next useful task: claim a separate Stage B harvest-QA/admission-refresh row to
join these coarse diagnostics with the existing F6 same-QOI gate. Any pressure
basis reconstruction must remain a separate explicitly scoped task.
