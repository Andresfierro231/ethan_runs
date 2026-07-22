# Thermal Boundary Contract and Frozen Replay Plan

Generated: `2026-07-08T18:34:07+00:00`
Task: `AGENT-208`

## Scope

This package reconstructs the current CFD thermal boundary contract for admitted Salt 2/3/4 Jin mainline continuation rows and defines the frozen-hydraulics replay gate needed before any model-form bakeoff.

## Key Findings

- CFD Salt rows are labeled `cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`.
- The July 2 1D reference scenario `predictive_airside_ins_1.0in_rad_1` is 61.950 to 66.201 K hotter than CFD and has a loop delta T 3.7 to 3.9 K smaller.
- `radiation_present=False` in the patchwise heat ledger means no OpenFOAM `qr` output term was available. Surface emissivity metadata is preserved as metadata, not converted into a heat-ledger radiation term.
- Heater imposed duty exceeds realized heater wallHeatFlux by about 22 to 27 W; this remains a boundary/solid/storage or staging mismatch until a same-time solid-energy audit exists.
- Frozen hydraulics are not an obvious first-class Fluid `ScenarioConfig` option yet. The replay needs a fixed-mdot solver hook or a reviewed wrapper before thermal-only iteration can be claimed.

## Outputs

- `cfd_thermal_boundary_contract.csv`: patchwise CFD thermal roles and reconstructed boundary metadata.
- `span_heat_residuals.csv`: unique span endpoint enthalpy-change and wallHeatFlux residual rows.
- `case_thermal_targets.csv`: CFD targets, prior 1D mismatch, and aggregate heat ledger quantities.
- `fluid_solver_state_audit.csv`: current 1D solver capabilities and gaps relevant to the replay.
- `frozen_hydraulics_replay_plan.csv`: required sequence and gates before bakeoff.
- `test_plan.csv`: tests and review gates required for paper-grade use.
- `summary.json`: machine-readable counts and validation errors.

## Source Evidence

- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-02_overnight/driver_thermal_compare.json`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/three_d_coupling.py`

## Validation

- Contract rows: `24`
- Target rows: `3`
- Validation errors: `0`
