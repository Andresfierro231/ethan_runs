---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/baseline_root_and_qoi_smoke.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/one_at_a_time_setup_uq_smoke.csv
tags: [predictive-1d, setup-uq, terminal-harvest, train-only, no-score]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-TERMINAL-HARVEST-AND-VALIDATOR-2026-07-22.md
  - .agent/journal/2026-07-22/1d-train-only-setup-uq-smoke-terminal-harvest-and-validator.md
  - imports/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator.json
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-TERMINAL-HARVEST-AND-VALIDATOR-2026-07-22
date: 2026-07-22
role: Scheduler Monitor / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# 1D Train-Only Setup-UQ Smoke Terminal Harvest

Decision: `terminal_harvest_complete_train_only_smoke_no_release_no_score`.

Slurm job `3310985` completed with exit code `0:0` in `00:38:40`. The
post-run validator passed. The smoke produced `3` accepted baseline roots and
`33` accepted one-at-a-time setup-legal variant roots.

This is still smoke evidence only. It does not release source/property values,
fit coefficients, score protected rows, freeze a candidate, admit a closure, or
create a final score.

Key result:

- pressure-loss variants gave the largest `mdot` response in this smoke
  (`max |delta mdot| = 0.00106461721522 kg/s`);
- cooler-HX strength gave the largest sensor-projection response
  (`max |delta T| = 38.0198797419 K`);
- residual-owner rows remain diagnostic because all `36` rows report
  `diagnostic_missing_cp`.

Outputs:

- `baseline_terminal_summary.csv`
- `sensitivity_family_summary.csv`
- `decision_gate_terminal.csv`
- `provenance_and_outputs.csv`
- `no_mutation_guardrails.csv`
- `summary.json`
