---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/blocker_unlock_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/future_sampler_contract.csv
tags: [pressure-ledger, two-tap, f6, blocker-unlock, same-qoi-uq]
related:
  - .agent/journal/2026-07-20/pressure-f6-two-tap-blocker-unlock-next-steps.md
  - imports/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS Status

## Objective

Turn the current pressure/F6/two-tap blocker state into implementation-ready
next-step contracts without fitting F6, admitting component K, launching
scheduler work, or mutating CFD/native outputs.

## Outcome

Complete. The package records the unlock path as two separate lanes:
ordinary-flow `CAND-001` anchor evidence for future component-K review, and a
recirculating section-effective pressure-residual lane for the current lower
apparent-K rows. The active pressure/F6/two-tap blockers remain open because the
current `corner_lower_right` evidence still has material reverse flow,
apparent/cluster component isolation, and missing same-QOI mesh/time UQ.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS.md`
- `.agent/journal/2026-07-20/pressure-f6-two-tap-blocker-unlock-next-steps.md`
- `imports/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/build_pressure_f6_two_tap_blocker_unlock_next_steps.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_pressure_f6_two_tap_blocker_unlock_next_steps/test_pressure_f6_two_tap_blocker_unlock_next_steps.py`
  passed: 6 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-PRESSURE-F6-TWO-TAP-BLOCKER-UNLOCK-NEXT-STEPS`
  passed.

## Remaining Blockers

- Current face-level `q_ref` rows remain rejected for material reverse flow.
- `CAND-001` source cases remain terminal-readiness gated in existing monitor
  evidence.
- Component K remains blocked until a low-reverse same-topology sample also
  passes component-isolation review.
- Same-QOI UQ remains missing until a same-label/same-formula/same-sign
  mesh/time family lands.
- F6 remains blocked until ordinary-anchor evidence or a separately scored
  recirculation-modeled pressure closure is available.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
ordinary-K promotion, hidden global multiplier, clipped K, model selection,
blocker-register mutation, or endpoint-pressure invention was performed.
