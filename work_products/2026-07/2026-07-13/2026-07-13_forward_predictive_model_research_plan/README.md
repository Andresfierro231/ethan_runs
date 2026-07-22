# Forward Predictive 1D Model Research Plan

Task: `AGENT-286`
Date: 2026-07-13

## Purpose

This package documents what is needed to turn the current CFD/1D parity work
into an end-to-end forward predictive model for the TAMU loop. The target is a
model that can accept physical setup inputs, solve for steady mass flow, march
the thermal state, and predict sensor temperatures without using CFD mdot,
realized CFD wall flux, or CFD target temperatures as runtime inputs.

## Prediction Target

The desired forward problem is:

```text
given:
  geometry
  fluid/material properties
  heater input power
  cooler/HX operating condition or imposed cooler duty
  ambient/surroundings conditions
  wall/insulation/layer construction
  hydraulic closure
  external heat-loss closure
  sensor map

solve:
  mdot
  loop bulk-temperature field
  wall/surface temperatures
  section heat gains/losses
  cooler duty if not imposed
  TP/TW sensor predictions
```

A stricter fully predictive case would not take cooler duty as an input. It
would take coolant/air-side boundary conditions and an HX model, then solve the
cooler duty internally. A useful intermediate case may take measured/imposed
cooler duty as a boundary condition while pressure and sensor temperatures are
predicted.

## Current Answer

We have enough infrastructure to run a forward model, but we do not yet have
enough admitted, fit-safe physics to claim end-to-end predictivity for mdot and
sensor temperatures.

The Fluid model already contains a thermo-hydraulic solve skeleton: geometry,
materials, pressure closure, temperature marching, parasitic heat loss,
cooling-jacket sink, and sensor prediction support. The current CFD evidence
stack supplies many needed setup inputs. The problem is that several inputs are
currently diagnostic or CFD-derived rather than predictive:

- cooler/HX duty is first-order and not yet predictive enough,
- heater imposed power and heater heat transferred to fluid differ,
- the test section is not a pure source in CFD realized wall flux,
- external wall heat loss is driven by wall/near-wall temperatures, not by a
  segment-average bulk temperature,
- radiation/emissivity is inseparable in available `rcExternalTemperature`
  wall-flux outputs,
- thermal mesh/time-window/recirculation gates block `Nu`/`h` fitting,
- sensor-location confidence remains provisional.

## Deliverables In This Package

- `input_readiness_matrix.csv`: each forward-model input, whether it exists,
  whether it is predictive, and the next gate.
- `blocker_register.csv`: blockers that prevent a thesis-strength predictive
  claim.
- `task_backlog.csv`: concrete next tasks to make the model work end to end.
- `research_plan.md`: phased scientific plan with acceptance criteria.

## Source Evidence

This plan relies on:

- `work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_heat_loss_path/`
- `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/`
- `work_products/2026-07/2026-07-13/2026-07-13_rc_external_temperature_implementation_audit/`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/`
- `work_products/2026-07/2026-07-13/2026-07-13_salt2_closure_qoi_mesh_gci/`
- `reports/2026-07/2026-07-09/2026-07-09_internal_nu_model_form_comparison/`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/`
- `operational_notes/07-26/10/2026-07-10_thermal_parity_roadmap.md`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/README.md`

## Decision Rules

1. Do not use CFD mdot as a runtime input for predictive claims.
2. Do not use realized CFD `wallHeatFlux` as a runtime input except in clearly
   labeled diagnostic modes.
3. Do not fit passive external hA until cooler/HX, heater transfer, and
   test-section source/loss contracts are separated.
4. Do not combine radiation, external convection, internal Nu, and wall-layer
   mapping into one scalar.
5. Do not claim sensor predictivity before energy balance and branch heat-loss
   parity are acceptable.
6. Do not make thesis-strength claims without held-out cases plus time-window
   and mesh uncertainty.

## Immediate Recommendation

Build a forward-v0 in two layers:

1. **Imposed-cooler predictive-pressure mode**: use heater input and imposed
   cooler duty, solve mdot and temperatures, and compare mdot plus sensors.
   This isolates hydraulic and wall/source contracts from HX uncertainty.
2. **Predictive-HX mode**: replace imposed cooler duty with a low-dimensional
   UA or epsilon-NTU cooler model after the first mode is stable.

The first task should be a strict input-contract table for Fluid: every runtime
input must be classified as physical setup, calibrated parameter, validation
target, or diagnostic-only CFD evidence.

## Relationship To Existing TODO Rows

The board already contains older focused predictive rows:

- `TODO-PREDICT-HEATER-FLUID-FRACTION`
- `TODO-PREDICT-COOLER-REMOVAL`

The new `TODO-PRED-*` rows do not invalidate those. They organize the work into
an end-to-end sequence. In particular:

- `TODO-PRED-HEATER-TEST-CONTRACT` should consume or supersede the heater-fluid
  fraction work by adding the test-section source-plus-loss contract.
- `TODO-PRED-HX-FIT` should consume or supersede the cooler-removal work by
  adding train/heldout separation and integration with the forward-v0 mode.
