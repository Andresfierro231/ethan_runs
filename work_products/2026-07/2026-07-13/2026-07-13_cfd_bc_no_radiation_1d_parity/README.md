# CFD BC No-Radiation 1D Parity

Generated: `2026-07-13T20:34:11+00:00`
Task: `AGENT-279`

## Purpose

This package tests a radiation-off fixed-mdot sensitivity: impose the CFD
heater and cooler setup together in the 1D model, force radiation off, and
compare whether the same sections gain and lose the same heat. It is fixed-mdot
and repo-local. It does not edit Fluid, mutate CFD solver outputs, or change
admissions.

Important correction from AGENT-287: this package is not Ethan-CFD parity.
AGENT-277 showed that Ethan CFD `rcExternalTemperature` responds to
`emissivity` and `Tsur`, so radiative exchange is embedded in total CFD
`wallHeatFlux`. This radiation-off package remains useful as a diagnostic
sensitivity only.

## Outputs

- `cfd_boundary_condition_contract_no_radiation.csv`: role-level CFD boundary
  inputs mapped to Fluid parent segments, including imposed Q, realized
  wallHeatFlux, and convection-only `hA/Ta` terms.
- `fixed_mdot_no_radiation_parity_results.csv`: no-radiation fixed-mdot replay
  results for N0-N3.
- `section_heat_loss_comparison.csv`: section-by-section model heat gain/loss
  versus CFD imposed and realized heat.
- `discrepancy_attribution.csv`: heater, cooler, test-section, and passive
  external residual lanes.
- `correction_proposal.csv`: low-dimensional correction candidates.
- `path_summary.csv` and `run_metadata.json`.

## Main Result

Best radiation-off sensitivity path by mean absolute Tmean error:
`N1_heater_cooler_imposed_rad_off`.

The package should be read with the section residuals, not only the mean
temperature score. `N2_cfd_setup_bc_plus_passive_conv_rad_off` is the closest
current repo-local radiation-off hA/Ta replay: heater/test-section imposed
sources, cooler imposed duty, and non-cooler `hA/Ta` convection-only losses.
Wall-layer parity remains approximate until Fluid has a first-class external
boundary dictionary mode.

## How To Read This Package

Use this package as a radiation-off sensitivity diagnostic, not as a final
thermal-closure fit and not as evidence that CFD radiation is absent. The
intended reading order is:

1. `cfd_boundary_condition_contract_no_radiation.csv`
   Defines the CFD patch roles reduced to Fluid parent segments. It preserves
   imposed heater/cooler/test-section setup terms, realized `wallHeatFlux`,
   non-cooler `hA/Ta`, and the explicit radiation-off sensitivity policy used
   in this pass.
2. `run_plan.csv`
   Lists the four fixed-mdot no-radiation replay modes for Salt2-4.
3. `path_summary.csv`
   Shows which mode best closes bulk mean temperature. This is only a first
   screen; it does not prove section heat parity.
4. `section_heat_loss_comparison.csv`
   Compares model heat gain/loss against CFD imposed and realized heat by
   physical section. This is the main table for finding where the model is
   losing heat in the wrong place.
5. `discrepancy_attribution.csv`
   Separates heater, cooler, test-section, and passive external residual lanes.
   Do not combine these lanes into one fitted scalar.
6. `correction_proposal.csv`
   Records low-dimensional correction candidates and blocks. Values marked
   diagnostic are not admissions.

## Replay Modes

- `N0_current_fluid_rad_off`: current Fluid thermal contract at CFD mdot, with
  radiation disabled.
- `N1_heater_cooler_imposed_rad_off`: CFD heater imposed source plus CFD cooler
  imposed duty, no radiation. This tests the first-order setup parity.
- `N2_cfd_setup_bc_plus_passive_conv_rad_off`: CFD heater/test-section setup
  sources, CFD cooler imposed duty, and non-cooler `hA/Ta` convection-only
  losses using 1D bulk temperature as the driving temperature. This is the
  closest current repo-local radiation-off hA/Ta replay, but it is not
  Ethan-CFD parity after AGENT-277/287 and is not yet wall-layer equivalent.
- `N3_realized_wallflux_diagnostic_rad_off`: fixed-Q diagnostic from realized
  CFD wall fluxes. It is heat-accounting evidence, not a predictive boundary
  model.

## Wall-Layer Mapping Block

The N2 replay intentionally applies CFD `hA/Ta` rows to the current 1D bulk
state through `q = hA * max(T_bulk - Ta, 0)`. That is a useful stress test, but
it is not the same as OpenFOAM's wall-boundary calculation. In CFD, the
boundary condition acts at the wall/near-wall temperature field, while the 1D
state is a segment bulk temperature. If wall-adjacent fluid is cooler or hotter
than the 1D bulk, the same `hA/Ta` can remove too much or too little heat.

The recommended mapping ladder is documented in:

`wall_layer_bulk_temperature_mapping_recommendations.md`

Until that ladder is implemented, external hA multipliers in
`correction_proposal.csv` should remain diagnostic only.

## Scientific Boundary

Radiation is forced off for this pass only as a sensitivity. AGENT-277 and
AGENT-287 supersede the original assumption that this matched CFD. The CFD
`rcExternalTemperature` boundary uses emissivity/Tsur and includes radiative
exchange inside total `wallHeatFlux`, but no separate `qr`/radiation ledger is
available. Therefore:

- Do not add a separate 1D radiation term on top of CFD `wallHeatFlux`.
- Do not call this radiation-off package CFD parity.
- For predictive 1D setup from physical inputs, retain/add radiative external
  loss capability or label radiation disabled as a sensitivity.

## Counts

- Boundary contract rows: `24`
- Run-plan rows: `12`
- Result rows: `12`
- Section comparison rows: `60`
- Discrepancy rows: `48`
- Correction proposal rows: `5`
- Validation errors: `0`
