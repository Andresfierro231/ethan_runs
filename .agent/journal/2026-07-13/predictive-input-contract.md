# Predictive Input Contract

Task: TODO-PRED-INPUT-CONTRACT

Built a strict runtime input contract for the forward predictive path. The
contract classifies setup inputs, calibrated parameters, validation targets,
diagnostic CFD evidence, and uncertainty metadata. It explicitly prevents
`forward_v0_imposed_cooler` and future `predictive_hx` modes from using CFD
mdot, realized CFD wallHeatFlux, CFD/experimental temperatures, or sensor
measurements at runtime.

Generated package:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/`

Source evidence:

- Fluid cases config: `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`
- Fluid validation table: `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/validation_cases.csv`
- CFD thermal targets: `work_products/2026-07/2026-07-08/2026-07-08_thermal_boundary_contract/case_thermal_targets.csv`
- CFD patch boundary setup: `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`
- Research plan: `work_products/2026-07/2026-07-13/2026-07-13_forward_predictive_model_research_plan/research_plan.md`

Validation:

- `python3 tools/analyze/test_predictive_input_contract.py`
- `python3 tools/analyze/build_predictive_input_contract.py --strict`

Strict status: pass. `violations.csv` contains only the header.

Open blockers remain assigned to later TODO-PRED rows: predictive HX, heater/test-section transfer efficiency, wall-layer mapping, hydraulic gate, thermal mesh gate, sensor map, validation split, and end-to-end scorecard.
