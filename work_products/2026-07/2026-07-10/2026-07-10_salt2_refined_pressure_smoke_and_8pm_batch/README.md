# Salt2 Refined Pressure Smoke And 8pm Batch

Generated: `2026-07-10T11:54:54-05:00`
Updated: `2026-07-10T16:48:58-0500`

This package is the AGENT-248 pressure-only repair path after AGENT-245 failed
on reconstructed `T`. It deliberately avoids `--dump-temperature`, reconstructs
only `p_rgh U rho wallShearStress yPlus`, extracts section pressure, and keeps
thermal UA/HTC/Nu blocked until the reconstructed-`T` path is diagnosed.

## Current State

Smoke passed on compute host `c318-008.ls6.tacc.utexas.edu` inside the active
allocation. Both Salt2 refined cases completed pressure-only section sampling,
friction reduction, and momentum-budget reduction:

| level | source time | source processor dir | sampled section rows | `segment_friction.csv` | `momentum_budget.csv` | source `T` diagnostic |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| medium | `518` | `processors64` | `30` | `13` lines | `7` lines | `10,410,605` finite numeric tokens, `0` nonfinite |
| fine | `399` | `processors128` | `30` | `13` lines | `7` lines | `30,225,749` finite numeric tokens, `0` nonfinite |

Each case sampled `5` stations in each required span: `lower_leg`,
`right_leg`, `left_lower_leg`, `test_section_span`, `left_upper_leg`, and
`upper_leg`.

At user request, the same pressure-only rerun was executed immediately in a
compute-node `tmux` background session after the smoke evidence showed it would
be short. It completed successfully:

- Session: `agent248_pressure_now`
- Host: `c318-008.ls6.tacc.utexas.edu`
- Log: `logs/background_20260710T164330-0500_pressure.log`
- Start: `2026-07-10T16:43:22-0500`
- Finish: `2026-07-10T16:48:08-0500`
- Elapsed: `00:04:46`

Slurm job `3288637` had been submitted from `login3` for
`2026-07-10T20:00:00`, but it was canceled after the immediate run completed
because it would have duplicated the same pressure-only extraction. `sacct`
reported `CANCELLED+`, elapsed `00:00:00`, with no node assigned.

## Run Smoke Again

```bash
srun -N1 -n1 -c128 bash /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/run_pressure_extraction.sh smoke
```

## Historical 8pm Batch

```bash
ssh login3 'squeue -j 3288637 -o "%i|%T|%S|%V|%M|%D|%R|%j"'
ssh login3 'sacct -j 3288637 --format=JobID,JobName,State,ExitCode,Elapsed,NodeList%30'
```

That job is no longer expected to run. The immediate background run log is the
current rerun evidence:

- `logs/background_20260710T164330-0500_pressure.log`

## Submit 8pm Batch If Requeued

Only submit after smoke passes:

```bash
ssh login3 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/sbatch_pressure_extraction_8pm.sh'
```

## Acceptance Gates

- OF13 ready and used by `foamPostProcess`.
- At least two sampled section rows per major span for medium and fine.
- Non-empty `segment_friction.csv` and `momentum_budget.csv` for medium and fine.
- `t_diagnostic_<level>.json` records source decomposed T as finite/plausible,
  while thermal closure remains blocked.

## Analysis Notes

This is readiness evidence, not publication-ready mesh-UQ evidence yet. The
pressure extraction path works for Salt2 medium/fine, but the derived friction
CSV still contains rows flagged `negative_f_pressure_recovery_or_noise`. Those
rows need sign-convention and retained-station review before closure fitting or
GCI rows are admitted.

Thermal closure remains blocked by AGENT-245: reconstructed `recon/medium/518/T`
failed OpenFOAM parsing even though the source decomposed `T` files scanned here
have finite/plausible numeric tokens. The next thermal task should diagnose
field reconstruction/write quality separately from pressure sampling.
