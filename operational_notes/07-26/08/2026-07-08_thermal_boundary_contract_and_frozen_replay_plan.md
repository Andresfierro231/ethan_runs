# Thermal Boundary Contract and Frozen-Hydraulics Replay Plan

Date: `2026-07-08`
Task: `AGENT-208`
Role: Coordinator / Implementer / Writer

## Question

The next 1D work should not tune friction harder.  It should reconstruct the
actual CFD thermal boundary contract, compute heat and enthalpy residuals from
the patchwise heat ledger, run a frozen-hydraulics thermal replay, and only then
run model-form bakeoff with hydraulic and thermal errors scored separately.

## Durable Artifact

I built a reproducible contract package:

- Builder: `tools/analyze/build_thermal_boundary_contract.py`
- Tests: `tools/analyze/test_thermal_boundary_contract.py`
- Output root: `work_products/2026-07-08_thermal_boundary_contract/`
- Package README: `work_products/2026-07-08_thermal_boundary_contract/README.md`

The package is read-only with respect to native solver outputs.  It consumes:

- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-02_overnight/driver_thermal_compare.json`
- read-only Fluid solver source under
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/`

## Observed CFD Contract

The Salt 2/3/4 CFD rows are labeled in the generated contract as:

`cfd_salt_1p4in_layer_present_surface_emissivity_bc_metadata_present_no_qr_field`

That label is intentionally specific:

- `1.4 in` is the CFD insulation/layer contract where present.
- Prior `0.25 in` or `0.30 in` labels are 1D diagnostic/sweep settings, not the
  CFD case label.
- Surface emissivity metadata is present in boundary metadata, but the heat
  ledger has `radiation_present=False` because no OpenFOAM `qr` output term was
  available.  The contract therefore does not silently convert emissivity into a
  radiation heat-ledger term.

The patchwise roles preserved in
`cfd_thermal_boundary_contract.csv` are:

- `heater`: prescribed source candidate, but heater imposed duty is larger than
  realized wallHeatFlux by 22.181 W, 24.345 W, and 27.113 W for Salt 2/3/4.
- `cooler`: prescribed sink candidate; cooler specified duty matches
  wallHeatFlux closely in the ledger.
- `ambient_wall`: passive ambient exchange candidate.
- `test_section`: explicit quartz test-section exchange candidate, not a hidden
  main-pipe insulation row.
- `junction_other`: grouped diagnostic wall flux, not bracketed by endpoint
  temperature spans.

## Thermal Targets and Current 1D Mismatch

`case_thermal_targets.csv` records the current prior 1D state against CFD:

| Case | CFD mdot kg/s | CFD Tmean K | CFD loop dT K | 1D Tmean K | 1D loop dT K | Tmean error K | dT error K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Salt 2 | 0.01318 | 450.3 | 12.1 | 512.250 | 8.192 | +61.950 | -3.908 |
| Salt 3 | 0.01497 | 463.7 | 12.2 | 527.398 | 8.293 | +63.698 | -3.907 |
| Salt 4 | 0.01698 | 479.2 | 12.3 | 545.401 | 8.578 | +66.201 | -3.722 |

This confirms the handoff diagnosis: the dominant error is thermal state
mismatch, not a pressure-loss-only problem.

## Heat Ledger and Enthalpy Residual Handling

`span_heat_residuals.csv` carries one heat-ledger span residual per source and
span: five spans per Salt case, 15 rows total.  This is not the same as the raw
18-row endpoint-temperature table, because the heat ledger only includes spans
that have patchwise thermal roles.

Residual caveats are preserved:

- Junction rows remain `not_bracketed_by_endpoint_temperature_segment`.
- Upcomer rows are `computed_diagnostic_only_high_recirculation` and carry
  high-recirculation quality flags.
- Cooler rows are `computed_but_cooler_cut_planes_only_partially_bracket_sink`.
- Residual rows are validation diagnostics, not fit targets.

## Current 1D Solver State

The generated `fluid_solver_state_audit.csv` records these key support gaps:

- Ambient temperature exists as `ScenarioConfig.ambient_temperature_K`, but must
  be set from the CFD boundary metadata rather than assumed.
- `ScenarioConfig.insulation_thickness_in` is a global scalar.  Per-parent
  insulation multipliers exist, but explicit per-segment CFD reconstruction is
  still needed for insulated pipe legs versus bare quartz.
- `radiation_on` is not equivalent to a CFD `qr` heat-ledger term.  Emissivity
  metadata and `qr` output must remain separate.
- 3D source profiles and prescribed segment losses have hooks through
  `three_d_contract_case_id`, `use_three_d_source_profile`,
  `use_three_d_segment_losses`, and
  `ambient_loss_model=external_prescribed_segment_loss`, after a normalized
  contract is prepared.
- No explicit fixed-mdot or frozen-hydraulics `ScenarioConfig` field was found.
  The replay needs a solver extension or reviewed wrapper before we can claim
  thermal-only iteration.

## Required Replay Sequence

The generated `frozen_hydraulics_replay_plan.csv` defines the gate sequence:

1. Reproduce the current July 2 1D baseline.
2. Freeze hydraulics to CFD mdot with a 5 pct relative gate.
3. Prescribe CFD patch heat ledger terms with sign-convention tests.
4. Reconstruct the CFD boundary network: 1.4 in insulated pipe legs where
   present, bare quartz test section, CFD ambient/h, emissivity tracked
   separately from `qr`.
5. Iterate only thermal BC terms until all admitted Salt cases satisfy
   `abs(Tmean error) <= 2 K` and `abs(loop delta T error) <= 1 K`.
6. Run model-form bakeoff only after stage 5 passes, with separate pressure
   distribution, mdot, mean-T, and loop-dT scores.

## Tests Run

Commands:

```bash
python3.11 tools/analyze/build_thermal_boundary_contract.py
python3.11 -m unittest tools.analyze.test_thermal_boundary_contract
python3.11 -m py_compile tools/analyze/build_thermal_boundary_contract.py tools/analyze/test_thermal_boundary_contract.py
```

Results:

- Builder completed and wrote
  `work_products/2026-07-08_thermal_boundary_contract/summary.json`.
- Focused unittest suite: 5 tests passed.
- Syntax check passed.

## Next Actions

1. Add or review a Fluid fixed-mdot/frozen-hydraulics thermal replay path.  This
   is the gating implementation step before thermal iteration.
2. Normalize the July 8 patchwise heat ledger into the Fluid 3D coupling
   contract format for Salt 2/3/4.
3. Run replay stages 0-4 and record every iteration with exact solver inputs,
   target residuals, and pass/fail status.
4. Keep model-form bakeoff blocked until the replay stage 4 thermal gate passes.
