---
provenance:
  - reports/powerpoint/07-15/2026-07-15_integrated_weekly_powerpoint_outline.md
  - work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/mdot_temperature_error_report.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/README.md
tags: [thesis-dossier, presentation-outline, definitions-first, figures-only, mdot, temperature, boundary-modeling, steady-state, forward-v1]
task: AGENT-428
date: 2026-07-15
role: Thesis/Presentation/Documentation/Figures
type: outline
status: complete
---
# Definitions-First Weekly Presentation Outline

Audience: advisor / weekly research update  
Format: Markdown outline only. Do not generate or attach a PowerPoint file from this document.  
Figure package: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/`  
Figure manifest: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figure_manifest.csv`

## Narrative Goal

The presentation should not jump straight to M2/M3 or gate acronyms. The first block should teach the advisor the problem setup, the model contract, the shorthand, and the math. Only then should the deck show the results.

Core message: we now have an auditable path from CFD evidence to a setup-only 1D model, but final forward-v1 remains blocked until diagnostic replays become admitted setup-only closures.

## Front-End Story Arc

1. **Mission:** Predict loop circulation and TP/TW temperatures from setup inputs, using CFD as reference evidence.
2. **Model contract:** The final model cannot consume CFD `mdot`, realized wallHeatFlux, imposed cooler duty, or validation temperatures at runtime.
3. **Definitions:** Explain M1/M1b/M2/M3, PM5, F6, H1, `h_proxy`, `Nu`, `f_D`, `K`, `UA`, and SEM before result slides.
4. **Equations:** Show pressure balance, energy closure, heat-transfer proxies, RMSE, and CLT/SEM.
5. **Evidence discipline:** Separate predictive, calibrated, diagnostic, and blocked evidence.
6. **Results:** Boundary placement controls both mdot and TP/TW error; lower temperature RMSE is not automatically better physics.
7. **Next work:** Convert diagnostic model-form clues into setup-only scorecards and admit rows only through gates.

## Slide 1: Title

**Title:** From CFD Replay to Setup-Only 1D Prediction

**Bullets**

- TAMU molten-salt natural-circulation loop.
- Weekly update: model setup, boundary-condition audit, steady-state trust, and admission gates.
- The goal is not to declare final forward-v1 done; the goal is to show what we learned and what must be admitted next.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig01_loop_schematic.svg`

**Speaker Notes**

Open with the thesis-level deliverable: a 1D model that predicts mass flow and temperatures from physical setup inputs. CFD is the reference evidence, not the runtime crutch.

## Slide 2: The Scientific Question

**Title:** What Must the 1D Model Predict?

**Bullets**

- Natural-circulation mdot comes from the balance between buoyancy drive and hydraulic resistance.
- TP and TW temperatures come from energy balance, heat input, cooler removal, passive losses, and wall/fluid coupling.
- A useful model must predict both circulation and thermal state, not just one metric.
- The model must remain honest about which quantities are predictions, calibrated parameters, diagnostics, or blocked claims.

**Figure**

- Reuse `fig01_loop_schematic.svg`.

**Speaker Notes**

This slide frames the whole talk. Avoid shorthand. Explain the loop as physical components: heater, test section/upcomer, cooler/HX, downcomer, walls, probes, and mass-flow measurement plane.

## Slide 3: Runtime Contract

**Title:** What the Final Model Is Allowed to Know

**Bullets**

- Allowed at runtime: geometry, material properties, setup boundary conditions, declared model parameters, heater electrical input, ambient/cooler setup metadata.
- Not allowed at runtime: CFD mdot, realized CFD wallHeatFlux, imposed CFD cooler duty, or validation temperatures.
- Calibrated quantities must be fit only on declared training rows and scored without refit on validation/holdout rows.
- Diagnostic replays are useful for understanding model-form error, but they are not final predictive evidence.

**Figure**

- Use `fig02_glossary_equations.svg` or a simple four-box runtime contract graphic derived from it.

**Speaker Notes**

This is where the advisor should hear the core guardrail. A low-error diagnostic replay is not automatically a predictive model because it may consume reference information that will not exist in a new setup.

## Slide 4: Terms to Define Before Results

**Title:** Shorthand Used in This Update

**Bullets**

- **M1:** full CFD segment heat ledger with pressure-root mdot solve; diagnostic upper-bound replay.
- **M1b:** full CFD heat ledger with fixed CFD mdot; thermal isolation diagnostic only.
- **M2:** CFD heater + test-section net + cooler with pressure-root mdot solve; best current mdot diagnostic.
- **M3 diagnostic:** CFD heater + cooler only with pressure-root mdot solve; best current TP/TW RMSE diagnostic, but it is an ablation, not a predictive model.
- **M3+TS successor:** the next intended predictive form; heater model + cooler/HX model + explicit setup-only distributed test-section heat-loss model.
- **PM5:** pressure-matched +/-5Q upcomer diagnostic evidence.
- **F6:** candidate hydraulic/friction correction scorecard; current fit-admitted rows are zero.
- **TP2 scoring decision:** restore TP2 to the 1D path at the right-downcomer/bottom-horizontal junction only after finite projection gates pass.
- **TW10 scoring decision:** keep TW10 excluded until the forward model predicts an active-HX shell-state temperature.
- **H1:** legacy shorthand from older hydraulic/heat-loss task names; avoid using it unless the physical quantity is spelled out.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig02_glossary_equations.svg`

**Speaker Notes**

This slide fixes the acronym problem. Say explicitly that M1/M2/M3 are experiments about boundary information, not names of final model versions. The requested forward direction is M3+TS: do not delete the test section; replace the CFD compatibility term with a physical setup-only heat-loss model.

## Slide 5: Equations and Modeling Assumptions

**Title:** Minimal Math Behind the Comparisons

**Bullets**

- Pressure-root solve: `sum_i[dp_drive,i(T_i,z_i,mdot) - dp_loss,i(T_i,geometry_i,regime_i,mdot)] = 0`.
- Buoyancy drive is not mdot-only: `dp_drive ~ integral rho(T(s),p,s) g dz(s)`.
- Pressure loss is segment-local: `dp_loss,i ~ [f_i L_i/D_i + K_i] (rho_i V_i^2/2)`.
- Different model forms are expected in heater, cooler/HX, downcomer, upcomer, test section, and junctions.
- Upcomer target form: throughflow pipe component + recirculating convection-cell exchange component.
- Boundary-layer development must be scored by segment, not hidden inside a global multiplier.
- Ordinary `Nu`, `f_D`, and `K` fitting should omit the current recirculating upcomer rows and proceed on other eligible branches with branch-specific model forms.
- Temperature/power error: `RMSE = sqrt(mean((prediction - reference)^2))`.
- Mass-flow error: `mean(abs((mdot_pred - mdot_CFD)/mdot_CFD)) x 100%`.
- Cooler/HX candidate form: `Q = UA DeltaT_drive`.
- Heater candidate form: `Q_heater = eta P_electrical`.
- Diagnostic upcomer proxy: `h_proxy = q''/(T_wall - T_bulk)`.
- Ordinary internal convection label: `Nu = hD/k`, valid only when the flow regime supports single-stream interpretation.
- Mean uncertainty: `SEM = sigma/sqrt(N)` for independent samples; use `SEM = sigma/sqrt(N_eff)` when autocorrelation reduces effective sample count.

**Figure**

- Use `fig02_glossary_equations.svg` as the visual reference; detailed equations live in `equation_register.csv`.

**Speaker Notes**

Keep this clear and not too formal. The advisor needs enough math to understand that mdot is the root variable, but pressure drive is created by the temperature/density field around the loop and pressure loss is built from segment-local terms. This also explains why recirculation invalidates fitted single-stream Nu/f_D/K labels.

## Slide 6: Evidence Classes

**Title:** Predictive, Calibrated, Diagnostic, Blocked

**Bullets**

- **Predictive:** setup-only inputs at runtime; no target leakage.
- **Calibrated:** trained on declared training rows, then scored elsewhere without refit.
- **Diagnostic:** consumes realized CFD quantities to localize model-form error.
- **Blocked:** readable evidence that fails split, runtime, heat-balance, or regime-validity gates.
- Current strongest numbers are mostly diagnostic; that is still scientific progress, but it is not final admission.

**Figure**

- `fig03_boundary_mode_ladder.svg` for mode examples, or `fig08_admission_gate_funnel.svg` for gate examples.

**Speaker Notes**

This slide prevents overclaiming. It also makes the later blocker slides feel like an admission policy rather than a list of failures.

## Slide 7: Boundary-Mode Ladder

**Title:** The Four Diagnostic Boundary Experiments

**Bullets**

- M1 asks whether a full realized CFD heat ledger closes the current 1D state.
- M1b isolates thermal behavior by fixing CFD mdot.
- M2 asks whether heater + test-section + cooler are the controlling realized boundary terms.
- M3 asks whether heater + cooler alone give a cleaner thermal state.
- The predictive successor to M3 must add modeled test-section loss back as setup-only physics.
- All four modes remain diagnostic until their runtime inputs become setup-only and admitted.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig03_boundary_mode_ladder.svg`

**Speaker Notes**

This is the last intro slide before the numbers. Walk left to right and reinforce that the modes change what heat information is supplied to the 1D model.

## Slide 8: One-Slide Takeaway

**Title:** The Model Is Auditable, Not Yet Fully Predictive

**Bullets**

- M2 is the best current combined diagnostic mode: `10.397%` mean absolute mdot error and `26.972 K` all-probe RMSE.
- M3 improves all-probe RMSE to `18.023 K` but worsens mdot error to `16.826%`.
- M1 full heat-ledger replay remains poor: `35.874%` mdot error and `159.168 K` all-probe RMSE.
- Interpretation: heat placement, pressure closure, and thermal state are coupled.
- Final forward-v1 remains blocked because current thermal/hydraulic/internal-Nu evidence is diagnostic or candidate-level, not admitted final fits.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig04_mode_error_bars.svg`

**Speaker Notes**

Now the result slides can use M2/M3 because the audience has already seen the definitions and equations.

## Slide 9: Boundary Ladder Performance

**Title:** More CFD Heat Information Does Not Monotonically Improve the Model

**Bullets**

- M1 full heat ledger: `35.874%` mdot error; `159.168 K` all-probe RMSE.
- M2 heater + test-section + cooler: `10.397%` mdot error; `26.972 K` RMSE.
- M3 heater + cooler only: `16.826%` mdot error; `18.023 K` RMSE.
- M2 is hydraulically better; M3 is thermally cleaner by RMSE.
- The lowest temperature RMSE is not automatically the best circulation physics.

**Figure**

- `fig04_mode_error_bars.svg`

**Speaker Notes**

This is a central technical result. Say clearly that a metric improvement can be a physical tradeoff if it moves buoyancy forcing or pressure closure in the wrong direction.

## Slide 10: Test-Section Tradeoff

**Title:** Move Toward M3 by Modeling the Test Section

**Bullets**

- M2 includes CFD test-section net heat as a diagnostic compatibility term.
- Diagnostic M3 removes that term and therefore acts as an ablation.
- Removing it improves temperature RMSE but worsens mdot error.
- Therefore the test section affects buoyancy and circulation state and cannot be deleted.
- User modeling requirement: the M3 successor must include an explicit test-section heat-loss model.
- Next model step: `Q_test_section_loss_model = f(geometry, h, Ta, Tsur, emissivity, coverage, wall/layer drive)`, not a negative-source workaround.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig05_test_section_tradeoff.svg`

**Speaker Notes**

Describe this as a tradeoff, not an improvement. The old M3 result is evidence that the current compatibility term is wrong or overcorrecting, not evidence that test-section heat loss is zero.

## Slide 11: Heater and Cooler Closure

**Title:** Heater/Cooler Models Are the Nearest Setup-Only Targets

**Bullets**

- Current fixed-mdot airside-HX cooler model RMSE: `102.886 W`.
- Salt2-fit constant-UA bulk-drive cooler diagnostic RMSE: `4.638 W`.
- Electrical 1:1 heater entry RMSE: `24.629 W`.
- Salt2-fit heater-efficiency diagnostic RMSE: `0.68 W`.
- RMSE here means error against CFD-realized component power: cooler heat removal for the cooler rows, heater-to-fluid power for the heater rows.
- `Salt2-fit UA` means `Q_cool = UA DeltaT_bulk`, one scalar fit on Salt2 and scored on Salt3/Salt4 without refit.
- `Salt2-fit eta` means `Q_heater = eta P_electrical`, one scalar fit on Salt2 and scored on Salt3/Salt4 without refit.
- These are promising model-form clues, but final admission requires setup-only justification and validation/holdout scoring.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg`

**Speaker Notes**

Use precise language: cooler/HX and heater look tractable, not solved. The reference is the CFD-realized component power, not TP/TW temperature RMSE. Fitted one-scalar forms are evidence for model-form direction, not final predictive closure.

## Slide 12: Steady-State Trust Check

**Title:** The Consumed Salt Windows Are Steady Enough for This Audit

**Bullets**

- Revised user train-scope package: `12` resolved cases, `684` TP/TW/mdot stats rows, `144` figures.
- All representative TP/TW/mdot rows classify `steady` over the final `300 s`.
- RMS and variance quantify oscillation size in the last window.
- CLT relation `SEM = sigma/sqrt(N)` is reported for mean uncertainty.
- Autocorrelation is handled through corrected effective sample count: `N_eff = N/tau_int`.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg`

**Speaker Notes**

This slide answers whether the averages are meaningful. It does not admit Nu/f_D/K or final hydraulic coefficients; it only supports use of final-window averages for the current audit.

## Slide 13: Representative Oscillation Numbers

**Title:** Oscillations Are Small Relative to the Mean

**Bullets**

- Salt2 Jin nominal RMS: TP `0.0236 K`, TW `0.0231 K`, mdot `2.37e-06 kg/s`.
- Salt3 Jin nominal RMS: TP `0.0341 K`, TW `0.0342 K`, mdot `4.28e-06 kg/s`.
- Salt4 nominal RMS: TP `0.0512 K`, TW `0.0339 K`, mdot `3.83e-05 kg/s`.
- Native Salt2 validation comparison RMS: TP `0.0392 K`, TW `0.0412 K`, mdot `3.51e-06 kg/s`.
- Corrected SEM values are small; remaining uncertainty is not dominated by unresolved oscillation.

**Figure**

- `fig07_steady_state_rms_sem.svg`

**Speaker Notes**

Keep this concise. It supports the time-window trust claim and tees up validation split discussion.

## Slide 14: val_salt2 External-Test Candidate

**Title:** Native Salt2 Validation Is Unlocked for External Testing

**Bullets**

- `val_salt_test_2_coarse_mesh` terminal window: `8302` to `8602 s`.
- Refreshed steady-state label: `steady`.
- mdot consensus: `0.01361622898 kg/s`.
- Section heat-loss ledger rows: `14`.
- Decision: `external_test_validation_candidate_unlocked`.
- Use it for scoring/testing, not fitting.

**Figure**

- Use a small table or card in the eventual deck; no new figure required yet.

**Speaker Notes**

This is a split-policy update. It becomes valuable only if we protect it from tuning.

## Slide 15: Internal Nu and F6 Gate

**Title:** Repaired PM5 Data Unlocks Review, Not Coefficient Fits

**Bullets**

- PM5 rows reviewed: `12`; rows with wallHeatFlux: `12`.
- Local `h_proxy=q''/(Twall-Tbulk)` can be computed.
- Positive `h_proxy` rows: `8`.
- Segment sign/heat-balance pass rows: `0`.
- F6 fit-admissible rows: `0`.
- Internal-Nu fit-admissible rows: `0`.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig08_admission_gate_funnel.svg`

**Speaker Notes**

This should be framed as an admission result. The fields exist, but the row physics and gates do not allow ordinary single-stream coefficient fitting.

## Slide 16: Scientific Result from Recirculation

**Title:** Current Salt2-4 Upcomer Evidence Is Recirculating

**Bullets**

- Current upcomer evidence supports a recirculating regime, not ordinary pipe flow.
- Single-stream `Nu`, `f_D`, and `K` labels are invalid in that regime.
- Immediate analysis plan: omit recirculating upcomer rows from ordinary-pipe coefficient fits and fit/score the other branches using branch-specific model forms.
- This is a scientific result and an admission rule, not merely a failed fit.
- Onset remains uncalibrated until ordinary/transition anchors exist.
- Next evidence: matched plane extraction plus candidate Re 150/200/250 cases.

**Figure**

- `fig08_admission_gate_funnel.svg` or a future matched-plane recirculation schematic.

**Speaker Notes**

This is the key human-facing phrasing: "we learned the current Salt2-4 upcomer regime is recirculating and cannot support fitted internal Nu."

## Slide 17: Current Blockers

**Title:** The Blockers Are Narrow and Named

**Bullets**

- closure-QOI mesh/GCI remains open.
- thermal CFD-to-1D parity remains open.
- predictive heater/cooler/wall-layer submodels remain open but now have implementation hooks.
- upcomer onset needs more Re/transition anchors.
- F6 friction/Re correction is ready for scorecard but not validated.
- Do not re-report stale blockers: OF13 reconstruction works, mesh families exist, and CFD `rcExternalTemperature` includes radiation.

**Figure**

- Use a simple blocker table in the eventual deck; no standalone figure required unless this becomes a management slide.

**Speaker Notes**

This is the management slide. The message is not "everything is blocked"; it is "the remaining gates are identifiable."

## Slide 18: Next Work

**Title:** Convert Diagnostics into Setup-Only Scorecards

**Bullets**

- Build setup-only cooler/HX UA or effectiveness scorecard; fit only on declared training rows.
- Build setup-only heater-efficiency or thermal-resistance model.
- Build `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`: replace the test-section compatibility negative source with a distributed setup-only physical boundary.
- Restore TP2 to the 1D scoring path after finite projection gates; keep TW10 excluded until an active-HX shell-state output exists.
- Score boundary-layer development effects by segment for mdot, TP, TW, Tmean, and loop-Delta-T errors.
- Build the upcomer hybrid model: ordinary throughflow plus recirculating convection-cell exchange, with no fitted single-stream Nu/f_D/K labels in recirculating rows.
- Build a branch-specific ordinary-pipe scorecard that excludes the recirculating upcomer and reports the included/excluded branch mask.
- Score the M3+TS successor against M2 and diagnostic M3 on mdot plus TP/TW errors.
- Use `val_salt2` as external-test candidate without fitting on it.
- Resolve sign/heat-balance gate before internal-Nu fitting.
- Design non-recirculating or transition matched-plane cases for onset.

**Figure**

- `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig09_forward_v1_roadmap.svg`

**Speaker Notes**

End with executable work. The next phase is not fitting more coefficients indiscriminately; it is admitting the right rows and converting diagnostic clues into setup-only model forms.

## Slide 19: Decisions Needed

**Title:** Advisor Decisions for the Next Scorecard

**Bullets**

- Confirm train/reporting scope: Salt1 Jin, Salt2 Jin, Salt3 Jin nominal as train rows; native Salt2 as external validation comparison.
- Decide whether Salt4 nominal remains training by user policy or becomes protected holdout in the next scorecard.
- Prioritize scorecard sequence: cooler/HX first, heater second, distributed test-section boundary third, then M3+TS end-to-end scoring.
- Approve non-recirculating/onset case design or matched-plane extraction plan for internal-Nu/F6.

**Figure**

- Decision table; no generated figure required yet.

**Speaker Notes**

This slide is deliberately managerial. Split policy must be explicit before more scorecards are run.

## Slide 20: Closing

**Title:** The Thesis Story Is Getting Cleaner

**Bullets**

- The evidence chain is now reproducible: CFD time series -> model-form error -> admission gates.
- Boundary placement, pressure closure, and thermal state are coupled.
- Steady-state evidence supports the consumed final windows.
- The biggest model improvements are visible: cooler/HX, heater entry, distributed test-section boundary, and recirculation-aware closure policy.
- Honest status: final forward-v1 remains blocked, but the next gates are concrete.

**Figure**

- `fig09_forward_v1_roadmap.svg`

**Speaker Notes**

Close by emphasizing progress without overclaiming. The story is stronger because the deck distinguishes what is predictive, calibrated, diagnostic, and blocked.

## Backup A: Equations

- `sum_i[dp_drive,i(T_i,z_i,mdot) - dp_loss,i(T_i,geometry_i,regime_i,mdot)] = 0`
- `dp_drive ~ integral rho(T(s),p,s) g dz(s)`
- `dp_loss,i ~ [f_i L_i/D_i + K_i] (rho_i V_i^2/2)`
- `Q = UA DeltaT_drive`
- `Q_heater = eta P_electrical`
- `h_proxy = q''/(T_wall - T_bulk)`
- `Nu = hD/k`
- `RMSE = sqrt(mean((prediction-reference)^2))`
- `SEM = sigma/sqrt(N)` and `SEM_corrected = sigma/sqrt(N_eff)`

## Backup B: Figure Index

- Loop schematic: `fig01_loop_schematic.svg`
- Definitions/equations: `fig02_glossary_equations.svg`
- Boundary ladder: `fig03_boundary_mode_ladder.svg`
- Mode error bars: `fig04_mode_error_bars.svg`
- M2/M3 tradeoff: `fig05_test_section_tradeoff.svg`
- Heater/cooler RMSE: `fig06_heater_cooler_rmse.svg`
- Steady-state RMS/SEM: `fig07_steady_state_rms_sem.svg`
- Admission funnel: `fig08_admission_gate_funnel.svg`
- Roadmap: `fig09_forward_v1_roadmap.svg`
