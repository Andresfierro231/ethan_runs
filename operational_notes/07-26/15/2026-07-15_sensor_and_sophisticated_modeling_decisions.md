---
task: AGENT-432
date: 2026-07-15
role: Coordinator/Writer
type: operational_note
status: complete
tags: [sensor-map, forward-model, upcomer, boundary-layer, scorecard]
related:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/sensor_map_policy_refresh.csv
---
# Sensor and Sophisticated Modeling Decisions

## Why this note exists

The forward-model story needs two fixes before the next scorecards are run:

1. TP2 should be restored to the 1D path and aggregate TP/TW scoring.
2. The next model family must represent the loop as coupled, segment-resolved
   pressure and thermal physics, including an upcomer hybrid between ordinary
   throughflow and a recirculating convection cell.

This is a coordination note only. It does not mutate native CFD outputs, Fluid
source, or current scorecard outputs.

## Decisions

### TP2 returns to the 1D path

Current sensor policy excluded TP2 because the provisional Fluid coordinate is
off the current 1D path. The policy note says native CFD TP2 and prior notes
bind TP2 to the right-downcomer / bottom-horizontal junction. The next sensor
work must therefore map TP2 onto that 1D path location and restore it as a
post-solve validation/scoring target once the projection and finite-output gates
pass.

Admission requirements before TP2 enters aggregate scoring:

- `source_segment` is assigned, expected initially as the
  right-downcomer/bottom-horizontal junction path.
- Fluid/1D prediction for TP2 is finite on the scored rows.
- TP2 remains `runtime_temperature_allowed = false`.
- TP2 remains `fit_allowed = false`.
- The before/after scorecard states the sensor-count change explicitly:
  current aggregate is 5 TP + 10 TW; restored target is 6 TP + 10 TW.

TP/TW probes remain validation outputs only. They must not become model inputs
or fitted temperatures.

### TW10 stays excluded

TW10 is a cooling-jacket shell surrogate. The current imposed-cooler and
setup-predictive forward modes do not emit a finite active-HX shell-state
temperature for that sensor. TW10 should stay out of aggregate TP/TW scoring
until an explicit HX shell/wall state exists and passes the same finite-output
and source-state audit.

This is not a data-quality failure. It is a model-output contract decision:
do not score a state the model does not claim to predict.

### Upcomer model target is pipe flow plus convection cell

The current Salt2-4 upcomer evidence is recirculating. A single-stream
ordinary-pipe model is not an admitted interpretation for fitted `Nu`, `f_D`,
or `K` in that regime. The next upcomer model should split the physics into:

- a throughflow pipe-like component carrying the net loop mass flow, and
- a recirculating convection-cell component that exchanges momentum and heat
  with the throughflow and wall.

Conceptually:

```text
mdot_loop = mdot_through
Q_wall,up = Q_through_internal + Q_cell_exchange + Q_mixing + Q_unresolved
dp_up = dp_through_friction + dp_reset/development + dp_cell_apparent + dp_junction
```

The recirculation-cell weight should be tied to observed/extracted regime
metrics such as reverse-flow area fraction, reverse-flow mass fraction,
secondary velocity fraction, `Ri`, `Gr`, `Ra`, `Re`, `Pr`, `Gz`, and wall-bulk
temperature drive. Until ordinary/transition anchors exist, onset remains
uncalibrated.

### Boundary-layer development must be scored, not assumed away

Hydraulic and thermal development can affect both `mdot` and TP/TW RMSE. The
next model work should quantify development effects by segment instead of using
a hidden global multiplier.

Required scorecard axes:

- hydraulic entrance/reset/development terms by leg and junction,
- apparent developing-flow friction such as Shah-style or equivalent terms,
- thermal entrance/Graetz effects by heated/cooled/passive segment,
- wall-adjacent temperature drive versus bulk-temperature drive,
- wall/layer resistance effects on TP and TW errors,
- ablations reported separately for `mdot`, TP RMSE, TW RMSE, Tmean, and loop
  Delta T.

## Board TODOs created

- `TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE`
- `TODO-UPCOMER-PIPE-CELL-HYBRID-MODEL`
- `TODO-PREDICT-BOUNDARY-LAYER-DEVELOPMENT-SCORECARD`

These complement the existing segment equation, segment pressure, segment
thermal, and M3+TS scorecard rows. The intended order is:

1. Restore TP2 scoring policy and keep TW10 excluded.
2. Freeze the segment-resolved equation contract.
3. Score boundary-layer/development effects by segment.
4. Build the upcomer pipe-cell hybrid candidate.
5. Run the coupled setup-only M3+TS scorecard.

## Guardrails

- Do not mutate native CFD outputs.
- Do not edit external `../cfd-modeling-tools/**` unless a later board row
  explicitly claims it.
- Do not use TP/TW values as runtime model inputs.
- Do not use realized CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler duty, or
  realized test-section net heat in a predictive runtime model.
- Do not label recirculating upcomer rows as fitted single-stream `Nu`, `f_D`,
  or `K`.
- Do not re-open stale blockers: OF13 reconstruction works, mesh families exist,
  and CFD `rcExternalTemperature` includes radiation.
