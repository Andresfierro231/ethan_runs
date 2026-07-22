# Paper-Ready Assessment

## Research Question

The AGENT-360 audit compares 1D mass-flow error to CFD TP/TW probe-temperature
error under a ladder of increasingly CFD-informed boundary modes. The key
scientific boundary is that modes using realized CFD wallHeatFlux are diagnostic
or upper-bound evidence; they are not final setup-only predictions.

The study asks whether the current 1D model is predictive for both circulation
rate and thermal state, and whether flow-rate error is coupled to TP/TW
probe-temperature error when CFD boundary information is supplied with different
levels of completeness.

## Case Admission and Data Use

Salt2/Salt3/Salt4 are scored under the current train/validation/holdout split.
Salt1 remains diagnostic because current Salt1 admission policy and patch heat
ledger inputs are incomplete in the consumed source set.

The scored CFD cases are Salt2 as the training row, Salt3 as validation, and
Salt4 as holdout. Salt1 is included only as diagnostic context. Closure
parameters in the simple Part4/Part5 alternatives may be fit on Salt2 only, then
are scored on Salt3/Salt4 without refitting.

## Boundary-Condition Modes

Part 1 contains two diagnostics. `M1_full_cfd_segment_heat_flux_pressure_root`
prescribes the realized CFD segment heat ledger and solves mdot from pressure
balance. `M1b_full_cfd_segment_heat_flux_fixed_mdot` uses the same heat ledger
but imposes CFD mdot, so it isolates thermal/sensor behavior and is not a
hydraulic prediction.

Part 2 prescribes CFD heater heat entry, CFD test-section net heat, and CFD
cooler heat removal, then solves mdot from pressure balance. The test-section
term is encoded as a compatibility negative source, not yet as a first-class
distributed external boundary model.

Part 3 prescribes only CFD heater heat entry and CFD cooler heat removal, then
solves mdot. The Part2-Part3 difference estimates how much the test-section
term changes mdot and probe-temperature errors in the current model.

Part 4 isolates the cooling leg at fixed mdot and compares heat removed. Part 5
isolates the heating leg at fixed mdot and compares heat added. These parts
score current/default model forms, diagnostic imposed-CFD upper bounds, and
one-parameter Salt2 fits evaluated on Salt3/Salt4 without refitting.

## Assumptions

The assumption register is `study_assumption_register.csv`. The most important
assumptions are:

- Positive CFD wallHeatFlux means heat enters the fluid; negative means heat
  leaves the fluid.
- CFD `rcExternalTemperature` includes radiation in total wallHeatFlux; no
  separate exported `qr` term is added.
- Realized CFD wallHeatFlux is only consumed by explicitly CFD-informed modes.
- Fixed-mdot rows impose CFD mdot and therefore are thermal diagnostics only.
- TP targets use CFD core/bulk probe references; TW targets use CFD wall
  references from the local validation refresh.
- Fluid default geometry, default minor losses, default friction closure, and
  1.0 inch insulation are used unless a mode explicitly says otherwise.

## Principal Results

The strongest near-term model-improvement levers remain the cooling/HX heat
removal and heater heat-entry fraction. The lowest cooling RMSE is
`salt2_fit_cooler_imposed_ratio` at `0`
W, but that is a CFD-boundary scaling diagnostic rather than a setup-only
prediction. The best nontrivial cooling candidate in this audit is
`salt2_fit_constant_UA_bulk_drive` with RMSE
`4.638` W. The best all-non-Salt1
heating-leg form is `salt2_fit_constant_heater_efficiency` with RMSE
`0.68` W.

The descriptive association between absolute mdot error and all-probe TP/TW
RMSE across pressure-root non-Salt1 rows has Pearson r=`0.47`
with n=`9`. This correlation is not treated as a
causal model because the sample is small and each boundary mode changes both
heat placement and buoyancy forcing.

## Trends and Conclusions

- `F001` full CFD heat ledger: M1 pressure-root rows reproduce net heat balance but leave large absolute Tmean errors (161.566 K average) and broad mdot errors (35.874 pct average absolute). Matching realized segment heat fluxes alone does not make the current 1D model thermally state-predictive; reference temperature/state closure remains a dominant issue.
- `F002` boundary subset predictivity: Part2 mean all-probe RMSE is 26.972 K and mean absolute mdot error is 10.397 pct; Part3 mean all-probe RMSE is 18.023 K and mean absolute mdot error is 16.826 pct. Heater/cooler-only boundaries improve probe RMSE in this diagnostic ladder but increase mdot error because omitting the test-section heat term changes buoyancy and heat distribution.
- `F003` test-section omission: Omitting the CFD test-section net term changes all-probe RMSE by -8.949 K on average and mdot error by 0.00099 kg/s on average. The test section is not a negligible closure term; it trades thermal-probe agreement against hydraulic buoyancy agreement in the current model form.
- `F004` cooling leg: Current fixed-mdot Fluid cooler RMSE is 102.886 W; Salt2-fit constant-UA bulk-drive RMSE is 4.638 W. Cooling heat removal is the clearest boundary-model improvement lever; a one-parameter Salt2 fit transfers to Salt3/Salt4 much better than the current fixed-mdot airside-HX diagnostic.
- `F005` heating leg: Electrical 1:1 heater RMSE is 24.629 W; Salt2-fit heater-efficiency RMSE is 0.68 W. The CFD heater heat entry fraction is nearly a scalar efficiency over Salt2/Salt4, so heater closure is tractable but still must be setup-only before predictive admission.
- `F006` mdot-temperature association: Across all pressure-root non-Salt1 rows, mdot absolute error and all-probe RMSE have Pearson r=0.47 with n=9. The association is descriptive, not causal: boundary-mode changes move mdot and probe errors together or apart depending on where heat is deposited.

## Interpretation for the Current 1D Model

The current 1D model is not yet a fully predictive setup-only model for the
Salt-family CFD cases. It can now be audited consistently, and several
CFD-informed diagnostics are quantified, but the best-performing rows still
consume realized CFD heat flux or fit a scalar on Salt2. The cooling leg and
heater heat-entry fraction are the most actionable near-term closures because
simple one-parameter Salt2 fits transfer well to Salt3/Salt4 in this diagnostic
exercise.

The test section should not be dropped silently. Omitting it improves TP/TW RMSE
in this ladder but worsens mdot error, which means it redistributes thermal
state and buoyancy error rather than removing a harmless term. The next
scientific step is a setup-only distributed test-section boundary model with
documented wall/ambient assumptions.

## Reproducibility and Appendix

Use `model_config_appendix/` for paper appendix material: it contains copied
Fluid YAML configuration snapshots, resolved scenario/mode tables, and
source/loss assignment tables.
