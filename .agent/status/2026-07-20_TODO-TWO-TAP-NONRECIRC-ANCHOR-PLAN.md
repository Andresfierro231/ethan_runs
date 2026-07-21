---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/candidate_anchor_inventory.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/launch_or_no_launch_decision.json
tags: [pressure-ledger, two-tap, nonrecirculating-anchor, component-k]
related:
  - .agent/journal/2026-07-20/two-tap-nonrecirc-anchor-plan.md
  - imports/2026-07-20_two_tap_nonrecirc_anchor_plan.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN Status

## Objective

Choose feasible non-recirculating anchor candidates and define the sampling
contract for future two-tap closure work. No scheduler launch was allowed unless
the row explicitly claimed launch scope; this row remained planning-only.

## Outcome

Complete. The package evaluates both requested lanes:

- `NR-CLR-01`: preferred conditional future lane through same-topology
  `corner_lower_right` sampling from Salt4 high-heat/no-recirculation probes
  after terminal review and preflight.
- `NR-ALT-01`: deferred because no current alternate named component row has
  exact mesh-station labels plus low-reverse ordinary evidence.

Current Salt2/Salt3/Salt4 `corner_lower_right` rows remain diagnostic-only and
are explicitly rejected as ordinary anchors. The launch decision is
`no_launch_from_this_row`.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN.md`
- `.agent/journal/2026-07-20/two-tap-nonrecirc-anchor-plan.md`
- `imports/2026-07-20_two_tap_nonrecirc_anchor_plan.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/build_two_tap_nonrecirc_anchor_plan.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_nonrecirc_anchor_plan/test_two_tap_nonrecirc_anchor_plan.py`
  passed: 6 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-TWO-TAP-NONRECIRC-ANCHOR-PLAN`
  passed.

## Unresolved Blockers

- `two-tap-corner-lower-right-material-reverse-flow`
- `two-tap-corner-lower-right-component-isolation-fails`
- `two-tap-corner-lower-right-same-qoi-uq-missing`

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
hidden global multiplier, clipped K, model selection, or endpoint-pressure
invention was performed.
