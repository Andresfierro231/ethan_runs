---
provenance:
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
  - /scratch/09748/andresfierro231/projects_scratch/ethan_runs/work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_runbook/README.md
tags: [journal, predictive-1d, setup-uq, smoke-execution]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22.md
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: journal
status: complete
---
# 1D Train-Only Setup-UQ Smoke Execution

## Attempted

Read the setup-UQ runbook, confirmed Fluid `solve_case` availability, froze a
runtime manifest, ran a bounded local train-only baseline smoke, and wrote a
no-release addendum package. The canonical Slurm execution, job `3310985`, later
completed and was reconciled by the terminal-harvest row.

## Observed

The Fluid API is callable in read-only mode but each salt solve is slow enough
that a broad full grid belongs on a compute node. The local bounded run completed
three accepted baseline rows and three post-solve sensor-projection audit rows,
then marked 36 variant rows as budget-skipped. Slurm job `3310985` completed
`COMPLETED 0:0`; its terminal harvest reports `3/3` accepted baseline roots and
`33/33` accepted one-at-a-time variant roots.

## Inferred

The setup-UQ pathway is executable and complete as a smoke-only execution. It
does not unlock admission, protected scoring, or candidate freeze. The completed
Slurm outputs supersede the local bounded addendum for full-matrix
interpretation.

## Next Useful Actions

Use the terminal-harvest package to design a follow-on train-only review row
that compares pressure-loss, external-convection, cooler-HX, and heater-source
placement families against residual-owner and source/property gates. Keep
source/property, Qwall, protected scoring, and candidate freeze in separate
explicitly claimed rows.
