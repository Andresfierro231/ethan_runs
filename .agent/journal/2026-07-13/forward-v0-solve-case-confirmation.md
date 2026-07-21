# Forward V0 solve_case Confirmation

Date: 2026-07-13

Agent role: Implementer / Tester / Writer

Task ID: AGENT-293

Branch or worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `tools/analyze/run_predictive_forward_v0_imposed_cooler.py`
- `tools/analyze/test_predictive_forward_v0_imposed_cooler.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md`
- `.agent/status/2026-07-13_TODO-PRED-FORWARD-V0.md`
- `.agent/journal/2026-07-13/predictive-forward-v0-imposed-cooler.md`

## Files Changed

- `.agent/BOARD.md`
- `.agent/status/2026-07-13_AGENT-293.md`
- `.agent/journal/2026-07-13/forward-v0-solve-case-confirmation.md`
- `imports/2026-07-13_forward_v0_solve_case_confirmation.json`
- `tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py`
- `tools/analyze/test_predictive_forward_v0_solve_case_confirmation.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/**`

## Observations

The completed forward-v0 package already supports `--engine solve_case`, but its
default output path belongs to completed `TODO-PRED-FORWARD-V0`. The safe
follow-on path is therefore a separate AGENT-293 package that reruns both
`fast_scan` and `solve_case` into disjoint subdirectories and compares only
their generated CSV outputs.

The full `solve_case` path remains compute-node work. This task did not run it
on the login node and did not submit a scheduler job.

## Commands Run

- `python3 tools/analyze/test_predictive_forward_v0_solve_case_confirmation.py`
- `python3 tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py`
- `bash -n work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sh`
- `bash -n work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch`

## Results

Focused tests passed. The package now contains:

- `README.md`
- `summary.json`
- `expected_outputs.csv`
- `comparison_metric_contract.csv`
- `solve_case_vs_fast_scan_comparison.csv` with pending headers
- `comparison_summary.json` with `overall_status=pending_compute_node_run`
- `scripts/run_forward_v0_solve_case_confirmation.sh`
- `scripts/run_forward_v0_solve_case_confirmation.sbatch`
- `logs/` pre-created for Slurm output files

## Incomplete Lines Of Investigation

The actual full Fluid `solve_case` rows are not yet produced. A future compute
node run should execute the prepared Slurm or shell runner, then inspect
`comparison_summary.json` and `solve_case_vs_fast_scan_comparison.csv`.

## Next Steps

1. Submit or run the prepared script only from a compute-node workflow.
2. Confirm all six solve_case rows are present and accepted for validation.
3. Use solve_case rows as authoritative for thesis-grade forward-v0 claims.
4. Treat fast_scan as a proxy only if mdot, Tmean, loop-delta, and heat-ledger
   deltas remain inside `comparison_metric_contract.csv` bands.
