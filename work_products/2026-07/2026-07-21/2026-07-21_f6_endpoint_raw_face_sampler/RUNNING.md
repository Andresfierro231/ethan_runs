---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/run_stage_a_f6_endpoint_sampler.sh
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/stage_a_endpoint_face_matrix.csv
tags: [f6, endpoint-sampler, scheduler-handoff, raw-face]
related:
  - .agent/status/2026-07-21_TODO-F6-STAGE-A-SAMPLER-SUBMIT.md
  - .agent/journal/2026-07-21/f6-stage-a-sampler-submit.md
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-F6-STAGE-A-SAMPLER-SUBMIT
date: 2026-07-21
role: Scheduler / cfd-pp / Tester / Writer
type: operational_note
status: active
---
# F6 Stage A Endpoint Raw-Face Sampler Running Handoff

## Job

- Task: `TODO-F6-STAGE-A-SAMPLER-SUBMIT`
- Job ID: `3308082`
- Job name: `f6_face_sA`
- Submitted from: `login3.ls6.tacc.utexas.edu`
- Submit command: `ssh login3.ls6.tacc.utexas.edu sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/scripts/submit_stage_a_f6_endpoint_sampler.sbatch`
- Initial state: `RUNNING` on `c318-012` at `2026-07-21T12:44:35-05:00`
- Walltime request: `02:00:00`
- Partition/account: `NuclearEnergy` / `ASC23046`

The direct local `sbatch` attempt from `c318-008` did not submit a job; the
compute-node wrapper only printed `sbatch not available on compute nodes`.

## Logs

- Slurm stdout: `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.out`
- Slurm stderr/progress log: `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/slurm-3308082.err`
- Per-case reconstruct logs expected after case launch:
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/salt_2_medium_reconstructPar.log`
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/salt_2_fine_reconstructPar.log`
- Per-case sampler logs expected after reconstruction:
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/salt_2_medium_foamPostProcess.log`
  - `work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/logs/salt_2_fine_foamPostProcess.log`

## Expected Outputs

The job should stage reconstructed copies under:

- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_medium`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_fine`

Expected raw VTK surfaces:

- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_medium/postProcessing/agentF6EndpointRawFaceSurfaces/518/plane_right_leg__s03.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_medium/postProcessing/agentF6EndpointRawFaceSurfaces/518/plane_right_leg__s01.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_medium/postProcessing/agentF6EndpointRawFaceSurfaces/518/plane_test_section_span__s03.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_medium/postProcessing/agentF6EndpointRawFaceSurfaces/518/plane_test_section_span__s01.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_fine/postProcessing/agentF6EndpointRawFaceSurfaces/399/plane_right_leg__s03.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_fine/postProcessing/agentF6EndpointRawFaceSurfaces/399/plane_right_leg__s01.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_fine/postProcessing/agentF6EndpointRawFaceSurfaces/399/plane_test_section_span__s03.vtk`
- `tmp/2026-07-21_f6_endpoint_raw_face_sampler/staged_reconstructed/salt_2_fine/postProcessing/agentF6EndpointRawFaceSurfaces/399/plane_test_section_span__s01.vtk`

If the job reaches the final harvest step, it will rerun
`build_f6_endpoint_raw_face_sampler.py --harvest --record-job-id 3308082`.

## Monitor Instructions

Claim `TODO-F6-STAGE-A-SAMPLER-MONITOR` before doing continuing monitor work.
Use:

- `squeue -j 3308082`
- `sacct -j 3308082 --format=JobID,JobName%24,State,ExitCode,Elapsed,NodeList%20,Start,End`
- `tail -40` on the Slurm and per-case logs
- existence checks for the eight VTK paths above

Report terminal state only. Do not submit a duplicate job, cancel/requeue the
job, harvest outputs, edit parser code, admit F6, admit component K, clip K, or
apply a global multiplier from the monitor row.

Killing this conversation shell or the `c318-008` interactive allocation should
not kill job `3308082`; it is a Slurm batch job. Only `scancel 3308082` would
cancel it, and that is forbidden without a new scheduler-control row.
