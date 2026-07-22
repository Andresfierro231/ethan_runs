---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [s13, upcomer-exchange, slurm, running]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22.md
task: TODO-S13-UPCOMER-EXCHANGE-MEDIUM-FINE-EXACT-LABEL-SAMPLER-2026-07-22
date: 2026-07-22
role: Scheduler/Monitor handoff
type: operational_note
status: active
---
# RUNNING: S13 Medium/Fine Exact-Label Sampler

Slurm job: `3310179`

Submitted from: `login3`

Submit command:

```bash
ssh login3 sbatch /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch
```

Job script:
`work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/run_medium_fine_exact_label_sampler.sbatch`

Logs:

- `logs/slurm-3310179.out`
- `logs/slurm-3310179.err`

Last observed state:

- `squeue -j 3310179` showed `R` on `c318-019` at approximately
  `2026-07-22 09:59`.
- `ssh c318-019 ps -f -p 410604` confirmed:
  `python3.11 tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py --execute --job-id 3310179`.
- Salt2-medium mask/face CSVs had been written, but final exact-label QOI rows
  were still pending.
- stdout/stderr were empty at the last check.

Duplicate-step note:

- An accidental local `srun` wrapper in allocation step `3307325.2` was killed
  after it was found writing toward the same package path. This did not cancel
  Slurm job `3310179`.
- Salt2-medium mask and face CSVs had been written; exact-label QOI rows had
  not yet been written.

Expected output files:

- `summary.json`
- `source_preflight.csv`
- `mesh_level_geometry_summary.csv`
- `medium_fine_terminal_window_reductions.csv`
- `medium_fine_exact_label_qoi_rows.csv`
- `trusted_wall_Q_wall_detail_rows.csv`
- `sampling_error_log.csv`
- `mesh_gci_readiness_gate.csv`
- `masks/*.csv`
- `faces/*.csv`

Monitor instructions:

1. Check `squeue -j 3310179`.
2. If it leaves the queue, check `sacct -j 3310179`.
3. Read `logs/slurm-3310179.err` and `logs/slurm-3310179.out`.
4. If `summary.json` exists, confirm `exact_label_qoi_rows` and
   `sampling_error_rows`.
5. Do not rerun mesh/GCI disposition from this row. That requires a separate
   post-sampler row after exact-label rows exist.

Forbidden without a new row:

- cancel/requeue unless the job is clearly hung or writing destructive output
- native OpenFOAM mutation
- OpenFOAM `postProcess`
- production harvest
- registry/admission mutation
- coefficient admission
- proxy substitution for exact S13 labels
