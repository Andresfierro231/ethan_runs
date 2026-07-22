---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/RUNNING.md
tags: [predictive-1d, setup-uq, bounded-local-smoke, caveat]
related:
  - .agent/status/2026-07-22_TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22.md
task: TODO-1D-TRAIN-ONLY-SETUP-UQ-SMOKE-EXECUTION-2026-07-22
date: 2026-07-22
role: Forward-pred / Uncertainty / Thermal-modeling / Hydraulics / Implementer / Tester / Writer
type: work_product
status: active
---
# Local Bounded Smoke Caveat

This package has an active scheduler-owned execution in Slurm job `3310985`.
During follow-up, a local bounded run was executed with the newer
`--execute --solve-budget 3` interface and wrote baseline-only smoke artifacts
into the same package:

- `baseline_root_and_qoi_smoke.csv`: 3 accepted baseline rows for Salt 2,
  Salt 3, and Salt 4.
- `one_at_a_time_setup_uq_smoke.csv`: 3 post-solve sensor-projection audit rows.
- `unsupported_variant_skip_reasons.csv`: 36 budget-skipped variant rows.
- `summary.json`: decision
  `bounded_train_only_setup_uq_smoke_partial_no_release_no_score`.

These local bounded artifacts are useful for baseline/root viability, but they
are not the canonical terminal result while Slurm job `3310985` remains running.
The terminal harvest row must reconcile the active job outputs, the old
`--run-smoke` provenance, and the newer bounded CLI/test compatibility patch
before closing this execution row.

Guardrails remain unchanged: no native CFD/OpenFOAM output mutation, registry or
admission mutation, source/property release, Qwall release, coefficient
admission, protected scoring, final score, or runtime-leakage relaxation.
