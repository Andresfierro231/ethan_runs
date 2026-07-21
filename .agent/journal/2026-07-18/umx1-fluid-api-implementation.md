---
provenance:
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/config_loader.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_solver_contracts.py
tags: [fluid, umx1, upcomer-mixing, api-contract, testing]
related:
  - .agent/status/2026-07-18_AGENT-540.md
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_fluid_api_implementation/README.md
  - operational_notes/07-26/18/2026-07-18_UMX1_FLUID_API_IMPLEMENTATION.md
task: AGENT-540
date: 2026-07-18
role: Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---

# UMX1 Fluid API Implementation Journal

Task: `AGENT-540`

## Observed

Fluid was not in the no-hook state reported by the earlier read-only audit.
The current working checkout already had UMX1 solver-side fields and helpers:
`DEFAULT_UPCOMER_EXCHANGE_PARENT_SEGMENTS`, `ScenarioConfig` UMX fields,
`SegmentState` ledger fields, sensor provenance stream metadata, the
`_validate_upcomer_exchange_contract` validator, and `_upcomer_exchange_heat_W`.

The remaining gap was contract hardening: config defaults needed to be tied to
the solver constant, tests needed to validate the hook without launching a solve,
and documentation needed to say what is and is not admitted.

## Attempted

I kept the existing solver exchange implementation in place and changed only the
loader/test/doc surface. The focused tests now cover:

- YAML loading and `scenario_records` round-trip for UMX fields.
- Rejection of unsupported `upcomer_mixing_mode`.
- Rejection of unknown `upcomer_exchange_parent_segments`.
- Finite positive exchange for an active segment.
- Direct marched `SegmentState` ledger output for an active UMX segment.
- Conservative diagnostic ledger semantics, `Q_main_to_reservoir +
  Q_reservoir_to_main = 0`.
- Default disabled no-op exchange.

## Inferred

Fluid now has a real UMX1 API hook in the working tree. It is not an admitted
predictive closure yet. The right next move is a separate dry scoring row that
declares allowed inputs, training/holdout split, candidate multiplier grid, and
acceptance metrics before any campaign run.

## Contradictions And Caveats

- `python3.11 tools/agent/preflight_task.py --task-id AGENT-540` reported a
  broad overlap with `TODO-FLUID-EXTERNAL-BC-DICT`. That older row explicitly
  allows Fluid API edits after a later row claims external
  `../cfd-modeling-tools/**`; AGENT-540 made that explicit claim.
- The external Fluid repo had other dirty files before this pass. This task did
  not revert or normalize unrelated work.
- No Fluid campaign, scoring grid, or full solver sweep was run.

## Next Useful Actions

- Define a UMX1 scoring plan in a new board row, not under AGENT-540.
- Require setup-only reservoir/source rows and forbid measured TP/TW,
  measured mass flow, or measured cooler duty as runtime inputs.
- Score conservation and probe residuals separately, with a holdout split, before
  any admission decision.
