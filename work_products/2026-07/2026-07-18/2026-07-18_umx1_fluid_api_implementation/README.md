---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [fluid, umx1, dry-contract, forward-predictive]
related:
  - .agent/status/2026-07-18_AGENT-540.md
  - .agent/journal/2026-07-18/umx1-fluid-api-implementation.md
  - operational_notes/07-26/18/2026-07-18_UMX1_FLUID_API_IMPLEMENTATION.md
task: AGENT-540
date: 2026-07-18
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---

# UMX1 Fluid API Implementation

Task: `AGENT-540`

## Result

Fluid has a real UMX1 upcomer exchange hook in the current working tree. This
task completed the dry API contract around it; it did not run or score a solver
campaign.

## Files

- `implementation_change_log.csv`: scoped Fluid/Ethan changes and guardrails.
- `validation_results.csv`: commands run and known full-suite limitation.
- `runtime_guardrail_audit.csv`: explicit no-run/no-admission checks.
- `next_step_queue.csv`: ordered follow-up tasks before any UMX1 campaign.
- `source_manifest.csv`: input/output provenance.
- `summary.json`: machine-readable contract status.

## API Contract

- Default state: `upcomer_mixing_mode: disabled` and
  `upcomer_exchange_multiplier: 0.0`; exchange is a no-op.
- Active state: `upcomer_mixing_mode: energy_conserving_exchange_v1` with a
  finite nonnegative `upcomer_exchange_multiplier`.
- Scope: `upcomer_exchange_parent_segments` defaults to
  `left_lower_vertical`, `test_section`, and `left_upper_vertical`.
- Setup/provenance rows: `upcomer_reservoir_heat_sources` is parsed as a list of
  mappings. It records source routing intent and is not an admission by itself.
- Ledger: active exchange reports main-to-reservoir heat,
  reservoir-to-main heat, residual, main-stream temperature, reservoir
  temperature, and prediction-stream labels.

## Dry Scoring Boundary

Any future UMX1 scoring row should require these gates before launch:

- candidate multiplier grid declared before looking at validation residuals;
- training and holdout cases declared;
- measured TP/TW, measured mass flow, and measured cooler duty forbidden as
  runtime inputs;
- conservation residual checked before probe scores are interpreted;
- probe errors reported separately for upcomer/test-section sensors and all
  sensors;
- no admission unless the row explicitly changes scientific status.

## Validation

- Focused UMX unit tests: 5 passed.
- Compile check for changed Fluid modules: passed.
- Solver/scoring grid: not run.
