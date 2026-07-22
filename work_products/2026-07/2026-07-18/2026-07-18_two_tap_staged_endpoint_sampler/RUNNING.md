---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/run_two_tap_staged_endpoint_sampling.sh
tags: [pressure-ledger, two-tap, raw-endpoints, scheduler]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST.md
  - .agent/status/2026-07-18_TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST.md
task: TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST
date: 2026-07-18
role: Hydraulics/cfd-pp/Scheduler/Implementer/Tester/Writer
type: running-handoff
status: harvested-after-parser-fix
---
# Two-Tap Endpoint Sampling Run Handoff

## Purpose

Run the task-owned `two_tap_ep` Slurm postprocessing job to generate VTK
cutting-plane endpoint surfaces for Salt2/Salt3/Salt4 `corner_lower_right`, then
harvest raw pressure, velocity, density, temperature, mass-flux, RAF, RMF, and
SVF rows.

## Submit Command

```bash
sbatch work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch
```

## Attempt History

- Attempt 1 job ID: `3302384`
- Job name: `two_tap_ep`
- Submitted at: `2026-07-18T19:31:00+00:00`
- Last checked at: `2026-07-18T14:28:09-05:00`
- Last observed state: `FAILED`
- Exit code: `1:0`
- Elapsed: `00:00:11`
- Node: `c318-019`
- Attempt 2 job ID: `3302388`
- Attempt 2 submitted at: `2026-07-18T14:29:14-05:00`
- Attempt 2 last checked at: `2026-07-18T14:29:56-05:00`
- Attempt 2 last observed state: `FAILED`
- Attempt 2 exit code: `1:0`
- Attempt 2 elapsed: `00:00:15`
- Attempt 2 node: `c318-019`
- Attempt 3 job ID: `3302464`
- Attempt 3 task: `TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST`
- Attempt 3 submitted at: `2026-07-18T15:13:51-05:00`
- Attempt 3 last checked at: `2026-07-18T15:21:00-05:00`
- Attempt 3 last observed state: `FAILED`
- Attempt 3 exit code: `1:0`
- Attempt 3 elapsed: `00:06:58`
- Attempt 3 node: `c318-019`
- Attempt 3 OpenFOAM result: all six endpoint VTK surfaces written.
- Attempt 3 harvest result: Slurm failed in the old Python parser; local harvest succeeded after parser fix.

## Attempt 1 Failure

The first submitted job failed before producing raw endpoint surfaces. The
OpenFOAM log at
`work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/logs/salt2_mainline_foamPostProcess.log`
reported:

```text
could not detect processor number from objectPath:"tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged/salt2_mainline/constant/polyMesh/points"
```

This was a synthetic staging bug, not a raw endpoint measurement result. The
first runner symlinked `constant` and the selected time directory directly from
`processors64`, which made OpenFOAM treat the staged root case as decomposed
processor content. No native solver output was changed and no endpoint rows were
harvested from this failed attempt.

## Corrected Runner

The generated runner now stages an ordinary root-case view under
`tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/`, copies
`constant`, `system`, and `0` from the source case, links the source
`processors64` tree, reconstructs the requested time and fields with
`reconstructPar`, disables inherited `system/functions`, and then runs
`foamPostProcess` against the reconstructed staged copy.

## Attempt 2 Failure

The corrected replacement job reached `reconstructPar`, then failed because the
staged `system/` directory contained only the task controlDict and did not carry
the source `decomposeParDict`:

```text
cannot find file "tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt2_mainline/system/decomposeParDict"
```

The source case does contain
`jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/system/decomposeParDict`.
The generator has been fixed after job `3302388` so future staged copies merge
missing source `system` entries before replacing `system/controlDict` with the
task sampling controlDict. No third scheduler submission was made in this board
row.

## Submission Notes

Direct `sbatch` from the current shell reported that submission was unavailable
from the compute-node context. The same sbatch file was submitted unchanged via
`ssh login3`:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch"
```

## Runtime Paths

- Work product: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/`
- Task tmp: `tmp/2026-07-18_two_tap_staged_endpoint_sampler/`
- Logs: `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/logs/`
- Expected VTK outputs:
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt2_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/7915/plane_lower_leg__s04.vtk`
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt2_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/7915/plane_right_leg__s00.vtk`
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt3_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/7618/plane_lower_leg__s04.vtk`
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt3_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/7618/plane_right_leg__s00.vtk`
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt4_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/10000/plane_lower_leg__s04.vtk`
  - `tmp/2026-07-18_two_tap_staged_endpoint_sampler/staged_reconstructed/salt4_mainline/postProcessing/agentCTwoTapRawEndpointSurfaces/10000/plane_right_leg__s00.vtk`

## Harvest Command

Run only after Slurm reports terminal success:

```bash
python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id <job_id>
```

## Monitor Instructions

Use:

```bash
squeue -j <job_id>
sacct -j <job_id> --format=JobID,JobName,Partition,State,ExitCode,Elapsed,NodeList
```

Both authorized submissions in `TODO-TWO-TAP-ENDPOINT-LAUNCH-HARVEST` have
failed. Do not resubmit without a new board decision. The next scheduler row may
submit the regenerated runner once, then if that job is `COMPLETED` with exit
code `0:0`, run the harvest command and then run
`python3.11 -m unittest tools.analyze.test_two_tap_staged_endpoint_sampler`.

## Attempt 3 Resubmission Result

`TODO-TWO-TAP-ENDPOINT-RESUBMIT-HARVEST` submitted job `3302464`. The job
successfully reconstructed and postprocessed Salt2/Salt3/Salt4 staged copies
and wrote all six expected VTK endpoint surfaces. Slurm still reported
`FAILED` with exit code `1:0` because the final in-job Python harvest crashed on
OpenFOAM's wrapped `POLYGONS`/`FIELD attributes` VTK layout. The parser was
fixed after the job ended, and the same staged VTK files were harvested locally
with:

```bash
python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py --harvest --record-job-id 3302464
```

Final harvested state:

- `raw_endpoint_pressure_velocity.csv`: six `sampled` rows.
- `raw_endpoint_surface_file_manifest.csv`: six existing VTK files.
- `summary.json`: `raw_sampled_rows=6`, `raw_missing_rows=0`.
- Admission state: raw sample only; no F6 fit and no component-K admission.

## Guardrails

The job uses a task-owned staged view and writes only under the task work product
and `tmp/2026-07-18_two_tap_staged_endpoint_sampler/`. Do not mutate native CFD
outputs, registry/admission state, generated docs indexes, Fluid/external repos,
F6 fits, or component-K admission state.
