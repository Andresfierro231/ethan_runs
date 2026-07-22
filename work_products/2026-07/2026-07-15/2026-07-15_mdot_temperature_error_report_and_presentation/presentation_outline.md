# Presentation Outline: mdot Error vs TP/TW Temperature Error

## Slide 1: Audit Question and Takeaway

- Question: how do mdot errors compare with TP/TW temperature-probe errors?
- The current 1D model is auditable, but not yet setup-only predictive.
- Boundary placement drives a hydraulic/thermal tradeoff.

Suggested figure: Create title slide with small schematic of 1D loop plus TP/TW/mdot labels.

Speaker notes:
Open by framing this as a model audit, not a claim of final predictive closure. Emphasize that the study separates diagnostic CFD-informed rows from setup-only predictive rows.

## Slide 2: Case Split and Admission Discipline

- Salt2 is training; Salt3 is validation; Salt4 is holdout.
- Salt1 is diagnostic/context only in this audit.
- No closure is fit on Salt3 or Salt4.

Suggested figure: Table from case_admission_and_use_table.csv.

Speaker notes:
This slide prevents overclaiming. Salt1 appears in the package, but heat-flux modes are blocked because a current admitted Salt1 patch heat ledger was not available in the consumed source set.

## Slide 3: Boundary-Condition Ladder

- M1: full CFD segment heat ledger, pressure-root mdot.
- M1b: same heat ledger, fixed CFD mdot; thermal diagnostic only.
- M2: CFD heater + test-section net + cooler, pressure-root mdot.
- M3: CFD heater + cooler only, pressure-root mdot.

Suggested figure: Schematic evidence ladder from model_mode_matrix.csv.

Speaker notes:
Explain that the ladder intentionally becomes less complete in heat-boundary information to expose what each boundary class controls.

## Slide 4: What Is Compared

- TP probes: TP1, TP2, TP3, TP4, TP5, TP6.
- TW probes: TW1, TW10, TW11, TW2, TW3, TW4, TW5, TW6, TW7, TW8, TW9.
- TP targets are CFD core/bulk references; TW targets are CFD wall references.
- mdot is solved from pressure balance except fixed-mdot diagnostics.

Suggested figure: Create annotated loop diagram with TP/TW markers.

Speaker notes:
Make clear which TP and TW families are scored. This avoids ambiguity about whether we are comparing wall temperatures, bulk temperatures, or mixed references.

## Slide 5: Boundary Ladder Performance

- M1: mean abs mdot error 35.874 pct; all-probe RMSE 159.168 K.
- M2: mean abs mdot error 10.397 pct; all-probe RMSE 26.972 K.
- M3: mean abs mdot error 16.826 pct; all-probe RMSE 18.023 K.

Suggested figure: Grouped bar chart from boundary_mode_performance_summary.csv.

Speaker notes:
This is the core performance slide. The important story is that the lowest thermal-probe RMSE is not the same as the lowest mdot error.

## Slide 6: Full CFD Heat Ledger Is Not Enough

- M1 prescribes realized CFD segment heat fluxes.
- Large Tmean and probe errors remain.
- Reference state and model-form issues remain even when net heat is matched.

Suggested figure: M1 per-case bars from case_mode_error_table.csv.

Speaker notes:
Use this to rule out a simplistic explanation that the model only needs the right total heat input/output.

## Slide 7: Test Section Tradeoff

- Part3 omits the CFD test-section net term.
- Probe RMSE improves on average.
- mdot error worsens on average.
- Conclusion: the test section is not negligible; it needs a physical boundary model.

Suggested figure: Part2 vs Part3 paired bars from part3_test_section_error_increment.csv.

Speaker notes:
Describe this as a tradeoff, not an improvement. A boundary deletion can make one score better while degrading circulation physics.

## Slide 8: Cooling Leg Is the Largest Boundary Lever

- Current fixed-mdot cooler RMSE is about 102.9 W.
- Salt2-fit constant-UA bulk-drive RMSE is about 4.64 W.
- A setup-only HX/cooler UA/effectiveness model is the next priority.

Suggested figure: Bar chart from part4_cooling_rmse_summary.csv.

Speaker notes:
This slide motivates concrete model development. Do not present the zero-error imposed-CFD cooler row as predictive.

## Slide 9: Heater Entry Is Tractable

- Electrical 1:1 heater RMSE is about 24.6 W.
- Salt2-fit heater efficiency RMSE is about 0.68 W.
- A scalar heater-efficiency model may transfer, but must be setup-only.

Suggested figure: Bar chart from part5_heating_rmse_summary.csv.

Speaker notes:
The heater is less complex than the cooler in this diagnostic exercise. The scientific requirement is to justify the scalar from setup or independent evidence.

## Slide 10: mdot Error vs Temperature Error

- Pearson r=0.47, n=9 across pressure-root non-Salt1 rows.
- Association is descriptive, not causal.
- Use as a triage view, not a fitting objective.

Suggested figure: Existing figure: work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/figures/mdot_error_vs_probe_rmse.svg.

Speaker notes:
This plot helps communicate coupling. Stress that each point changes boundary conditions, so correlation is not a physical law.

## Slide 11: Assumptions That Matter

- Positive wallHeatFlux heats the fluid; negative cools it.
- CFD rcExternalTemperature includes radiation; no separate qr term is added.
- Realized CFD wallHeatFlux rows are diagnostic unless explicitly declared CFD-informed.
- Fixed-mdot rows are thermal diagnostics only.

Suggested figure: Assumption table from study_assumption_register.csv.

Speaker notes:
This slide is for scientific defensibility. It should be included in a technical presentation or appendix.

## Slide 12: What To Do Next

- Build setup-only cooler/HX model and rescore Salt3/Salt4.
- Build setup-only heater efficiency or resistance model.
- Replace test-section compatibility sink with a distributed boundary model.
- Audit reference-state handling before using full heat-ledger rows as validation.

Suggested figure: Roadmap graphic with three branches: cooler, heater, test section.

Speaker notes:
End with executable next steps, not only conclusions. The model audit has identified where development should focus.
