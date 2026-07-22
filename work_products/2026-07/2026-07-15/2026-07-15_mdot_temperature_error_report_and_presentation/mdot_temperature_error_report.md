# mdot Error vs TP/TW Temperature Error: Report-Ready Synthesis

## Executive Summary

This report synthesizes the AGENT-360 audit of the current 1D model against
Salt-family CFD. The audit compares mass-flow error (`mdot`) with TP/TW
temperature-probe error under a ladder of boundary-condition modes. The central
result is that hydraulic and thermal errors are coupled, but not in a way that
can be collapsed to a single scalar correction. Boundary choices move mdot,
mean thermal state, loop temperature rise, and local probe errors in different
directions.

The best current diagnostic boundary subset is **M2**, which imposes CFD heater
heat entry, CFD test-section net heat, and CFD cooler heat removal while solving
mdot from pressure balance. Across Salt2/Salt3/Salt4, M2 has mean absolute mdot
error `10.397` pct and mean all-probe RMSE
`26.972` K. Omitting the test-section term in **M3**
improves mean all-probe RMSE to `18.023` K but worsens
mean absolute mdot error to `16.826` pct. Full realized
segment heat flux in **M1** does not solve the state problem: mean absolute mdot
error is `35.874` pct and mean all-probe RMSE is
`159.168` K.

The highest-leverage model improvements are the cooling/HX closure and heater
heat-entry fraction. The current fixed-mdot cooler model has all-non-Salt1 RMSE
`102.886` W, while a Salt2-fit constant-UA
bulk-drive diagnostic has RMSE `4.638` W. The
current electrical 1:1 heater model has RMSE `24.629`
W, while a Salt2-fit scalar heater efficiency has RMSE `0.68`
W. These are strong diagnostic signals, but the final predictive model must use
setup-only boundary parameters rather than realized CFD heat rates.

## Study Design

The study uses Salt2 as the training row, Salt3 as validation, and Salt4 as
holdout. Salt1 is diagnostic/context only because the consumed source set lacks
a current admitted Salt1 patch heat ledger. No closure should be fitted on
Salt3 or Salt4.

The temperature comparison uses TP probes `TP1, TP2, TP3, TP4, TP5, TP6` and TW
probes `TW1, TW10, TW11, TW2, TW3, TW4, TW5, TW6, TW7, TW8, TW9`. TP targets are CFD core/bulk probe
references. TW targets are CFD wall references from the local validation
refresh. The audit generated `204` sensor
error rows, `16` model-result rows, and
`23` heat-score rows.

## Boundary-Condition and Model Modes

| Mode | Part | Predictivity class | Uses CFD mdot at runtime | Uses realized CFD wallHeatFlux at runtime | Mean abs mdot error pct | Mean all-probe RMSE K |
| --- | --- | --- | --- | --- | ---: | ---: |
| `M1_full_cfd_segment_heat_flux_pressure_root` | part1 | diagnostic_cfd_informed_upper_bound | no | yes | 35.874 | 159.168 |
| `M1b_full_cfd_segment_heat_flux_fixed_mdot` | part1 | diagnostic_fixed_mdot_thermal_isolation | yes | yes |  | 152.212 |
| `M2_cfd_heater_test_section_cooler_pressure_root` | part2 | diagnostic_cfd_informed_boundary_subset | no | yes | 10.397 | 26.972 |
| `M3_cfd_heater_cooler_pressure_root` | part3 | diagnostic_cfd_informed_boundary_subset | no | yes | 16.826 | 18.023 |

Important interpretation:

- M1 and M1b are diagnostic upper bounds because they prescribe realized CFD
  segment heat ledgers.
- M1b, Part4, and Part5 fixed-mdot rows isolate thermal behavior only; they are
  not hydraulic predictions.
- M2 and M3 remain CFD-informed diagnostic boundary subsets because they impose
  CFD heater/cooler/test-section heat terms.
- A setup-only predictive row must not consume CFD mdot, realized CFD
  wallHeatFlux, CFD cooler duty, CFD heater heat entry, or validation
  temperatures at runtime.

## Results by Study Part

### Part 1: Full CFD segment heat fluxes

Matching the full realized CFD segment heat ledger is not sufficient. M1
pressure-root rows reproduce net heat balance but still leave large state
errors. This means the problem is not only total heat accounting; reference
temperature handling, boundary placement, passive losses, and hydraulic
pressure closure still matter.

M1b fixes mdot to the CFD value and therefore should not be read as hydraulic
predictivity. It is useful because it shows that even with CFD mdot and full
realized heat rates, thermal state can remain badly biased when the model's
state/reference handling is inconsistent.

### Part 2: CFD heater + test-section net + cooler

M2 is the best current balance between mdot and probe error among pressure-root
CFD-informed modes. It keeps the test-section net term and solves mdot. The
mean all-probe RMSE is `26.972` K and mean absolute mdot
error is `10.397` pct across Salt2/Salt3/Salt4.

The caveat is scientific, not clerical: the test-section term is currently
encoded as a compatibility negative source, not as a first-class distributed
external boundary model.

### Part 3: CFD heater + cooler only

M3 removes the CFD test-section net term. Probe RMSE improves, but mdot error
worsens. This is the clearest evidence that the test section cannot simply be
dropped. In the current model, removing it redistributes thermal and buoyancy
error rather than eliminating an irrelevant term.

### Part 4: Cooling leg heat removed

The cooling leg is the strongest near-term boundary-model lever. The current
fixed-mdot Fluid cooler model under-predicts heat removal with RMSE
`102.886` W. The Salt2-fit constant-UA bulk-drive
diagnostic transfers to Salt3/Salt4 with all-non-Salt1 RMSE
`4.638` W. This suggests the model needs a better
setup-only cooler/HX UA or effectiveness representation.

### Part 5: Heating leg heat added

The current electrical 1:1 heater entry has RMSE
`24.629` W. The Salt2-fit scalar heater-efficiency
diagnostic has RMSE `0.68` W. The heater boundary
therefore looks tractable, but the fitted scalar must be converted into a
documented setup-only heater efficiency or thermal-resistance model before it
can be used predictively.

## mdot vs Temperature-Error Correlation

Across pressure-root non-Salt1 rows, the audit reports Pearson r=
`0.47` with n=`9` between absolute
mdot error and all-probe RMSE. This is a triage statistic, not a causal model.
Boundary modes change heat placement and buoyancy forcing at the same time, so
mdot and temperature errors can move together or trade off depending on the
mode.

## Assumptions and Guardrails

- `A001` wallHeatFlux sign: Positive CFD wallHeatFlux means heat enters the fluid; negative means heat leaves the fluid. Risk: Wrong sign reverses heater/cooler/test-section interpretation.
- `A002` radiation: CFD rcExternalTemperature includes radiation in total wallHeatFlux; current CFD exports no separate qr. Risk: Do not double count radiation as a separate 1D term when prescribing CFD heat flux.
- `A003` runtime discipline: Realized CFD wallHeatFlux is diagnostic evidence unless a mode explicitly declares itself CFD-informed. Risk: CFD-informed modes are not final setup-only predictions.
- `A004` fixed mdot: Fixed-mdot modes impose CFD mdot and therefore isolate thermal/sensor behavior only. Risk: Do not use fixed-mdot rows as hydraulic predictivity evidence.
- `A005` test-section sink encoding: For M2, CFD test-section net loss is encoded as a negative source to preserve current Fluid passive boundary behavior. Risk: This is a compatibility representation, not a first-class external boundary model.
- `A006` sensor targets: TP targets use CFD core/bulk probe references; TW targets use CFD wall-area-average probe references. Risk: Sensor-coordinate uncertainty remains a score limitation.
- `A007` split discipline: Salt2 is the current train row, Salt3 validation, Salt4 holdout, and Salt1 diagnostic/context only. Risk: No model form is fit on validation or holdout rows.
- `A008` Salt1: Salt1 has sensor and Fluid setup references but lacks a current admitted Salt1 patch heat ledger in the consumed source set. Risk: Salt1 is reported as diagnostic and blocked for CFD heat-flux modes.
- `A009` closures: Fluid default geometry, default MinorLosses, default friction closure, 1.0 inch insulation, and current solver thermal model are used unless the mode says otherwise. Risk: This is an audit of the current 1D model, not a new closure calibration.

## Conclusions

- **F001 full CFD heat ledger.** M1 pressure-root rows reproduce net heat balance but leave large absolute Tmean errors (161.566 K average) and broad mdot errors (35.874 pct average absolute). Interpretation: Matching realized segment heat fluxes alone does not make the current 1D model thermally state-predictive; reference temperature/state closure remains a dominant issue. Next: Audit start-temperature/reference-state handling and segment energy accumulation before treating full heat-ledger rows as validation evidence.
- **F002 boundary subset predictivity.** Part2 mean all-probe RMSE is 26.972 K and mean absolute mdot error is 10.397 pct; Part3 mean all-probe RMSE is 18.023 K and mean absolute mdot error is 16.826 pct. Interpretation: Heater/cooler-only boundaries improve probe RMSE in this diagnostic ladder but increase mdot error because omitting the test-section heat term changes buoyancy and heat distribution. Next: Model the test-section as a physical distributed boundary rather than a compatibility negative source.
- **F003 test-section omission.** Omitting the CFD test-section net term changes all-probe RMSE by -8.949 K on average and mdot error by 0.00099 kg/s on average. Interpretation: The test section is not a negligible closure term; it trades thermal-probe agreement against hydraulic buoyancy agreement in the current model form. Next: Extract/localize test-section wall heat flux and compare a distributed sink, passive ambient loss, and zero-test-section assumptions.
- **F004 cooling leg.** Current fixed-mdot Fluid cooler RMSE is 102.886 W; Salt2-fit constant-UA bulk-drive RMSE is 4.638 W. Interpretation: Cooling heat removal is the clearest boundary-model improvement lever; a one-parameter Salt2 fit transfers to Salt3/Salt4 much better than the current fixed-mdot airside-HX diagnostic. Next: Promote a setup-only cooler model using geometry/air-flow inputs, then score Salt3/Salt4 without realized CFD cooler heat.
- **F005 heating leg.** Electrical 1:1 heater RMSE is 24.629 W; Salt2-fit heater-efficiency RMSE is 0.68 W. Interpretation: The CFD heater heat entry fraction is nearly a scalar efficiency over Salt2/Salt4, so heater closure is tractable but still must be setup-only before predictive admission. Next: Replace electrical 1:1 heater entry with a documented heater-efficiency or thermal-resistance model and hold Salt4 as a final blind check.
- **F006 mdot-temperature association.** Across all pressure-root non-Salt1 rows, mdot absolute error and all-probe RMSE have Pearson r=0.47 with n=9. Interpretation: The association is descriptive, not causal: boundary-mode changes move mdot and probe errors together or apart depending on where heat is deposited. Next: Use the correlation table as a triage view, not a fitting objective, until more setup-only cases exist.

## Recommended Next Work

1. Promote the cooling model from diagnostic Salt2-fit evidence to a setup-only
   HX/cooler formulation, then score Salt3 and Salt4 without realized CFD cooler
   heat.
2. Replace electrical 1:1 heater entry with a setup-documented heater
   efficiency or thermal-resistance model.
3. Build a first-class distributed test-section boundary model. Do not keep the
   compatibility negative-source encoding as the final scientific model.
4. Audit reference-state/start-temperature handling before interpreting full
   CFD heat-ledger rows as validation evidence.
5. Keep the mdot-vs-temperature-error correlation as a diagnostic plot, not a
   fitting objective, until more setup-only cases exist.

## Reproducibility

Primary source package: `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit`.

Appendix configuration snapshots are in
`work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/model_config_appendix`. The most important appendix files are
`resolved_scenario_config_by_mode.csv`, `closure_terms_by_mode.csv`,
`segment_source_loss_assignment_by_mode.csv`, `cases.yaml`, `campaigns.yaml`,
and `scenarios.yaml`.
