---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/logs/run_provenance.env
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/summary.json
tags: [forward-predictive-model, solve-case, slurm, compute-run]
related:
  - .agent/status/2026-07-13_AGENT-301.md
  - .agent/journal/2026-07-13/forward-v0-solve-case-compute-run.md
  - imports/2026-07-13_forward_v0_solve_case_compute_run.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/README.md
task: AGENT-301
date: 2026-07-13
role: Implementer/Tester/Writer
type: work_product
status: active
supersedes: []
superseded_by:
---

# Forward V0 solve_case Compute Run

This AGENT-301 package records submission and initial monitoring for the full
Fluid `solve_case` forward-v0 confirmation prepared by AGENT-293.

## Submission

Direct `sbatch` was unavailable in the current compute-node shell
(`c318-008.ls6.tacc.utexas.edu`), so the job was submitted from login node
`login3`:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch"
```

Slurm returned:

```text
Submitted batch job 3293960
```

## Initial State

- Job ID: `3293960`
- Job name: `fwdv0_solve`
- State at first check: `RUNNING`
- Node: `c318-011`
- Latest state checked in this session: `RUNNING`, elapsed `00:03:18` in
  `sacct` / `3:18` in `squeue`
- Account/partition: `ASC23046` / `NuclearEnergy`
- Walltime request: `06:00:00`
- Resources: `1` node, `1` task, `4` CPUs per task

## Expected Result Package

The running job writes to the prepared AGENT-293 package:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/fast_scan_reference/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_vs_fast_scan_comparison.csv`

By the latest check, `fast_scan_reference/` outputs existed and
`logs/solve_case_full.log` had been created but had no tail output yet.

## Monitor Commands

```bash
ssh login3 "squeue -j 3293960"
ssh login3 "sacct -j 3293960 --format=JobID,JobName,Partition,Account,State,Elapsed,ExitCode,NodeList%20 -X"
tail -40 work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/logs/solve_case_full.log
tail -40 work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/logs/comparison.log
```

## Harvest Criteria

Treat the run as harvested only after:

- Slurm reaches terminal `COMPLETED` with exit code `0:0`.
- `comparison_summary.json` is regenerated after the solve-case output exists.
- `solve_case_full/forward_v0_results.csv` contains six forward-v0 rows.
- `solve_case_vs_fast_scan_comparison.csv` contains row-level deltas for the six
  Salt case/source-variant pairs.

If the job fails or reaches walltime, inspect `logs/solve_case_full.log` before
rerunning. Do not mutate native CFD/OpenFOAM outputs.
