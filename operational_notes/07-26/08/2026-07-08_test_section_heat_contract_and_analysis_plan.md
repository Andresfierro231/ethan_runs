# Test-Section Heat Contract And Analysis Plan

Date: `2026-07-08`
Task: `AGENT-207`
Role: Coordinator / Implementer / Writer

## Question

The July 8 heat ledger shows that heater imposed duty exceeds realized
`wallHeatFlux`, and that the test-section patch is a net sink even though the
Salt 1D input contract includes `test_section_power_W = 37.0 W`. This note
documents what that means and what analysis is needed before the 1D model can
predict net heat gained or lost through the test section.

## Observed Facts

- The CFD Salt `0/T` boundary metadata imposes positive heater/test-section
  `Q` values and negative cooler `Q` values. The July 8 heat ledger extracts
  those as `imposed_Q_sum_W`.
- The same ledger extracts OpenFOAM `wallHeatFlux` at the fluid boundary. Its
  sign convention is positive into the fluid and negative out of the fluid.
- For the main heater group, imposed electrical duty exceeds realized
  wallHeatFlux:
  - Salt 2: `265.7 W` imposed vs `243.519 W` wallHeatFlux.
  - Salt 3: `297.5 W` imposed vs `273.155 W` wallHeatFlux.
  - Salt 4: `337.6 W` imposed vs `310.487 W` wallHeatFlux.
- For the cooler group, imposed duty and wallHeatFlux agree to within
  `0.001 W`, so the sign extraction and imposed-Q parsing are internally
  consistent.
- For the test-section group, the Salt CFD boundary metadata imposes `37 W`,
  but the fluid-side `wallHeatFlux` is negative:
  - Salt 2: `-5.68 W`
  - Salt 3: `-10.545 W`
  - Salt 4: `-16.769 W`
- The 1D Fluid geometry marks the quartz test section as uninsulated and as a
  test-section heater:
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
  has `has_test_section_heater=True`, `insulated=False`, and
  `wall_material="Quartz"` for segment `test_section`.
- The 1D Fluid case config assigns Salt cases `test_section_power_W = 37.0`
  and active Water cases `test_section_power_W = 0.0` in
  `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`.
- The 1D Fluid solver applies the Salt test-section power as a positive source:
  `heating_power_for_segment_with_scenario()` returns
  `case.test_section_power_W * scale` when `segment.has_test_section_heater`,
  and `march_temperatures()` advances segment temperature with
  `T_new = T_in + (Q_source - q_sink - q_amb) / (mdot * cp)`.

## Interpretation

`heater imposed duty exceeds realized wallHeatFlux` means the electrical/source
term prescribed in the boundary condition is larger than the net heat crossing
the fluid-side wall boundary in the extracted `wallHeatFlux` output. It does not
mean the `Q` parser is wrong; the cooler agreement argues the parser and sign
convention are sane.

For the heater, the difference is plausibly a boundary/solid/storage/staging
effect: imposed power is not identical to the instantaneous net fluid-interface
heat rate unless the solid and wall boundary are at a same-time steady balance.

For the test section, the contradiction is stronger. The current 1D model
implements the stated Salt electrical-input contract correctly as a positive
`37 W` source into the test-section segment. However, the CFD wallHeatFlux says
the net fluid-interface exchange through the test-section patch is heat leaving
the fluid. Therefore the existing 1D source term is a gross imposed-power
contract, not a validated predictor of net fluid heat gain through the quartz
test section.

In other words:

- The 1D implementation is correct for "Salt cases include 37 W test-section
  imposed power."
- It is not sufficient for "the fluid gains 37 W through the test section."
- To predict net fluid heat gain/loss, the 1D thermal model must solve or
  prescribe the competing loss path from test-section wall/quartz to ambient and
  compare the resulting net interface heat with CFD `wallHeatFlux` and enthalpy
  change.

## Analysis Needed

1. Create a test-section heat sub-ledger from the July 8 patchwise heat ledger:
   imposed `Q`, wallHeatFlux, wall temperature, area, internal effective HTC,
   wall conduction resistance, external convection resistance, radiation status,
   and segment enthalpy residual.
2. Extract or confirm same-time wall and ambient boundary temperatures for the
   test-section row. The current ledger uses reconstructed wall T and `0/T`
   metadata, but specified-Q rows do not always expose the full external
   resistance stack.
3. Add a 1D diagnostic mode that reports per-segment:
   `Q_source`, `q_ambient_loss`, `q_hx_sink`, `Q_net_to_fluid`, `T_in`,
   `T_out`, and `mdot cp DeltaT`. The existing solver has most pieces in
   `SegmentState`; the missing product is a direct, fit-ready comparison table
   against the CFD heat ledger.
4. For the test section, score three candidate closures separately:
   gross imposed source only, imposed source minus external quartz/ambient loss,
   and CFD-calibrated net wallHeatFlux/UA diagnostic. Do not mix these into one
   mdot score.
5. Treat radiation as absent unless OpenFOAM exposes a `qr` term. Boundary
   emissivity metadata alone should not be counted as an extracted radiation
   heat term.
6. Keep upcomer/test-section enthalpy residuals validation-only until
   recirculation-cell behavior is modeled. The span endpoint temperature source
   reports high upcomer recirculation, so the residual is evidence of regime
   mismatch, not an ordinary pipe heat-transfer coefficient.

## Files Used

- `work_products/2026-07-08_patchwise_heat_ledger/patchwise_heat_ledger.csv`
- `work_products/2026-07-08_patchwise_heat_ledger/README.md`
- `work_products/2026-07-08_span_endpoint_temperatures/span_endpoint_temperatures.csv`
- `work_products/2026-07-08_postprocessor_summary_charts/figures/heat_enthalpy_residual_by_segment.svg`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/geometry.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`

## Recommended Next Action

Use the completed heat ledger and the refreshed enthalpy residual chart as
thermal validation diagnostics in `TODO-MODEL-FORM-BAKEOFF`. Do not score the
1D model as correct merely because it includes `test_section_power_W = 37 W`;
score whether its predicted net test-section heat exchange and segment
enthalpy change match the CFD ledger.
