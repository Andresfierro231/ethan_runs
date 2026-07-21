# Scaling Study

Date: 2026-06-30
Task: AGENT-160
Role: Coordinator / Implementer / Writer

## Objective

Run a bounded OpenFOAM parallel scaling pilot for the Ethan Salt 2 Jin
continuation case, using a benchmark clone rather than mutating the production
continuation tree. The user requested overnight execution only: start at
2026-06-30 20:00 CDT and enforce a hard cutoff by 2026-07-01 08:00 CDT.

## Source Case

Observed source path:

`jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation`

Relevant observed state:

- OpenFOAM 13 continuation with `foamRun`.
- Mesh note in `constant/polyMesh/owner`: `nCells:2166996`.
- Current decomposition: `numberOfSubdomains 64`, `method scotch`.
- Current `controlDict`: `fileHandler collated`, `writeInterval 1`,
  `purgeWrite 21`, `writeCompression off`.
- Latest retained `processors64` time at setup: `7915`.
- Minimal restart material is small enough for a benchmark clone:
  `constant` about 439 MB, `processors64/constant` about 426 MB, and
  `processors64/7915` about 510 MB.

## Overnight Pilot Plan

Submit one scheduled `NuclearEnergy` batch job:

- partition: `NuclearEnergy`
- account: `ASC23046`
- begin: `2026-06-30T20:00:00`
- walltime: `12:00:00`
- nodes: `1`
- tasks: `256`
- hard cutoff: Slurm walltime should terminate the allocation before 08:00 CDT
  when the job starts on time; the wrapper also has an internal
  `2026-07-01 08:00:00` cutoff guard so a delayed start exits rather than
  running into daytime.

The job will:

1. Source the canonical OpenFOAM 13 environment.
2. Stage a fresh benchmark clone under
   `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/work/`.
3. Copy only `0`, `constant`, `system`, `dynamicCode`, `processors64/constant`,
   and `processors64/7915` from the source tree.
4. Run `reconstructPar -latestTime` once to create a serial restart state.
5. For ranks `32 64 128 256`, create a separate clone, set `scotch`
   decomposition, decompose the latest serial state, and run `foamRun -parallel`
   from `7915` to about `7916`.
6. Write per-rank logs and a `results/scaling_summary.csv` with status,
   start/end timestamps, requested ranks, and final logged `ClockTime` /
   `ExecutionTime` lines.

## Interpretation Boundaries

This first overnight run is a rank-count pilot, not a finished scaling paper.
It should be enough to determine whether the current 64-rank production choice
is obviously over- or under-parallelized for this mesh family. It does not yet
test `hierarchical`, I/O compression, multi-case packing interference, or the
Water cases.

## Next Steps After Completion

1. Check Slurm state and the job stdout/stderr after 08:00 CDT.
2. Inspect `results/scaling_summary.csv`.
3. Parse the per-rank logs for solver iterations, `ClockTime` deltas, timestep
   count, and any decomposition failures.
4. If the 32/64/128/256 scotch pilot is clean, run a second overnight matrix
   comparing `scotch` against one geometry-aligned `hierarchical` split.
5. Promote the final results into a dated report package once at least one
   rank-count matrix and one decomposition comparison are complete.

## Submission Record

The compute-node shell could not submit directly:

`NOTIFICATION: sbatch not available on compute nodes. Use a login node.`

Submission was therefore made through `login3` from the same repo path.

- Slurm job: `3268028`
- Command path:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/scripts/run_salt2_scotch_rank_pilot.sbatch`
- Queue check: `PENDING`, reason `BeginTime`
- Scheduled start: `2026-06-30T20:00:00`
- Scheduled end from Slurm walltime: `2026-07-01T08:00:00`
- Partition: `NuclearEnergy`
- Nodes/tasks: `1` node / `256` tasks
- Stdout:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.out`
- Stderr:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268028.err`

## Handoff For 2026-07-01

No more action is required before the 20:00 CDT scheduled start unless the user
wants to cancel or modify the pilot. The next agent should pick up after the
08:00 CDT cutoff by checking Slurm accounting for job `3268028`, reading the
Slurm stdout/stderr, and parsing
`results/job_3268028/scaling_summary.csv`.

Decision gate:

- If all four rank cases finish, compare walltime and core-hours for
  `32`, `64`, `128`, and `256`.
- If only some ranks finish, report which stage failed or hit timeout and
  whether the available partial data is still useful.
- If the run is clean, schedule the next overnight matrix comparing `scotch`
  against a geometry-aligned `hierarchical` decomposition.

## Planned Follow-Up For 2026-07-01 Overnight

The user asked to schedule the decomposition and I/O optimization run for the
next overnight window. The planned follow-up uses the same Salt 2 Jin restart
clone pattern and is intended to test whether OpenFOAM can run better through
decomposition and output-policy changes, not only rank count.

Scheduled variants:

- `scotch_prod_io`: current-style `scotch`, `writeInterval 1`,
  `writeCompression off`
- `scotch_sparse_io`: `scotch`, `writeInterval 1000`,
  `writeCompression off`
- `scotch_sparse_compressed`: `scotch`, `writeInterval 1000`,
  `writeCompression on`
- `hierarchical_sparse_io`: `hierarchical`, `writeInterval 1000`,
  `writeCompression off`

Default rank count is `64` because that is the current production setting.
Tomorrow morning, after job `3268028` is analyzed, this can still be adjusted
before the scheduled 20:00 CDT start if the first pilot clearly identifies a
better rank count.

Submission record:

- Slurm job: `3268024`
- Queue check: `PENDING`, reason `BeginTime`
- Scheduled start: `2026-07-01T20:00:00`
- Scheduled end from Slurm walltime: `2026-07-02T08:00:00`
- Partition: `NuclearEnergy`
- Nodes/tasks: `1` node / `256` tasks
- Stdout:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268024.out`
- Stderr:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/slurm-3268024.err`
- Expected summary:
  `jadyn_runs/modern_runs/2026-06-30_openfoam_parallel_scaling_study/results/job_3268024/optimization_summary.csv`

## Correction Note

Initial rank-pilot submission `3267856` was canceled before its scheduled
start after the generated `decomposeParDict` header was simplified. The active
rank-pilot job is `3268028`; ignore `3267856` for tomorrow's results.

## 2026-07-01 Postponement

The scaling study was intentionally postponed because the queued jobs did not
start in the intended overnight window and production/ROM work needed the
available capacity.

Observed on `2026-07-01`:

- `3268028` `of_s2_scale` was still pending after the intended
  `2026-06-30 20:00` to `2026-07-01 08:00` window; `squeue --start`
  projected `2026-07-02T09:19:34`.
- `3268024` `of_s2_opt` was still pending for its planned
  `2026-07-01 20:00` start.
- Both jobs were canceled at `2026-07-01T10:29:57-05:00`.
- No production scaling matrix was completed. The `job_3267228` CSVs in
  `results/` are header-only artifacts from an earlier canceled dev allocation
  and must not be used as evidence.

Next attempt should be a new task, not an implied continuation of this one:
wait until the four long production CFD packs and latest-window ROM chain are
clear, then submit a smaller matrix or a confirmed low-priority overnight run.

User follow-up on `2026-07-01`: there was another scaling job that had been
expected to run yesterday. When the scaling study is resumed, first audit the
June 30 / July 1 Slurm history and campaign notes for every intended scaling
submission, not only `3268028` and `3268024`. The recovered plan should include
resubmitting that additional yesterday scaling job or explicitly documenting
why it is superseded. Treat `3267856`, `3268028`, `3268024`, and any other
same-window scaling submission as non-results unless a fresh run completes and
writes a populated summary CSV.
