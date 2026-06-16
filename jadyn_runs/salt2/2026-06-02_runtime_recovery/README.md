# 2026-06-02 salt2 runtime recovery

## Purpose

This folder records the reproducible runtime-recovery path for
`val_salt_test_2_coarse_mesh_laminar` after the container-based continuation
attempts failed to expose a usable `foamRun` command on compute nodes.

## Current interpretation

The blocker was not just `libRCWallBC.so`.

We needed a runnable OpenFOAM environment that provides:

- `foamRun`
- `wmake` and the standard OpenFOAM runtime tree
- compatibility with the imported case's OpenFOAM 13 syntax and dynamic-code
  expectations
- a readable `libRCWallBC.so` path
- an MPI launch path that works on LS6 compute nodes

The case logs show the original source runs used a private tree under:

- `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13`

That means the first-choice recovery path is still to obtain access to that
exact runtime or a faithful copy/build recipe from the coworker who ran the
cases.

## Ask coworker for

1. Read access to `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13`, or a
   copy of that tree into a shared/readable location.
2. The exact bootstrap command used before solver launch, including any module
   loads, environment exports, or shell wrappers.
3. Confirmation whether the original runtime was stock OpenFOAM 13 or a custom
   local build with modifications.
4. Any custom libraries beyond `libRCWallBC.so` that were expected on
   `LD_LIBRARY_PATH` during the original runs.
5. If the original build is reproducible from source, the exact source origin
   and build recipe.

## Download/install ourselves

These are the pieces we can procure independently from the official OpenFOAM
Foundation sources if coworker access is not available:

1. OpenFOAM 13 release source pack.
2. ThirdParty 13 source pack.
3. A local compiled runtime under the current user's `/work` tree.

This does **not** replace the need to compare against the original private
runtime, because a self-built official 13 tree may still differ from the exact
private environment used for the source runs.

## Canonical runtime path

Use this stable path in future submissions and documentation:

- `/work/09748/andresfierro231/ls6/OpenFOAM-13`

That alias currently points to the dated fallback build root:

- `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13`

The dated path remains useful for provenance. The canonical alias may later be
repointed if the coworker provides the exact original private runtime tree and
that runtime is judged preferable.

Current persistent contents under the fallback root:

- source tree: `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/source/`
- source manifest: `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/SOURCE_MANIFEST.json`
- build logs: `/work/09748/andresfierro231/ls6/openfoam_runtime_recovery/2026-06-02_openfoam13/build_logs/`
- repo-side provenance note: `imports/2026-06-02_openfoam13_runtime_source.json`

## Existing readable custom library

The known readable custom boundary-condition library remains:

- `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/libRCWallBC.so`

## Submitted jobs and results

Runtime-recovery history on `2026-06-02`:

- `3202499` build and `3202500` dependent probe: obsolete. First wrapper failed
  because `set -u` made `etc/bashrc` abort on `ZSH_NAME`.
- `3202502` build and `3202503` dependent probe: obsolete. Second wrapper failed
  because `set -e` aborted during OpenFOAM bootstrap before real compilation.
- `3202506` build and `3202507` dependent probe: obsolete. This was the first
  real compile attempt, but it followed the OpenFOAM default `SYSTEMOPENMPI`
  path. On LS6 that later failed in ThirdParty Zoltan configuration because
  `mpi.h` was not found and the MPI test link step could not succeed under the
  assumed system OpenMPI layout.
- `3202515` build and `3202516` dependent probe: successful pair. This build
  switched to `module load intel/24.1 impi/21.12` and sourced OpenFOAM with
  `WM_MPLIB=INTELMPI`. Probe `3202516` confirmed compute-side `foamRun -help`
  and readable `libRCWallBC.so`.

Continuation history:

- `3202687`: first continuation relaunch failed inside the `srun` step because
  `foamRun` was not resolved on the launched ranks and Intel MPI lacked PMI
  wiring.
- `3202708`: corrected continuation relaunch uses the resolved `foamRun` path,
  `srun --mpi=pmi2`, and `I_MPI_PMI_LIBRARY=/usr/lib64/libpmi2.so`. Current
  observed state is successful OpenFOAM startup through `Create mesh for time =
  1724`.

## Ethan shared bootstrap reference

Ethan reported that the original `/work/09807/ethanrozak/ls6/OpenFOAM_V13/OpenFOAM-13`
tree is a standard OpenFOAM 13 install and shared the effective launch order:

1. `source /work/09807/ethanrozak/ls6/OpenFOAM_V13/of13-env.sh`
2. `unset FOAM_SIGFPE`
3. launch the solver

The shared environment semantics were:

- `module purge`
- `module load TACC`
- `module load gcc/13.2.0`
- `module load impi/21.12`
- `export WM_MPLIB=INTELMPI`
- `export MPI_ROOT=${I_MPI_ROOT}`
- `source .../OpenFOAM-13/etc/bashrc`
- `module load python3/3.9.7`
- prepend `/opt/apps/gcc11_2/python3/3.9.7/lib` to `LD_LIBRARY_PATH`

Direct inspection of Ethan's actual `/work/09807/...` tree is still blocked here by
filesystem `Permission denied`, so the local comparison is currently bootstrap-based
rather than file-by-file. The local reusable env script
`jadyn_runs/salt2/2026-06-02_runtime_recovery/scripts/of13-env.sh` mirrors these
semantics against the canonical runtime alias `/work/09748/andresfierro231/ls6/OpenFOAM-13`,
with `python3/3.9.7` treated as optional because that module does not load cleanly
on this account under the same toolchain.

## Login vs compute guidance

- Login node is fine for documentation, inventory, source download, and Slurm
  submission.
- Compute nodes or batch jobs should be used for heavy compilation and for any
  actual `foamRun` validation or continuation attempt.
- Do not treat a successful login-node shell source as proof that the runtime is
  usable on compute nodes.

## Scripts here

- `scripts/download_openfoam13_source_to_work.sh`
- `scripts/compile_openfoam13_from_work.sbatch`
- `scripts/probe_openfoam13_runtime.sbatch`
