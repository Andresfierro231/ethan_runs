# Forward V0 solve_case Confirmation

Generated: `2026-07-13T22:28:41+00:00`

Task: `AGENT-293`

## Why This Exists

The completed forward-v0 imposed-cooler package used `--engine fast_scan`
because Fluid's full nested `solve_case` path was too slow interactively. This
package prepares the full confirmation path for a compute node without
submitting a job from the login session.

## Open First

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/README.md`
- `tools/analyze/run_predictive_forward_v0_imposed_cooler.py`
- `tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py`

## Exact Commands

Login-node smoke, plan regeneration only:

```bash
python3 tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py
```

Compute-node full confirmation command:

```bash
bash work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sh
```

Prepared Slurm command, not submitted by this package:

```bash
sbatch work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/scripts/run_forward_v0_solve_case_confirmation.sbatch
```

The shell runner executes:

```bash
python3 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/run_predictive_forward_v0_imposed_cooler.py --output-dir /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/fast_scan_reference --strict-input-contract --sensor-source both --engine fast_scan
python3 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/run_predictive_forward_v0_imposed_cooler.py --output-dir /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full --strict-input-contract --sensor-source both --engine solve_case
python3 /scratch/09748/andresfierro231/projects_scratch/ethan_runs/tools/analyze/build_predictive_forward_v0_solve_case_confirmation.py --package-dir /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation --compare
```

## Compute-Node Requirements

- Run on a compute node, not a login node.
- Slurm template: account `ASC23046`, partition `NuclearEnergy`, `1` node,
  `1` task, `4` CPUs per task, walltime `06:00:00`.
- Expected workload: six forward-v0 rows (`3` Salt cases x `2` source variants)
  using Fluid only; no OpenFOAM solver output is read or mutated.
- If `06:00:00` expires, preserve logs and rerun only after inspecting
  `logs/solve_case_full.log`.

## Expected Output Package

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/fast_scan_reference/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_vs_fast_scan_comparison.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json`

## Comparison Metrics

See `comparison_metric_contract.csv`. The core row-level metrics are mdot,
pressure residual, temperature periodicity error, model Tmean proxy, loop delta
proxy, ambient heat loss, cooler heat, root status, and validation acceptance.
Full `solve_case` rows are authoritative. `fast_scan` is thesis-grade only as a
proxy where deltas remain inside the documented bands.

## Current Status

`pass`. No scheduler job was submitted by this
package builder.

## Guardrails

- Do not run the full `--engine solve_case` matrix on a login node.
- Do not edit the completed `TODO-PRED-FORWARD-V0` package.
- Do not mutate native CFD/OpenFOAM outputs.
- Do not treat imposed cooler duty as predictive HX closure.
