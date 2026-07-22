---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_blocker_research_path_next_step_synthesis/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/next_model_contract.csv
tags: [umx1, scoring-readiness, forward-predictive, upcomer-mixing]
related:
  - .agent/status/2026-07-18_AGENT-543.md
  - .agent/journal/2026-07-18/umx1-scoring-readiness.md
  - imports/2026-07-18_umx1_scoring_readiness.json
task: AGENT-543
date: 2026-07-18
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
supersedes:
  - AGENT-537 hook-existence conclusion
  - AGENT-539 UMX1 blocked-until-hook statement
superseded_by:
---

# UMX1 Scoring Readiness

Task: `AGENT-543`

## Decision

UMX1 is no longer blocked on Fluid API existence. AGENT-540 confirms the current
Fluid checkout has a no-op-default upcomer exchange hook. This package converts
that into a dry scoring-readiness contract and does not run Fluid.

## Outputs

- `case_split_contract.csv`
- `candidate_grid_contract.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `score_gate_contract.csv`
- `probe_localization_contract.csv`
- `next_run_contract.csv`
- `blocker_reconciliation.csv`
- `source_manifest.csv`
- `summary.json`
- `validate_package.py`

## Research Path

The next research step is a separate execution row that creates Fluid scenarios
from the predeclared candidate grid and runs a tiny smoke on compute resources.
Training/model selection is limited to Salt1/Salt2/Salt4 nominal. Salt3 is
holdout. Salt2 +/-5Q and `val_salt2` remain blind score-only after adapters and
release gates exist.

## Guardrails

No Fluid source, native CFD/OpenFOAM output, registry/admission state, scheduler
state, generated docs index, fitting, tuning, model selection, or scientific
admission state was changed. No Fluid solver or scoring grid was launched.
