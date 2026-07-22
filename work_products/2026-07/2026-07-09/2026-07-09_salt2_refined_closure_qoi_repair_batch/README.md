# Salt2 Refined Closure-QOI Repair Batch

Generated: `2026-07-09T17:46:43-05:00`

This package is the corrected follow-on to AGENT-239. AGENT-239 reconstructed
medium/fine fields but section sampling produced `no_output` rows and empty
segment-friction tables. This package reruns extraction in fresh staged mirrors
and hard-fails if pressure or thermal cut-plane outputs are missing.

## Submit

```bash
ssh login3 'cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-09/2026-07-09_salt2_refined_closure_qoi_repair_batch/scripts/sbatch_repair_extraction_9pm.sh'
```

The batch is configured to start at `2026-07-09T21:00:00` on `NuclearEnergy`.

Submitted job: `3287580`

Scheduler check immediately after submit:

```text
3287580|PENDING|2026-07-09T21:00:00|2026-07-09T17:46:57|0:00|1|(BeginTime)|agent245_salt2_qoi
```

## Job Result

Job `3287580` failed:

```text
3287580|agent245_salt2_qoi|FAILED|1:0|00:03:05|2026-07-09T21:00:03|2026-07-09T21:03:08|c318-018
```

The hard gate prevented bad closure outputs. Medium section sampling failed
before fine was attempted. `foamPostProcess` ran under OpenFOAM 13, but failed
while reading reconstructed `recon/medium/518/T`:

```text
wrong token type - expected Scalar ... punctuation token '-'
```

The reconstructed serial `T` contains garbage values and `-nan` near the fatal
line, while the decomposed source `processors64/518/T` has normal temperatures.

## Fresh-Agent Continuation

1. Do not use this package's section/friction outputs as closure evidence.
2. Retry pressure-only section sampling without `--dump-temperature`.
3. Diagnose or replace the reconstructed-`T` path before retrying thermal
   closure sampling.
4. Only after real medium/fine pressure rows exist should a new task assemble
   mainline-coarse/medium/fine closure-QOI mesh-UQ tables.
