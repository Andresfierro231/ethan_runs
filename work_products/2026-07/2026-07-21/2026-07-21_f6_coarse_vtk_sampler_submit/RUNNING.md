---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/scripts/submit_stage_b_f6_coarse_vtk_sampler.sbatch
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/stage_b_coarse_endpoint_face_matrix.csv
tags: [f6, coarse-vtk, running, scheduler, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-COARSE-VTK-SAMPLER-SUBMIT.md
  - .agent/journal/2026-07-21/f6-coarse-vtk-sampler-submit.md
task: TODO-F6-COARSE-VTK-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: running-handoff
status: complete
---
# F6 Stage B Coarse VTK Sampler Running Handoff

## Scheduler State

- Job ID: `3308382`
- Job name: `f6_face_sB`
- Submitted from: `login3.ls6.tacc.utexas.edu`
- Immediate observed state: running on `c318-016` at `2026-07-21T14:55:xx-05:00`
- Terminal observed state: `COMPLETED 0:0`, elapsed `00:01:04`, node `c318-016`
- Command:

```bash
ssh login3.ls6.tacc.utexas.edu "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/scripts/submit_stage_b_f6_coarse_vtk_sampler.sbatch"
```

## Logs

- Slurm stdout: `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/slurm-3308382.out`
- Slurm stderr: `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/slurm-3308382.err`
- Case logs:
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/salt_2_coarse_foamPostProcess.log`
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/salt_3_coarse_foamPostProcess.log`
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/logs/salt_4_coarse_foamPostProcess.log`

## Expected Outputs

The job should produce 12 VTK surfaces under:

`tmp/2026-07-21_f6_coarse_vtk_sampler_submit/staged_reconstructed/<case>/postProcessing/agentF6CoarseRawFaceSurfaces/<time>/plane_<station>.vtk`

Expected cases and times:

- `salt_2_coarse`, time `7915`
- `salt_3_coarse`, time `7618`
- `salt_4_coarse`, time `10000`

Expected stations for each case:

- `right_leg__s03`
- `right_leg__s01`
- `test_section_span__s03`
- `test_section_span__s01`

## Monitor / QA Instructions

Check:

```bash
squeue -j 3308382
sacct -j 3308382 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList
```

The terminal successful state has been observed. The harvest command was rerun:

```bash
python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_vtk_sampler_submit/build_f6_coarse_vtk_sampler_submit.py --harvest --submitted --record-job-id 3308382
```

Claim a separate QA row before interpreting the harvested diagnostics or
refreshing the F6 admission gate.

## Forbidden Without A New Row

- Do not submit a duplicate Stage B sampler job.
- Do not reconstruct static `p` from `p_rgh`.
- Do not mutate native OpenFOAM outputs.
- Do not mutate registry or admission state.
- Do not admit F6, component K, cluster K, clipped K, or a global multiplier.
