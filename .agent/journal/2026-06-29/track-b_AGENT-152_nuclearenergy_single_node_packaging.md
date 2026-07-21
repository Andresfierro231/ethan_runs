# AGENT-152 Raw Notes

Date: `2026-06-29`
Role: `Coordinator / Implementer / Writer`

## Observed Output

- `squeue` showed the long `NuclearEnergy` jobs `3261320`, `3261321`, `3261322`, and `3261323` each running as `2`-node jobs.
- `sacct` showed each long job contains four `foamRun` job steps with `64` CPUs each.
- `scontrol show step` confirmed the live step placement is not reliably balanced across the two allocated nodes:
  - `3261320`: steps `.2` and `.3` running on `c318-012`; completed steps `.0` and `.1` no longer queryable
  - `3261321`: steps `.0`, `.2`, and `.3` running on `c318-014`; completed step `.1` no longer queryable
  - `3261322`: steps `.0`, `.2`, and `.3` running on `c318-019`; step `.1` running on `c318-020`
  - `3261323`: steps `.0`, `.2`, and `.3` running on `c318-017`; step `.1` running on `c318-018`
- The live launcher is `tmp/2026-06-26_nuclearenergy_repack_followon/run_packed_four_case_nuclear.sbatch`.
- That launcher requested `#SBATCH -N 2` and `#SBATCH -n 256`, while each case launch already uses `srun --nodes=1 --ntasks=64`.

## Inferred Interpretation

- The packing mistake is at the Slurm allocation layer, not the per-case `srun` step layer.
- A single `NuclearEnergy` node appears to expose `256` CPUs, so four `64`-rank CFD runs can fit on one node if the batch allocation is constrained to `1` node.
- Leaving the batch allocation at `2` nodes wastes node capacity and does not guarantee a clean `2 + 2` per-node split anyway.

## Contradictions / Caveats

- Editing the launcher does not change the already running jobs `3261320-3261323`; live correction still requires cancel/resubmit.
- Completed steps do not remain queryable through `scontrol show step`, so for `3261320` and `3261321` the earlier node placement of finished steps is no longer directly visible.

## Actions Taken

- Claimed `AGENT-152` for the launcher fix and documentation.
- Changed `run_packed_four_case_nuclear.sbatch` from `#SBATCH -N 2` to `#SBATCH -N 1`.
- Added a queue-policy note stating that `NuclearEnergy` submissions should default to one node unless explicitly justified otherwise.
- Canceled the live mispacked jobs `3261320`, `3261321`, `3261322`, and `3261323`.
- Reconstructed the original case-group exports from the existing Slurm `.out` files and resubmitted the same four groups through `login3` because `sbatch` is not available from the compute node.
- New single-node job IDs:
  - `3265972` replaces `3261320` for `ethan_s123hi_ne5d`
  - `3265971` replaces `3261321` for `ethan_s41lo2mid_ne5d`
  - `3265969` replaces `3261322` for `ethan_s34mid_ne5d`
  - `3265970` replaces `3261323` for `ethan_w1234_ne5d`
- Verified with `squeue` and `scontrol show job` that each replacement is `RUNNING` on `1` node with `256` CPUs.

## Suggested Next Actions

- If the live jobs are left alone, use the corrected launcher as the default for the next repack or continuation submission.
- For any future packed-job audit, verify both `NumNodes=1` and the per-step `NodeList` rather than assuming the allocation shape guarantees correct packing.
