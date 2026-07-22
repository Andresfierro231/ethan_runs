---
provenance:
  - source_manifest.csv
tags: [forward-model, math, assumptions, residual-attribution]
related:
  - README.md
task: AGENT-366
date: 2026-07-14
role: Forward-pred/Scientific-closure
type: method_note
status: complete
---
# Math, Assumptions, Theory, And Results

## Purpose

Forward-v1 predicts loop mass flow and TP/TW temperatures from setup-level
inputs only. CFD observations are joined after the solve for scoring and
residual attribution.

## Residual Definitions

- Mass-flow residual: `e_mdot = mdot_1d - mdot_cfd`.
- Sensor residual: `e_T(sensor) = T_1d(sensor) - T_cfd(sensor)`.
- Role heat residual: `e_Q(role) = Q_1d(role) - Q_cfd_reference(role)`.
- Section thermal residual: `e_T_section = T_1d_section - T_cfd_section`.

## Attribution Lanes

- `hydraulic_mdot`: friction, localized loss, reset/development, and pressure
  evidence.
- `boundary_hx_heat`: setup-only cooler/HX and external-wall heat removal.
- `sensor_temperature`: post-solve TP/TW comparison only.
- `internal_nu_thermal`: internal heat-transfer closure; currently blocked for
  fitting.
- `cfd_admission_uncertainty`: terminal state, split policy, and metric
  admission quality.

## Assumptions

- The active final split remains `salt_2=train`, `salt_3=validation`,
  `salt_4=holdout`.
- Fluid reset/development API support is implemented, but this is not pressure
  evidence.
- Salt1 terminal BC rows are training-context evidence only until a dated split
  revision admits them to a final scorecard population.
- +/-5Q corrected-Q rows are sensitivity/admission evidence only; they add zero
  independent training rows today.
- CFD `rcExternalTemperature` embeds radiation metadata; do not add a separate
  radiation correction on top of CFD wallHeatFlux-derived diagnostics.

## Results From This Refresh

- Final forward-v1 remains blocked.
- Scorecard-ready input lanes are now explicit.
- Residual-attribution output columns are predefined for the next runnable
  scorecard.
- PM5 matched pressure/upcomer metrics remain the first pending gate.
