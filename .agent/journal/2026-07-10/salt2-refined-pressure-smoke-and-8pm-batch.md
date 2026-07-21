# Salt2 Refined Pressure Smoke And 8pm Batch

Task: `AGENT-248`
Date: `2026-07-10`

## Context

AGENT-245 submitted a 9pm repair batch for Salt2 refined closure QoIs, but job
`3287580` failed while reading reconstructed `recon/medium/518/T`. The native
decomposed source `T` field looked plausible at comparable locations, so the
next safe lane was to split pressure-only extraction from thermal diagnosis.

This pass implemented that split. The generated runner avoids
`--dump-temperature` and reconstructs only pressure/mechanical fields:
`p_rgh U rho wallShearStress yPlus`.

## Actions

Generated package:

`work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/`

Added reusable task scripts:

- `tools/analyze/build_salt2_refined_pressure_smoke_and_8pm_batch.py`
- `tools/analyze/test_salt2_refined_pressure_smoke_and_8pm_batch.py`

Validated locally:

```bash
python3.11 -m py_compile tools/analyze/build_salt2_refined_pressure_smoke_and_8pm_batch.py tools/analyze/test_salt2_refined_pressure_smoke_and_8pm_batch.py
python3.11 -c "import tools.analyze.test_salt2_refined_pressure_smoke_and_8pm_batch as t; t.test_generator_contract(); print('manual assertions passed')"
bash -n work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/run_pressure_extraction.sh
bash -n work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/sbatch_pressure_extraction_8pm.sh
```

Ran compute-node checks:

```bash
srun -N1 -n1 -c128 bash work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/run_pressure_extraction.sh preflight
srun -N1 -n1 -c128 bash work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/run_pressure_extraction.sh smoke
```

Submitted batch after smoke passed:

```bash
ssh login3 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/sbatch_pressure_extraction_8pm.sh'
```

Slurm returned job `3288637`. `squeue` showed:

```text
3288637|PENDING|2026-07-10T20:00:00|2026-07-10T12:06:54|0:00|1|(BeginTime)|agent248_salt2_pressure
```

After the user asked to run it immediately on this compute node because the
reuse path was short, the first detached attempt through the sandbox did not
survive; its log was empty. The run was then launched outside the sandbox in a
compute-node `tmux` session:

```bash
tmux new-session -d -s agent248_pressure_now 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && bash work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/scripts/run_pressure_extraction.sh batch > work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/logs/background_20260710T164330-0500_pressure.log 2>&1'
```

The immediate compute-node run completed successfully:

```text
start=2026-07-10T16:43:22-0500
finish=2026-07-10T16:48:08-0500
elapsed=00:04:46
host=c318-008.ls6.tacc.utexas.edu
log=work_products/2026-07/2026-07-10/2026-07-10_salt2_refined_pressure_smoke_and_8pm_batch/logs/background_20260710T164330-0500_pressure.log
```

The run reused reconstructed pressure times for both medium and fine, sampled
`30` rows for each level, and completed friction/momentum reductions. Since the
8pm Slurm job would only duplicate the same pressure-only extraction, job
`3288637` was canceled. `sacct` then reported `CANCELLED+`, elapsed
`00:00:00`, with no node assigned.

## Observed Output

Smoke completed at `2026-07-10T12:06:47-0500` on
`c318-008.ls6.tacc.utexas.edu`.

Medium:

- Source: `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/medium/viscosity_screening_salt_test_2_jin_medium_mesh`
- Time: `518`
- Processor dir: `processors64`
- Sampled sections: `30`, with `5` per required major span.
- `segment_friction.csv`: `13` lines.
- `momentum_budget.csv`: `7` lines.
- Source decomposed `T`: `10,410,605` finite numeric tokens, `0` nonfinite.

Fine:

- Source: `/home1/09748/andresfierro231/bubble_flow_loop/tamu_loop_box/ethan_data/modern_runs/salt/fine/viscosity_screening_salt_test_2_jin_fine_mesh`
- Time: `399`
- Processor dir: `processors128`
- Sampled sections: `30`, with `5` per required major span.
- `segment_friction.csv`: `13` lines.
- `momentum_budget.csv`: `7` lines.
- Source decomposed `T`: `30,225,749` finite numeric tokens, `0` nonfinite.

## Interpretation

The pressure-only extraction path works for Salt2 medium/fine on the current
compute node. This resolves the immediate AGENT-239/245 smoke blocker for
pressure, friction, and streamwise momentum reductions.

This does not resolve thermal closure. The source decomposed `T` diagnostics
support the hypothesis that AGENT-245's failure is tied to reconstructed `T`
output/readback rather than an obviously corrupt native decomposed source file,
but that remains an inference until reconstructed `T` is directly diagnosed and
repaired.

## Caveats

This is not publication-ready mesh-UQ admission. The derived segment-friction
rows include `negative_f_pressure_recovery_or_noise` flags, so a later analysis
must reconcile sign conventions, retained fitting stations, and which spans are
valid closure targets before building GCI rows.

The package did not update registry state, closure-observation tables, or any
native solver output.

## Next Steps

1. Build a pressure-only mesh-family comparison table for Salt2 coarse/medium/fine:
   section means, friction spans, and momentum-budget terms.
2. Review negative/friction-recovery flags before admitting any friction GCI row.
3. Open a separate thermal repair task for reconstructed `T`; do not retry
   thermal extraction in the pressure lane.
