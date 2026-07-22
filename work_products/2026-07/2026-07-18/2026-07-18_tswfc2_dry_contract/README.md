---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/physics_requirement_matrix.csv
  - work_products/2026-07/2026-07-18/2026-07-18_tp_tw_failure_forensics/next_model_contract.csv
  - work_products/2026-07/2026-07-17/2026-07-17_test_section_wall_fluid_coupling_candidate/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_blocker_audit/README.md
tags: [forward-model, wall-fluid-coupling, test-section, dry-contract]
related:
  - .agent/status/2026-07-18_AGENT-541.md
  - .agent/journal/2026-07-18/tswfc2-dry-contract.md
  - imports/2026-07-18_tswfc2_dry_contract.json
task: AGENT-541
date: 2026-07-18
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# TSWFC2 Distributed Wall/Fluid Dry Contract

Generated: `2026-07-18T19:17:56+00:00`

## Decision

This package defines the dry contract for `TSWFC2`, a distributed test-section
wall/fluid node model. It does not implement Fluid behavior or launch a solver.

`TSWFC2` remains secondary while AGENT-540 owns the UMX1 Fluid API unblock. If
UMX1 is unavailable or fails cleanly, this contract is the next wall/test-section
path to review before any Fluid grid.

## Outputs

- `node_geometry_contract.csv`
- `node_heat_ledger_contract.csv`
- `runtime_input_audit_contract.csv`
- `score_gate_contract.csv`
- `distinction_from_tswfc1.csv`
- `next_step_handoff.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Node rows: `4`.
- Heat-ledger rows: `4`.
- Runtime-audit rows: `5`.
- Score-gate rows: `3`.
- TSWFC1 distinction rows: `4`.
- Next-step rows: `4`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, Fluid source,
generated index files, fitting, tuning, model selection, or scientific admission
state were changed. This package explicitly forbids duplicating AGENT-526's
single-node bulk-to-ambient series-resistance model unchanged.
