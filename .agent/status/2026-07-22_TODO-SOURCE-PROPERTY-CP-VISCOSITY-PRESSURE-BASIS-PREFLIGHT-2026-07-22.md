---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/summary.json
tags: [status, source-property, cp, viscosity, pressure-basis, fail-closed]
related:
  - .agent/journal/2026-07-22/source-property-cp-viscosity-pressure-basis-preflight.md
  - imports/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight.json
task: TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / cfd-pp / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22

## Objective

Preflight the exact source/property basis needed before any release:
`cp_J_kg_K`, viscosity/property mode, pressure basis, setup-known source/sink
inputs, signed heat-path ownership, and runtime-forbidden CFD replay fields.

## Outcome

Published
`work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/`.

Decision: `fail_closed_exact_cp_viscosity_pressure_basis_not_release_ready`.

Release-ready rows remain zero for nominal train, MF13, MF15, MF16, S13
source/property, and pressure/F6 lanes.

## Changes Made

- Added `README.md`.
- Added `source_manifest.csv`.
- Added `field_release_contract.csv`.
- Added `case_qoi_preflight_matrix.csv`.
- Added `pressure_basis_contract.csv`.
- Added `heat_path_lane_separation.csv`.
- Added `runtime_forbidden_replay_audit.csv`.
- Added `next_extraction_queue.csv`.
- Added `summary.json`.
- Updated `.agent/BOARD.md`.
- Added this status note.
- Added `.agent/journal/2026-07-22/source-property-cp-viscosity-pressure-basis-preflight.md`.
- Added `imports/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight.json`.

## Validation

- `python3.11 tools/agent/preflight_task.py --task-id TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22` passed.
- `python3.11 -m json.tool work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/summary.json` passed.
- `python3.11 -c "...csv parse/count..."` parsed 7 CSV files.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight` passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight --strict` passed with `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight` passed.
- `python3.11 -m json.tool imports/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight.json` passed.
- `git -C . diff --check -- <task-owned paths>` passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22` passed.

## Unresolved Blockers

- Exact row-level `cp_J_kg_K` and viscosity/property release remains closed.
- Pressure/F6 basis remains blocked by terminal source, endpoint fields, and
  same-QOI UQ.
- S13 source/property release remains blocked by same-label mesh/GCI and exact
  source/property fields.
- Missing heat residual remains a residual-owner blocker and is not allowed to
  enter internal Nu.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/sampler/harvest/UQ launch, Fluid/external edit, source/property release,
Qwall release, coefficient admission, candidate freeze, protected scoring,
fitting/model selection, blocker-register change, generated-index refresh, or
residual absorption into internal Nu occurred.
