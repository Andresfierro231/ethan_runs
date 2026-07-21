# Forward Predictive Model Research Plan

Task: `AGENT-286`
Date: 2026-07-13
Role: Coordinator / Writer

## Context

The user asked whether the current model can predict mass flow and sensor
temperatures from heater and cooling rates, then asked for thorough
documentation, blockers, next steps, and tasks to make the path work end to
end.

## Work Performed

Created:

`work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/`

with:

- `README.md`
- `research_plan.md`
- `input_readiness_matrix.csv`
- `blocker_register.csv`
- `task_backlog.csv`

Also added:

- `operational_notes/07-26/13/2026-07-13_forward_predictive_model_research_plan.md`
- `imports/2026-07-13_forward_predictive_model_research_plan.json`
- board row `AGENT-286`
- unclaimed board rows `TODO-PRED-*`

## Interpretation

The forward problem is not blocked by lack of a solver skeleton. Fluid already
has geometry, properties, pressure closure, thermal marching, cooler modes, and
sensor-output machinery. The blockers are scientific/modeling gates:

- cooler/HX duty is first-order,
- heater input does not equal heat transferred to fluid,
- test-section heat is a source-plus-loss problem,
- CFD external h acts on wall/near-wall state rather than 1D bulk temperature,
- radiation is inseparable in current `rcExternalTemperature` outputs,
- thermal fit rows fail mesh/time/recirculation gates,
- sensor locations and local temperature claims are still downstream of energy
  parity.

## Proposed Model Sequence

Start with imposed-cooler forward-v0:

```text
physical setup + heater input + imposed cooler duty
  -> solve mdot
  -> solve loop temperature state
  -> emit TP/TW predictions
  -> compare validation targets after solve
```

Then replace imposed cooler duty with a predictive HX model after mdot/source
and wall-layer contracts are controlled.

## Board Tasks Added

- `TODO-PRED-INPUT-CONTRACT`
- `TODO-PRED-FORWARD-V0`
- `TODO-PRED-HX-FIT`
- `TODO-PRED-HEATER-TEST-CONTRACT`
- `TODO-PRED-WALL-LAYER`
- `TODO-PRED-HYDRAULIC-GATE`
- `TODO-PRED-THERMAL-MESH-GATE`
- `TODO-PRED-SENSOR-MAP`
- `TODO-PRED-VALIDATION-SPLIT`
- `TODO-PRED-ENDTOEND-SCORE`

## Validation

- Parsed CSV files with Python `csv.DictReader`.
- Validated import JSON with `python -m json.tool`.
- Searched board/package references with `rg`.

No solver outputs, Fluid source files, registry rows, scheduler state, or
admission decisions were modified.
