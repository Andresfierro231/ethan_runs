---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_equation_contract/segment_equation_contract.csv
  - work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-15/2026-07-15_agent373_hydraulic_chain_node_verification/hydraulic_admission_final_decisions.csv
tags: [segment-pressure-models, forward-predictive-model, hydraulics, admission]
related:
  - .agent/status/2026-07-17_TODO-PREDICT-SEGMENT-PRESSURE-MODELS.md
  - .agent/journal/2026-07-17/predict-segment-pressure-models.md
task: TODO-PREDICT-SEGMENT-PRESSURE-MODELS
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Segment Pressure Model Scorecard

## Decision

The segment pressure model slots are now scored against existing evidence and current admission gates. No true segment `f_D` or physical component `K` coefficient is admitted yet. Existing pressure rows remain useful diagnostics and gate evidence.

## Results

- Loop regions reviewed: `7`.
- Model-slot rows: `22`.
- Fit-admitted pressure coefficient rows: `0`.
- Diagnostic evidence rows represented in segment scorecard: `148`.
- Runtime audit pass rows: `4`.

## Interpretation

Pressure and thermal coupling can proceed only with diagnostic pressure terms unless a later package admits segment-local coefficients. Current blockers are mesh/GCI, pressure definition, geometry normalization, component isolation, straight-loss subtraction, and recirculation/hybrid upcomer policy.

## Next Action

Use this package as input to the thermal scorecard and later coupled M3+TS runner, but do not treat it as an admitted pressure closure.
