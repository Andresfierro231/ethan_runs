---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [fluid, umx1, upcomer-mixing, start-here]
related:
  - .agent/status/2026-07-18_AGENT-540.md
  - .agent/journal/2026-07-18/umx1-fluid-api-implementation.md
task: AGENT-540
date: 2026-07-18
role: Implementer/Tester/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---

# UMX1 Fluid API Implementation Start Here

Task: `AGENT-540`

## Why This Exists

AGENT-537 reported that UMX1 should stop at a no-solver API contract if Fluid
lacked a real upcomer mixing/stratification hook. The current Fluid working tree
does have such a hook, so AGENT-540 completed the dry API and test contract
without running a solver/scoring grid.

## Open First

- `work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`

## Trusted Contract

The accepted dry contract is:

- default disabled UMX is no-op;
- invalid UMX modes and unknown parent segments are rejected by the validator;
- positive exchange is finite and conservative at the helper/ledger level;
- a marched segment state emits finite UMX ledger and stream metadata;
- config loader and scenario-record output carry the UMX fields;
- no Fluid scoring/admission has occurred.

## Remaining Blockers

UMX1 scoring still needs a new explicit row. That row should define the candidate
grid, train/holdout split, setup-only reservoir/source provenance, probe metrics,
and admission threshold before any run.

## Next Task Sequence

1. Open `operational_notes/07-26/18/2026-07-18_UMX1_SCORING_READINESS.md`
   and `work_products/2026-07/2026-07-18/2026-07-18_umx1_scoring_readiness/README.md`
   for the AGENT-543 split-legal dry scoring contract.
2. Decide whether UMX1 should be scored independently or together with the
   TSWFC2 distributed wall/fluid contract.
3. Run only after a later execution row explicitly allows a Fluid campaign and names
   the output root.

## Do Not Do

- Do not use measured TP/TW, measured mass flow, or measured cooler duty as
  runtime inputs.
- Do not run a Fluid scoring grid under AGENT-540.
- Do not mutate native CFD/OpenFOAM outputs or registry/admission state.
- Do not treat the API hook as a scientific admission.
