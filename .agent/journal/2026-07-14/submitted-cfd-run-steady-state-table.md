---
provenance:
  task: AGENT-343
  owner: codex
  created_at: 2026-07-14T13:52:00-05:00
tags: [journal, cfd-pp, submitted-runs, steady-state, corrected-q]
related:
  - .agent/status/2026-07-14_AGENT-343.md
  - work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/README.md
---
# Submitted CFD Run Steady-State Table

## Question

The coordinator asked for a table of all submitted CFD runs, including continuation runs and perturbed/corrected-Q rows, with a last-window steady-state detection label when such detection has been run. The operational label needed is `steady` or `needs continuation`, with `not run` preserved where no detector output exists.

## Method

Implemented `tools/analyze/build_submitted_cfd_run_steady_state_table.py`.

The script reads submission evidence from:

- `jadyn_runs/modern_runs/2026-06-25_ethan_normal_relaunch_and_recirculation_boundary_wave/submitted_jobs.csv`
- `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/submitted_jobs.csv`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/submitted_jobs.csv`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/selected_submitted_jobs.csv`

It joins detector and admission context from:

- `work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/all_timeseries_case_rollup.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_cfd_steady_state_continuation_table/primary_cfd_continuation_decisions.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_stopped_sbatch_steady_state_decisions/final_window_metrics.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_corrected_q_latest_time_refresh/all_corrected_q_status_table.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_terminal_admission_gate/corrected_q_terminal_gate_rows.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/salt_cfd_candidate_inventory.csv`

Label rule:

- `steady`: explicit final-window or representative time-series detector says steady/quasi-steady without a drifting representative series.
- `needs continuation`: detector found drifting behavior, the selected continuation is still running, the row is under-advanced, or there is no terminal current-run detector.
- `not run`: submitted ledger evidence exists, but no last-window detector output was found.

## Results

Generated package:

- `work_products/2026-07/2026-07-14/2026-07-14_submitted_cfd_run_steady_state_table/`

Summary:

- 50 rows.
- 14 `steady`.
- 33 `needs continuation`.
- 3 `not run`.
- 43 rows with detector output.
- 7 rows without detector output.

Notable rows:

- `salt1_jin_nominal_continuation_corrected`: `steady` by the final 600 s monitor, with terminal/admission context still pending.
- `salt1_jin_lo10q_corrected` and `salt1_jin_hi10q_corrected`: `steady` by final-window flatness, but Salt1 corrected-Q remains policy-constrained for closure fitting.
- `salt2_jin_lo10q_corrected`, `salt2_jin_hi10q_corrected`, `salt4_jin_lo10q_corrected`, and `salt4_jin_hi10q_corrected`: `needs continuation` because the selected continuation rows are running/pending terminal last-window harvest.
- `salt2_jin_lo5q_corrected`, `salt2_jin_hi5q_corrected`, `salt4_jin_lo5q_corrected`, and `salt4_jin_hi5q_corrected`: `needs continuation` because the available detector output still shows heat/total-Q drift.
- `salt4_jin`: `steady` by representative last-window detector.
- `salt2_jin` and `salt3_jin`: `needs continuation` under the conservative full-state label because hydraulic quantities are stationary while heat is still drifting.

## Verification

Passed:

- `python3.11 -m unittest tools.analyze.test_submitted_cfd_run_steady_state_table`
- `python3.11 tools/analyze/build_submitted_cfd_run_steady_state_table.py`

Native CFD solver outputs were not mutated.
