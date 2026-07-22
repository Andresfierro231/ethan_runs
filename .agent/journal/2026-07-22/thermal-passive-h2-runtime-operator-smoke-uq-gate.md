---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_one_train_repair_preflight/passive_operator_term_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/sensor_projection_predictions.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_execution/mdot_heat_sensitivity.csv
tags: [journal, thermal, passive-h2, runtime-operator, smoke-uq, no-release]
related:
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/README.md
  - imports/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate.json
task: TODO-THERMAL-PASSIVE-H2-RUNTIME-OPERATOR-SMOKE-UQ-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# passive_H2 runtime-operator smoke/UQ gate

## Attempted

Claimed a separate execution/gate row after the completed dry one-train
passive_H2 repair preflight. Built a reproducible postprocess that evaluates a
diagnostic no-leak passive operator for `PASSIVE-H2-CAND001` on the Salt 2 train
case. The operator consumes setup hA/area/Ta/Tsur/emissivity/layer provenance
and model-predicted wall-state temperatures from the train-only setup-UQ smoke.

Also joined existing train-only mdot, heat-ledger, and TP/TW projection
sensitivity so the result reports the requested QoIs without launching new
solver work.

## Observed

The smoke gate is executable with forbidden runtime inputs disabled. The
nominal local passive operator is `873.2718786177952 W`, with `656.4927338489465
W` from the direct radiation term and `216.7791447688486 W` from convection.

The existing Salt 2 train-only setup-UQ context gives maximum sensitivity
values of `0.000933617528568 kg/s` for mdot, `12.4703209333 K` for TP,
`32.6280138454 K` for TW, and `7.18208423015 W` for heat-ledger qambient.

The existing `radiation_on` setup-UQ variant has zero model-output delta, while
the local operator radiation-off comparison is large.

## Inferred

The no-leak operator pathway is now testable, but the radiation/runtime-basis
semantics are not ready for numeric release. The large radiation term and zero
effect of the existing model `radiation_on` variant point to an implementation
or basis mismatch that must be resolved before any passive_H2 numeric q-loss,
source/property, Qwall, repair, or freeze claim.

## Caveats

The emitted operator heat-loss values are diagnostic smoke values only. They are
not admitted source properties, Qwall values, repair outputs, coefficient
admissions, frozen candidates, protected scores, or final-score values.

The current row did not edit Fluid or execute a solver. It used existing
train-only model predictions and setup-UQ outputs as read-only source evidence.

## Next Useful Actions

Claim a targeted passive_H2 radiation/runtime-basis reconciliation row. It
should determine why `radiation_on` does not change the train-only model outputs
while the source-backed direct radiation operator is large. It should remain
train-only and no-leak, and it should still forbid wallHeatFlux, protected
temperatures, CFD mdot, Qwall, hidden global multipliers, and residual
absorption into internal Nu.
