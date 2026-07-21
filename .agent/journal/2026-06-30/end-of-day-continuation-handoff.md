# End-of-Day Continuation Handoff

Date: 2026-06-30
Written: 2026-06-30T17:30:08-0500 CDT
Owner: codex

## Purpose

This is the single pickup note for tomorrow. It consolidates today's context
from the OpenFOAM scaling-study lane and the 3D-to-1D field-reduction methods
lane.

## Active Workstreams From Today

### AGENT-160: OpenFOAM parallel scaling and optimization

Goal: quantify whether the current OpenFOAM parallel run setup can be improved
by changing MPI rank count, decomposition, and I/O policy.

Task files:

- `.agent/status/2026-06-30_AGENT-160.md`
- `.agent/journal/2026-06-30/scaling-study.md`
- `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/`

Key decisions:

- Source continuation trees stay read-only.
- Benchmark clones are staged under:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/work/`
- Results are expected under:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/results/`
- Source case for the first two pilots:
  `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation`
- Latest retained source processor time at setup: `7915`.
- Mesh size from `constant/polyMesh/owner`: `nCells:2166996`.
- Current production decomposition: `64` ranks, `scotch`.

Scheduled jobs as of 2026-06-30T17:30 CDT:

```text
JOBID    PARTITION      NAME         STATE                  START_TIME
3268028  NuclearEnergy  of_s2_scale  PENDING (BeginTime)    2026-06-30T20:00:00
3268024  NuclearEnergy  of_s2_opt    PENDING (BeginTime)    2026-07-01T20:00:00
```

`3268028` is tonight's rank-count pilot:

- window: 2026-06-30 20:00 CDT to 2026-07-01 08:00 CDT
- walltime: `12:00:00`
- node/task request: `1` node, `256` tasks
- rank variants: `32`, `64`, `128`, `256`
- decomposition: `scotch`
- script:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/scripts/run_salt2_scotch_rank_pilot.sbatch`
- expected summary:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/results/job_3268028/scaling_summary.csv`
- stdout/stderr:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.out`
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.err`

Important correction:

- Initial rank-pilot submission `3267856` was canceled before start after the
  generated `decomposeParDict` header was simplified.
- Active rank-pilot job is `3268028`.
- Ignore `3267856` for results.

`3268024` is tomorrow night's optimization follow-up:

- window: 2026-07-01 20:00 CDT to 2026-07-02 08:00 CDT
- walltime: `12:00:00`
- node/task request: `1` node, `256` tasks
- default benchmark rank count: `64`
- script:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/scripts/run_salt2_method_io_followup.sbatch`
- variants:
  - `scotch_prod_io`: `scotch`, `writeInterval 1`, compression off
  - `scotch_sparse_io`: `scotch`, `writeInterval 1000`, compression off
  - `scotch_sparse_compressed`: `scotch`, `writeInterval 1000`, compression on
  - `hierarchical_sparse_io`: `hierarchical`, `writeInterval 1000`,
    compression off
- expected summary:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/results/job_3268024/optimization_summary.csv`

Tomorrow morning pickup for AGENT-160:

```bash
sacct -j 3268028 --format JobID,JobName%30,Partition,State,Elapsed,NNodes,NTasks,AllocCPUS,MaxRSS,MaxVMSize
tail -80 jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.out
tail -80 jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.err
cat jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/results/job_3268028/scaling_summary.csv
```

Decision before 2026-07-01 20:00 CDT:

- If `3268028` strongly favors a non-64 rank, cancel and resubmit `3268024`
  with an updated `BENCHMARK_RANKS`.
- If `64` remains acceptable or the rank pilot is inconclusive, let `3268024`
  run as scheduled.

### AGENT-161: 3D-to-1D field-reduction methods report

Goal: write a paper-ready report explaining how OpenFOAM 3D field data are
reduced to 1D profiles and closure quantities, including whether native
OpenFOAM zones/sets are used.

Task files:

- `.agent/status/2026-06-30_AGENT-161.md`
- `.agent/journal/2026-06-30/3d-to-1d-field-reduction-methods.md`
- `reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/`

Deliverables:

- `reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/README.md`
- `reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/summary.json`

Status:

- Complete / ready for user review.
- No AGENT-156-owned operational notes were edited.
- Existing AGENT-156 notes were cited as source material only.

Key content in the report:

- Native OpenFOAM `faceZones`, `faceSets`, `cellSets`, and `cellZones` are used
  when they encode meaningful monitor surfaces or regions.
- In the inspected Salt 2 Jin case:
  - `faceZones` contains four mdot monitor planes.
  - `constant/polyMesh/sets` contains mdot `faceSet` objects and `piv_slab` as
    a `cellSet`.
  - `cellZones` contains 33 geometry/topology zones.
- Zones/sets are useful provenance anchors and monitor supports, but not a
  complete 1D streamwise reduction basis.
- The full 3D-to-1D path still requires:
  - `tools/case_analysis_profiles.py`
  - repaired streamwise station definitions
  - wall patch membership
  - flow-direction hints
  - single-leg cross-section masking
  - QC gates for alignment, area support, flux support, and temperature
    difference.
- The report includes paper-ready methods prose.

Validation already run:

```bash
python3.11 -m json.tool reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/summary.json
rg -n "cellSets|faceSets|faceSet|cellSet|faceZones|cellZones|sets/" \
  reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/README.md \
  reports/2026-06/2026-06-30/2026-06-30_3d_to_1d_field_reduction_methods/summary.json
```

Suggested next work:

- If user wants this report polished further, turn the methods report into a
  manuscript-style section with figure/table callouts.
- Add a small provenance table listing each native set/zone and where it is used
  in reductions.
- Optionally add a diagram of the 3D-to-1D reduction pipeline.

## Other Context

The queue also has unrelated active production jobs:

- `3265969` `ethan_s34mid_ne5d`
- `3265970` `ethan_w1234_ne5d`
- `3265971` `ethan_s41lo2mid_ne5d`
- `3265972` `ethan_s123hi_ne5d`

Those were not touched today by the scaling-study work.

Current interactive allocation:

- `3267228` on `NuclearEnergy-dev` / `c318-008`

Smoke checks for the scaling wrappers were run on that node and passed.

## Board State

New board rows added today:

- `AGENT-160`: OpenFOAM parallel scaling and optimization handoff.
- `AGENT-161`: 3D-to-1D field-reduction methods report.

Use the task-specific status files first if continuing either lane.

## Priority Order Tomorrow

1. Check `3268028` after 08:00 CDT.
2. Parse rank-count results and decide whether `3268024` needs adjustment
   before 20:00 CDT.
3. If asked, review/polish the 3D-to-1D methods report.
4. Do not edit active production case trees; continue using benchmark clones
   and report packages.

