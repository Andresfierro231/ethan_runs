---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_segment_readiness_ledger.csv
  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_blocker_table.csv
  - work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_shortest_missing_data_path.csv
tags: [forward-predictive-model, fluid-walls, handoff, segment-models]
related:
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - .agent/status/2026-07-16_TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER.md
task: TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER
date: 2026-07-16
role: Coordinator/Forward-pred/Thermal-modeling/Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Tomorrow Handoff: Fluid+Walls Readiness Ledger

## Start Here

Open these files in order:

1. `operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md`
2. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/README.md`
3. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_segment_readiness_ledger.csv`
4. `work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/fluid_walls_shortest_missing_data_path.csv`
5. `.agent/status/2026-07-16_TODO-PREDICT-FLUID-WALLS-READINESS-LEDGER.md`

## What Was Decided

- The current steady-state model-form name is `fluid+walls`.
- The model is steady-state only; do not add wall storage or transient heat-capacity terms to this current target.
- Every segment should carry geometry, material stack, pressure model, thermal circuit, source/sink role, boundary-layer state, recirculation/admission flags, and uncertainty status.
- Realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, and validation temperatures are diagnostic/scoring evidence only, not predictive runtime inputs.

## Current Ledger State

- `lower_leg_heater`: geometry admitted; material partial; pressure diagnostic; thermal diagnostic; source/sink partial; uncertainty partial.
- `left_lower_leg_upcomer`: geometry admitted; pressure/thermal diagnostic; recirculation diagnostic guardrail; ordinary `Nu`, `f_D`, and `K` fits forbidden.
- `test_section_span`: geometry and bare-quartz material admitted; thermal partial; M3+TS candidate not admitted yet.
- `left_upper_leg_upcomer`: geometry admitted; recirculating/effective-lane status blocks ordinary pressure/thermal coefficient fitting.
- `upper_leg_cooler_hx`: geometry admitted; HX/cooler thermal circuit partial; imposed CFD cooler duty remains forbidden at runtime.
- `right_leg_downcomer`: geometry admitted; downcomer Nu/UA fit not admitted because sign/enthalpy, recirculation, GCI, and lit-review gates fail.
- `junction_stub_connector_group`: geometry/material partial; boundary-layer and uncertainty missing; heat/pressure evidence is aggregate diagnostic only.

## Shortest Useful Next Sequence

1. For M3+TS, freeze a runtime-legal setup-only test-section heat-loss candidate.
2. Run the coupled Fluid validation/holdout score for that candidate.
3. Keep the upcomer recirculation guardrail active; do not fit ordinary `Nu`, `f_D`, or `K` to upcomer/test-section rows.
4. Use the ledger for paper/model-form wording now, but state clearly that coefficient claims are not admitted.
5. For paper-ready coefficients, attach same-QOI uncertainty/admission gates by segment after source/sign, recirculation, and GCI blockers are resolved.

## Do Not Do

- Do not use realized CFD `wallHeatFlux`, CFD `mdot`, imposed CFD cooler duty, or validation temperatures as runtime inputs.
- Do not treat pressure maps/ladders as admitted `f_D` or `K` coefficients.
- Do not hide junction/stub heat loss inside a global insulation or Nu correction.
- Do not treat the diagnostic M3/no-test-section baseline as the physical final model.
- Do not mutate native solver outputs or refresh generated repo indexes unless a new board row explicitly claims those paths.

## Exact Commands From This Session

```text
python3 tools/analyze/build_fluid_walls_readiness_ledger.py
python3 -m pytest tools/analyze/test_fluid_walls_readiness_ledger.py
python3 -m json.tool imports/2026-07-16_predict_fluid_walls_readiness_ledger.json
python3 -m json.tool work_products/2026-07/2026-07-16/2026-07-16_predict_fluid_walls_readiness_ledger/summary.json
```

## Validation State

The focused tests pass (`3 passed`). The builder emits `7` segment rows, `7` blocker rows, and `5` shortest-path rows. The generated summary explicitly records no runtime leakage, native-output mutation, registry mutation, or scheduler action.
