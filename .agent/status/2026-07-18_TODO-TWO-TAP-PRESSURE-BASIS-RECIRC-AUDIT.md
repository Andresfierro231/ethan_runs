---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/endpoint_recirculation_metrics.csv
tags: [pressure-ledger, two-tap, raw-endpoints, recirculation]
related:
  - .agent/journal/2026-07-18/two-tap-pressure-basis-recirc-audit.md
  - imports/2026-07-18_two_tap_pressure_basis_recirc_audit.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT
date: 2026-07-18
role: Hydraulics/Tester/Implementer/Writer
type: status
status: complete
---
# TODO-TWO-TAP-PRESSURE-BASIS-RECIRC-AUDIT Status

## Objective

Consume the six harvested `corner_lower_right` raw endpoint rows and audit the
pressure/velocity basis plus same-window recirculation gates without fitting F6
or admitting component K.

## Outcome

Complete. The audit produced three paired Salt2/Salt3/Salt4 feature rows with
finite static pressure, `p_rgh`, hydrostatic correction, kinetic correction,
local density, bulk velocity, local dynamic pressure, and diagnostic
`K_apparent` basis terms.

All three pairs fail the ordinary recirculation gate. Aggregate RAF is about
`0.763` and aggregate RMF is about `0.500`, far above the `<0.01` ordinary
threshold. The gate decision table therefore keeps all rows
`diagnostic_only_recirculation_blocked`, with zero ordinary component-K
candidates.

## Changes Made

- Added `tools/analyze/build_two_tap_pressure_basis_recirc_audit.py`.
- Added `tools/analyze/test_two_tap_pressure_basis_recirc_audit.py`.
- Created
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/**`.
- Added blocker
  `two-tap-corner-lower-right-material-reverse-flow` to `.agent/blockers.yml`.
- Updated `operational_notes/maps/pressure-and-momentum-budget.md`.

## Validation

- `python3.11 tools/analyze/build_two_tap_pressure_basis_recirc_audit.py`
  passed.
- `python3.11 -m unittest tools.analyze.test_two_tap_pressure_basis_recirc_audit`
  passed: 5 tests.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker
  register OK with 13 entries. Generated index files were not refreshed.

## Unresolved Blockers

- `two-tap-corner-lower-right-material-reverse-flow` is open.
- Component isolation and same-QOI uncertainty remain unaudited downstream
  tasks.
- F6 governance remains separate; these material-reverse-flow rows are not
  ordinary F6 anchors.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. Generated docs index files were not refreshed. No F6 fit,
component-K admission, model selection, or endpoint-pressure invention was
performed.
