---
provenance:
  - operational_notes/07-26/15/2026-07-15_segment_resolved_pressure_thermal_modeling_plan.md
  - operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/runtime_input_contract.csv
tags: [segment-equation-contract, forward-predictive-model, m3ts, runtime-input-contract]
related:
  - .agent/status/2026-07-17_TODO-PREDICT-SEGMENT-EQUATION-CONTRACT.md
  - .agent/journal/2026-07-17/predict-segment-equation-contract.md
task: TODO-PREDICT-SEGMENT-EQUATION-CONTRACT
date: 2026-07-17
role: Coordinator/Writer/Implementer/Tester
type: work_product
status: complete
---
# Segment Equation Contract

## Decision

The next forward model must be segment-resolved. Buoyancy drive, pressure loss, source/sink heat terms, properties, and admission labels are local to loop regions. A global friction or heat-loss multiplier is not an admitted model form.

## Main Outputs

- `equation_forms.csv`: expanded pressure/thermal/root equations.
- `segment_equation_contract.csv`: allowed model slots for each loop region.
- `pressure_model_slots.csv`: pressure-specific slot aliases derived from the segment table.
- `thermal_model_slots.csv`: thermal-specific slot aliases derived from the segment table.
- `runtime_input_contract.csv`: runtime leakage audit.
- `downstream_gate_contract.csv`: gates for pressure, thermal, boundary-layer, and coupled scorecards.
- `source_manifest.csv`: cited source paths.

## Observed Facts

- Equation rows: `5`.
- Segment rows: `7`.
- Runtime audit rows: `6`.
- Downstream gate rows: `4`.

## Guardrails

- CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty, validation temperatures, hidden global multipliers, and recirculating-row true `Nu`/`f_D`/`K` fits are forbidden runtime inputs.
- Pressure and thermal scorecards may now start from this package, but the coupled M3+TS scorecard must wait until both are complete.
- Diagnostic CFD rows remain score/target evidence unless an admission package explicitly promotes a model coefficient.
