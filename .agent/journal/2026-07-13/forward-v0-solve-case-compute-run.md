---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - .agent/FILE_OWNERSHIP.md
  - .agent/ROLES.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sh
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/summary.json
tags: [forward-predictive-model, solve-case, slurm, compute-run]
related:
  - .agent/status/2026-07-13_AGENT-301.md
  - imports/2026-07-13_forward_v0_solve_case_compute_run.json
  - work_products/2026-07/2026-07-13/2026-07-13_forward_v0_solve_case_compute_run/README.md
  - .agent/journal/2026-07-13/forward-v0-solve-case-confirmation.md
task: AGENT-301
date: 2026-07-13
role: Implementer/Tester/Writer
type: journal
status: active
supersedes: []
superseded_by:
---

# Forward V0 solve_case Compute Run

Date: 2026-07-13

Task ID: AGENT-301

Role: Implementer / Tester / Writer

## Context Read

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
- `.agent/status/2026-07-13_AGENT-293.md`
- `.agent/journal/2026-07-13/forward-v0-solve-case-confirmation.md`
- `imports/2026-07-13_forward_v0_solve_case_confirmation.json`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sh`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch`

## Observed Output

The AGENT-293 package is a no-submit confirmation harness with
`comparison_status=pending_compute_node_run`. Its prepared Slurm script requests
account `ASC23046`, partition `NuclearEnergy`, `1` node, `1` task, `4` CPUs per
task, and walltime `06:00:00`. The shell runner executes fast-scan reference,
full `solve_case`, then the comparison builder, all inside the AGENT-293 result
package.

Direct local submission attempt:

```bash
sbatch work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch
```

The current shell is on compute node `c318-008.ls6.tacc.utexas.edu`; there
`sbatch` resolves to a shell function that prints:

```text
NOTIFICATION: sbatch not available on compute nodes. Use a login node.
```

The normal login-node submission path was therefore used:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch"
```

Slurm accepted the job:

```text
Submitted batch job 3293960
```

Initial scheduler state:

```text
JOBID    PARTITION      NAME         ST  TIME  NODES NODELIST(REASON)
3293960  NuclearEnergy  fwdv0_solve  R   0:09  1     c318-011
```

`sacct` also reported `RUNNING`, elapsed `00:00:09`, exit code `0:0`, node
`c318-011`.

Latest scheduler check in this session still reported `RUNNING` on `c318-011`,
with elapsed `00:03:18` in `sacct` and `3:18` in `squeue`. By then the
`fast_scan_reference/` output files and `logs/solve_case_full.log` existed;
`solve_case_full.log` had no tail output yet.

The run provenance log exists and records:

```text
started_at=2026-07-13T17:21:23-0500 host=c318-011.ls6.tacc.utexas.edu job=3293960
```

## Validation Commands

- `hostname`
- `which sbatch`
- `squeue -u $USER`
- `bash -n work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sh`
- `bash -n work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch`
- `ssh login3 "squeue -j 3293960"`
- `ssh login3 "sacct -j 3293960 --format=JobID,JobName,Partition,Account,State,Elapsed,ExitCode,NodeList%20 -X"`
- Bounded tails of `run_provenance.env`, `fast_scan_reference.log`,
  `slurm_3293960.out`, and `slurm_3293960.err`

## Interpretation

The full solve-case confirmation is now a live compute job, not a login-node
solve. The AGENT-293 package remains the expected result package because the
prepared harness was designed to write `fast_scan_reference/`, `solve_case_full/`,
`comparison_summary.json`, and `solve_case_vs_fast_scan_comparison.csv` there.

No native CFD/OpenFOAM output was mutated. This run uses Fluid only and writes
generated predictive-model artifacts/logs under the prepared work-product path.

## Next Monitor And Harvest Steps

1. Monitor terminal state:

   ```bash
   ssh login3 "squeue -j 3293960"
   ssh login3 "sacct -j 3293960 --format=JobID,JobName,Partition,Account,State,Elapsed,ExitCode,NodeList%20 -X"
   ```

2. If the job is still running, inspect progress without interrupting:

   ```bash
   tail -40 work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/logs/solve_case_full.log
   ```

3. After terminal success, inspect:

   ```bash
   cat work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
   head -20 work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_vs_fast_scan_comparison.csv
   ```

4. Confirm the expected result files exist:

   - `fast_scan_reference/forward_v0_results.csv`
   - `solve_case_full/forward_v0_results.csv`
   - `comparison_summary.json`
   - `solve_case_vs_fast_scan_comparison.csv`

5. If the job times out or fails, preserve logs and inspect
   `logs/solve_case_full.log` before rerunning.
