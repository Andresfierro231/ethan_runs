---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/scripts/run_train_only_setup_uq_smoke.sbatch
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/runtime_input_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/scenario_matrix.csv
tags: [predictive-1d, setup-uq, train-only, running, slurm]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22.md
  - .agent/journal/2026-07-22/1d-train-only-setup-uq-smoke-execution.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_execution.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: active
---
# Running Handoff

Task: `TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22`

Slurm job: `3310985`

Initial scheduler state: `RUNNING` on `c318-011` at `2026-07-22 11:02 CDT`.

Follow-up observation at approximately `2026-07-22 11:09 CDT`: Slurm job
`3310985` was still `RUNNING`; the active process on `c318-011` was
`python3.11 tools/analyze/build_1d_train_only_setup_uq_smoke_execution.py
--output-dir ... --run-smoke` at near-full CPU. The `run_smoke.log`,
`slurm_3310985.out`, and `slurm_3310985.err` files were still empty, which is
consistent with buffered output while the Fluid solve loop is active.

Important provenance caveat: the live Slurm process loaded the earlier
full-matrix execution builder that accepted `--output-dir` and `--run-smoke`.
The builder file currently visible on disk has since changed to a bounded
`--execute/--solve-budget` interface. Do not infer the behavior of job
`3310985` from the later on-disk CLI alone. Interpret the terminal outputs and
logs from the job-owned package first, then reconcile the script version in the
closeout status.

Submit command:

```bash
ssh login3 "cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs && sbatch work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/scripts/run_train_only_setup_uq_smoke.sbatch"
```

Task-owned logs:

- `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs/slurm_3310985.out`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs/slurm_3310985.err`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs/run_smoke.log`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs/test_after_smoke.log`
- `work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/logs/run_provenance.env`

Expected terminal outputs after success:

- `baseline_root_and_qoi_smoke.csv`
- `one_at_a_time_setup_uq_smoke.csv`
- `segment_heat_ledger.csv`
- `sensor_projection_predictions.csv`
- `mdot_heat_sensitivity.csv`
- `sensor_projection_sensitivity.csv`
- `residual_owner_sensitivity.csv`
- `unsupported_variant_skip_reason.csv`
- `decision_gate.csv`
- refreshed `summary.json` and `README.md`

Stop/report conditions:

- Report if job `3310985` enters `FAILED`, `CANCELLED`, `TIMEOUT`, or any other terminal non-success state.
- If the job finishes successfully but the post-run validator fails only on the
  later `tools` import-path issue, treat the CSV/JSON science artifacts as
  harvestable but require a validator repair before closeout.
- If `baseline_root_and_qoi_smoke.csv` exists with any non-accepted baseline root, do not interpret missing variant rows as a code failure; the runbook says to stop before variants.
- Do not submit a duplicate job without a new board row.
- Do not cancel or requeue without a new board row or explicit user instruction.
- Do not treat outputs as source/property release, final score, coefficient admission, or protected-row scoring.
