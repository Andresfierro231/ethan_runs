---
task: AGENT-492
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
tags: [journal, AGENT-492, cooler, wall-circuit, predictive-wall]
related:
  - .agent/status/2026-07-17_AGENT-492.md
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_fluid_timeout_and_wall_circuit_study/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model/README.md
---
# Cooler Fluid Timeout Diagnosis And Wall-Circuit Study

## Why This Avenue Exists

AGENT-482 left the cooler-removal coupled scorecard blocked by `12/12`
`timeout_after_45s` rows. The next scientific question was whether the Fluid
solve path was stuck, or whether the timeout bound was simply shorter than the
ordinary coupled solve runtime. In parallel, the wall/test-section/passive
boundary blocker needed a better candidate than the prior local TS1/TS2
static screen.

## Observed Facts

- A direct in-process Salt2 lumped cooler probe completed with an accepted root
  in about `59.797 s`, already exceeding the old `45 s` bound.
- The bounded rerun with `--timeout-seconds 180` completed all `12` coupled
  candidate/case rows.
- Completed elapsed times were `69.97005505-136.4293815 s`; the posthoc future
  production timeout recommendation is `273 s`.
- The coupled cooler rows are not admission-quality: mdot errors remain about
  `29-37%`, TP RMSE about `64-69 K`, and TW RMSE about `120-135 K`.
- The passive-total thermal-circuit candidate
  `PB1_total_hA_heater_power_drive_p1` passes static validation/holdout gates.
- Local test-section candidates remain failed by percent gate, even when W
  errors improve under heater-power drive scaling.

## Interpretation

The AGENT-482 timeout was a bound-selection problem, not a Fluid API failure.
The cooler-duty model can now be reviewed from completed coupled rows. Those
rows do not close the predictive-wall/test-section blocker because the coupled
thermal/hydraulic errors remain large and the wall-circuit candidate has only a
static total-passive pass.

The better wall-circuit direction is to keep active heater and active cooler/HX
terms separated, represent passive boundary loss as a setup hA network with one
Salt2-trained drive scaled by setup heater power, and retain local test-section
component scoring as a separate gate. This avoids using passive total-loss
cancellation to admit a local recirculating test-section miss.

## Commands

- `python3.11 -c '...'` direct Salt2 Fluid timing probe.
- `python3.11 -m unittest tools.analyze.test_cooler_removal_model tools.analyze.test_cooler_timeout_and_wall_circuit_study`
- `python3.11 -m py_compile tools/analyze/build_cooler_removal_model.py tools/analyze/test_cooler_removal_model.py tools/analyze/build_cooler_timeout_and_wall_circuit_study.py tools/analyze/test_cooler_timeout_and_wall_circuit_study.py`
- `python3.11 tools/analyze/build_cooler_removal_model.py --run-fluid --timeout-seconds 180`
- `python3.11 tools/analyze/build_cooler_timeout_and_wall_circuit_study.py`

## Next Action

Promote `PB1_total_hA_heater_power_drive_p1` into a coupled M3+TS+cooler
candidate and score it in Fluid with no realized `wallHeatFlux`, no CFD mdot,
no imposed CFD cooler duty, and no validation/holdout temperatures as runtime
inputs. Keep local test-section and passive-total gates separate.
