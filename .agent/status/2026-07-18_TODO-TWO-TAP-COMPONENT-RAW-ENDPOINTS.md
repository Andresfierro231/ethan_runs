---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/target_feature_taps.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/launch_readiness_gate.csv
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/journal/2026-07-18/two-tap-component-raw-endpoints.md
  - imports/2026-07-18_two_tap_component_raw_endpoints.json
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/README.md
task: TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS Status

## Objective

Convert the AGENT-530 `corner_lower_right` repair queue into exact raw
pressure/velocity/recirculation/UQ sampling requirements.

## Outcome

Complete. The new package emits a raw endpoint sampling contract for Salt2,
Salt3, and Salt4 `corner_lower_right` rows:

- upstream endpoint: `lower_leg__s04` /
  `ncc_pipeleg_lower_09_fitting_end`
- downstream endpoint: `right_leg__s00` /
  `ncc_pipeleg_right_01_lower_start`
- time windows: Salt2 `7915`, Salt3 `7618`, Salt4 `10000`
- required endpoint fields: `p`, `p_rgh`, `U`, `T_or_rho`, flux/area/normal
  data
- required gates: pressure/velocity basis, hydrostatic and kinetic correction
  separation, straight-reference/component isolation, same-window RAF/RMF/SVF,
  same-QOI mesh/time UQ, and F6/component-K separation

This is a contract only. It admits no coefficient and launches no sampling job.

## Changes Made

- `tools/analyze/build_two_tap_component_raw_endpoint_plan.py`
- `tools/analyze/test_two_tap_component_raw_endpoint_plan.py`
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/**`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `.agent/BOARD.md`
- `.agent/status/2026-07-18_TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS.md`
- `.agent/journal/2026-07-18/two-tap-component-raw-endpoints.md`
- `imports/2026-07-18_two_tap_component_raw_endpoints.json`

## Validation

- `python3.11 -m unittest tools.analyze.test_two_tap_component_raw_endpoint_plan`
  - Result: pass, 6 tests.
- `python3.11 tools/analyze/build_two_tap_component_raw_endpoint_plan.py`
  - Result: pass, generated 3 target rows, 6 endpoint surface rows, 8 basis
    field rows, 3 recirculation rows, 3 same-QOI uncertainty rows, and 7 launch
    gates.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: none.
- Solver/postprocessing launch: none.
- External Fluid edit: no.
- Generated docs index refresh: not run; active AGENT-536 owns generated index
  paths.
- Scientific admission change: none.
- F6/component-K status: no F6 fit and no component-K admission. Negative
  current `K_local` remains a blocker, not a value to clip.

## Remaining Work

A separate staged-copy postprocessing task can now implement the contract. It
must write under task-owned `tmp/` or `work_products/`, keep native source cases
read-only, and then feed a new extractor/admission package rather than
overwriting AGENT-530 or this plan.
