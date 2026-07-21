---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/blocker_matrix.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/next_step_queue.csv
tags: [pressure-ledger, two-tap, raw-endpoints, blockers, component-k, f6]
related:
  - .agent/journal/2026-07-18/two-tap-blocker-roadmap.md
  - imports/2026-07-18_two_tap_blocker_roadmap.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/README.md
task: TODO-TWO-TAP-BLOCKER-ROADMAP
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-BLOCKER-ROADMAP Status

## Objective

Implement the blocker, research-path, and next-step roadmap for the completed
`corner_lower_right` raw endpoint contract.

## Outcome

Complete. The roadmap package emits:

- 7 blocker/gate rows covering task scope, target taps, pressure/velocity basis,
  straight-reference/component isolation, recirculation metrics, same-QOI UQ,
  and F6 separation.
- 6 research paths from staged-copy raw sampling through admission governance.
- 7 ordered next steps, with the staged-copy cfd-pp row as the first executable
  follow-on.
- 7 admission decision rules that forbid endpoint inference, K clipping,
  unrelated GCI reuse, F6 fitting from this thread, and automatic component-K
  admission.

## Changes Made

- `tools/analyze/build_two_tap_blocker_roadmap.py`
- `tools/analyze/test_two_tap_blocker_roadmap.py`
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/**`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `.agent/BOARD.md`
- `.agent/status/2026-07-18_TODO-TWO-TAP-BLOCKER-ROADMAP.md`
- `.agent/journal/2026-07-18/two-tap-blocker-roadmap.md`
- `imports/2026-07-18_two_tap_blocker_roadmap.json`

## Validation

- `python3.11 -m unittest tools.analyze.test_two_tap_blocker_roadmap`
  - Result: pass, 5 tests.
- `python3.11 tools/analyze/build_two_tap_blocker_roadmap.py`
  - Result: pass, generated 7 blocker rows, 6 research paths, 7 next steps,
    7 admission rules, and 0 admissions.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: none.
- Solver/postprocessing launch: none.
- External Fluid edit: no.
- Generated docs index refresh: not run; active/generated-index ownership is
  outside this task.
- Scientific admission change: none.
- F6/component-K status: no F6 fit and no component-K admission.

## Remaining Work

Claim a separate staged-copy cfd-pp row before sampling endpoint surfaces. The
sampler must preserve `lower_leg__s04` to `right_leg__s00` at `7915/7618/10000`
and write only into task-owned `tmp/` or `work_products/`.
