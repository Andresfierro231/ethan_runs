---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_h1_proxy_rerun/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/comparison_summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/admission_split_table.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/hx_validation_guardrail_scorecard.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/summary.json
tags: [forward-model, predictive-1d, scorecard, validation-split, h1-proxy]
related:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_endtoend_scorecard_precursor/README.md
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-315
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Forward-Model Readiness After H1 Proxy

This is a readiness note and residual-attribution refresh. It is not a final
forward-v1 score, does not fit a new model, does not edit native CFD outputs,
and does not edit external Fluid source.

## Current Decision

Final forward-v1 remains blocked. Evidence improved in two ways: full
`solve_case` confirmation for forward-v0 passed `6/6`
comparison rows, and the H1 aggregate proxy reduced the F1 mean mdot error to
`0.002144 kg/s`. That H1 result is
still screen-only because it is an aggregate fixed-K proxy, not localized H1,
and every Salt row still overpredicts CFD mdot.

## Evidence Now Admitted

- Strict predictive input contract: `0` violations, with the five lit-rev gates present.
- Split discipline: `salt_2=train`, `salt_3=validation`, `salt_4=holdout`.
- Full forward-v0 `solve_case` confirmation: pass; solve_case rows are authoritative for forward-v0.
- H1 proxy: directionality evidence only; no thermal fitting and no publication closure.
- Sensor map: `15` provisional diagnostic labels, with `TP2` and `TW10` blocked.

## Blocks Final Forward-v1

- Faithful localized H1 named-loss/reset implementation has not been run.
- H1 proxy still has systematic positive mdot error versus CFD on Salt2/3/4.
- Thermal gate still has `0` fit-admissible rows and `0` publication-ready thermal GCI rows.
- HX/cooler remains guardrailed proxy evidence, not a fully predictive UA or epsilon-NTU boundary.
- Sensor scoring remains partial and post-solve only.

## Files

- `readiness_lanes_after_h1_proxy.csv`
- `train_validation_holdout_guardrail.csv`
- `residual_attribution_after_h1_proxy.csv`
- `input_contract_gate_readiness.csv`
- `blockers_to_final_forward_v1.csv`
- `source_manifest.csv`
- `summary.json`
