---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/lower_apparent_k_diagnosis.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/q_ref_orientation_audit.csv
tags: [pressure-ledger, two-tap, recirculation, residual-scorer, lower-apparent-k]
related:
  - .agent/journal/2026-07-20/two-tap-recirc-residual-scorer.md
  - imports/2026-07-20_two_tap_recirc_residual_scorer.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER Status

## Objective

Explain the lower apparent `K` trend in current recirculating
`corner_lower_right` rows and define the next evidence needed for a trustworthy
section-effective residual scorer.

## Outcome

Complete. The package shows the lower static apparent `K` trend is diagnostic:
local dynamic pressure grows strongly from Salt2 to Salt4 while the static
pressure drop changes only modestly and remains hydrostatic/buoyancy dominated.
The package also audits endpoint normal mass flux and marks throughflow `q_ref`
untrusted until a single-leg orientation/masking audit proves the denominator.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER.md`
- `.agent/journal/2026-07-20/two-tap-recirc-residual-scorer.md`
- `imports/2026-07-20_two_tap_recirc_residual_scorer.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/build_two_tap_recirc_residual_scorer.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_residual_scorer/test_two_tap_recirc_residual_scorer.py`
  passed: 5 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-TWO-TAP-RECIRC-RESIDUAL-SCORER`
  passed.

## Unresolved Blockers

- Throughflow `q_ref` remains untrusted until face-level single-leg
  orientation/masking audit passes.
- Same-QOI mesh/time UQ remains missing.
- Current rows remain material-reverse-flow, apparent-cluster-only diagnostics.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
hidden global multiplier, clipped K, model selection, or endpoint-pressure
invention was performed.
