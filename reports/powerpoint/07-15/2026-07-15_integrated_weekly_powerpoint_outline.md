---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/mdot_temperature_error_report.md
  - work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/presentation_outline.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/report.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_training_testing_oscillation_steady_state/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/README.md
  - .agent/BLOCKERS.md
tags: [thesis-dossier, weekly-presentation, powerpoint-outline, mdot, temperature, boundary-modeling, steady-state, forward-v1]
related:
  - reports/thesis_dossier/README.md
  - reports/powerpoint/07-15/2026-07-15_powerpoint_outline.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-426
date: 2026-07-15
role: Thesis/Presentation/Writer
type: report
status: complete
---
# Integrated PowerPoint Outline: CFD-to-1D Model Audit and Next Gates

Audience: advisor / weekly research update  
Suggested length: 18 main slides plus 5 backup slides  
Core narrative: We moved from scattered CFD/1D comparisons to an admission-gated model-development story. The present model is not final-predictive yet, but we now know which setup and boundary-condition choices control mass flow and TP/TW error, which Salt runs are steady enough to use as evidence, and which gates still block forward-v1 promotion.

## Narrative Spine

1. **Problem:** Build a setup-only 1D model that predicts loop mass flow and TP/TW temperatures from physical inputs, using CFD as reference evidence.
2. **Current status:** Diagnostic CFD-informed replays explain which submodels matter; setup-only prediction is still gated.
3. **Main technical result:** Boundary placement changes both hydraulic and thermal error. Better temperature RMSE does not automatically mean better mdot prediction.
4. **Most actionable model setup finding:** Cooler/HX and heater entry are the strongest near-term setup-only closure targets; the test section must become a physical distributed boundary rather than a compatibility sink.
5. **Trust check:** Selected Salt time series are steady in the final 300 s by TP/TW/mdot oscillation metrics; CLT mean uncertainty is reported but autocorrelation must be respected.
6. **Scientific guardrail:** Recirculating upcomer evidence supports a regime result and diagnostic section-effective quantities, not fitted single-stream `Nu`, `f_D`, or `K`.
7. **Next work:** Convert diagnostic evidence into setup-only scorecards, admit only rows that pass split/runtime/heat-balance/recirculation gates, then rebuild final forward-v1.

## Created Figure Package

- Figure package: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/`
- Manifest: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figure_manifest.csv`
- Advisor-facing glossary: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/term_glossary.csv`
- Equation register: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/equation_register.csv`
- Definitions-first Markdown outline for tomorrow's editable deck work: `reports/powerpoint/07-15/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md`

## Slide 1: Title

**Title:** From CFD Replay to Setup-Only 1D Prediction

**Bullets**

- TAMU molten-salt natural-circulation loop
- Weekly update for July 15, 2026
- Focus: model setup, mdot/temperature error, steady-state trust, and admission gates

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig01_loop_schematic.svg`.

**Speaker Notes**

Open with the thesis-level goal: the CFD is the high-fidelity reference, but the deliverable is a 1D model that can predict `mdot` and temperatures from setup inputs. Say up front that the meeting is not about declaring final forward-v1 done; it is about explaining the evidence chain and the next gates.

## Slide 2: One-Slide Takeaway

**Title:** The Model Is Now Auditable, Not Yet Fully Predictive

**Bullets**

- Boundary-condition choices move `mdot`, mean temperature, loop `dT`, and local probe errors in different directions.
- Best current combined diagnostic mode is M2: `10.397%` mean absolute mdot error and `26.972 K` all-probe RMSE.
- M3 has lower temperature RMSE (`18.023 K`) but worse mdot error (`16.826%`), so heat placement changes circulation physics.
- Full CFD heat-ledger replay M1 still has large errors: `35.874%` mdot error and `159.168 K` all-probe RMSE.
- Final forward-v1 remains blocked because current F6/internal-Nu/thermal rows are diagnostic or candidates, not admitted final fits.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig04_mode_error_bars.svg`.

**Speaker Notes**

This slide should prevent the audience from getting lost in details. The lesson is not "more CFD heat terms always make the 1D model better." The lesson is that heat placement, reference state, and pressure closure interact. We have learned where to work next.

## Slide 3: Definitions, Assumptions, and Evidence Classes

**Title:** Define the Model Modes Before Showing Results

**Bullets**

- **M1:** full CFD segment heat ledger; pressure-root mdot solve. Diagnostic upper-bound replay.
- **M1b:** full CFD heat ledger with fixed CFD mdot. Thermal isolation diagnostic only.
- **M2:** CFD heater + test-section net + cooler; pressure-root mdot solve. Best current mdot diagnostic subset.
- **M3:** CFD heater + cooler only; pressure-root mdot solve. Best current TP/TW RMSE diagnostic subset.
- **PM5/F6:** PM5 is pressure-matched +/-5Q upcomer diagnostic evidence; F6 is a candidate hydraulic/friction scorecard with zero fit-admitted rows today.
- **H1:** legacy shorthand from older task names; do not use it in the talk without spelling out the physical quantity.
- **Core equations:** pressure balance `sum(dp_drive - dp_loss)=0`; cooler/HX `Q=UA DeltaT`; heater `Q_heater=eta P_electrical`; `h_proxy=q''/(Twall-Tbulk)`; `Nu=hD/k`; `SEM=sigma/sqrt(N)` or `sigma/sqrt(N_eff)` for autocorrelated samples.
- **Predictive:** setup geometry, material, BC, and model parameters in; no CFD `mdot`, realized wallHeatFlux, imposed cooler duty, or validation temperatures at runtime.
- **Calibrated:** fit on declared training rows only, then scored on validation/holdout rows without refit.
- **Diagnostic:** uses CFD-realized quantities to localize model-form error or test a hypothesis.
- **Blocked:** row is readable but missing an admission gate, split role, heat-balance pass, or regime validity.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig02_glossary_equations.svg`.

**Speaker Notes**

Start here before using shorthand. Explain that M1/M2/M3 are not final model names; they are diagnostic boundary-condition experiments. Then establish language discipline: many of the strongest-looking numbers are diagnostic because they consume realized CFD heat rates. That does not make them useless; it makes them model-form evidence rather than final prediction evidence.

## Slide 4: Current Model Setup in Plain Language

**Title:** What the 1D Model Is Doing

**Bullets**

- Fluid 1D loop solves circulation from pressure balance and computes segment thermal state.
- Current default model uses Fluid geometry, default minor losses, default friction closure, 1 inch insulation, and current heater/cooler/passive loss handling.
- TP comparisons use CFD core/bulk probe references.
- TW comparisons use CFD wall probe references.
- Boundary modes deliberately change which heat sources/sinks are imposed to isolate model-form error.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig01_loop_schematic.svg`.

**Speaker Notes**

This is the overview the audience needs before the mode names. Explain that model setup means more than one coefficient: geometry, pressure closure, heater input, cooler removal, passive external loss, and sensor/reference definitions all enter. Then say the rest of the deck tests which part matters most.

## Slide 5: Boundary-Condition Ladder

**Title:** The Four Main Diagnostic Modes

**Bullets**

- **M1:** full CFD segment heat ledger; solve mdot from pressure root.
- **M1b:** full CFD heat ledger plus fixed CFD mdot; thermal isolation only.
- **M2:** CFD heater + test-section net + cooler; solve mdot.
- **M3:** CFD heater + cooler only; solve mdot.
- M1/M1b/M2/M3 are diagnostic CFD-informed modes, not setup-only final predictions.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig03_boundary_mode_ladder.svg`.

**Speaker Notes**

Walk left to right. M1 asks: if we place all realized CFD heat exactly, does the current 1D state agree? M2 and M3 ask: what if we reduce the heat ledger to the most important boundary terms? M1b asks thermal-only behavior by fixing mdot, so it should not be described as hydraulic prediction.

## Slide 6: Boundary Ladder Performance

**Title:** More CFD Heat Information Does Not Monotonically Improve the Model

**Bullets**

- M1 full heat ledger: `35.874%` mean absolute mdot error; `159.168 K` all-probe RMSE.
- M2 heater + test-section + cooler: `10.397%` mdot error; `26.972 K` RMSE.
- M3 heater + cooler only: `16.826%` mdot error; `18.023 K` RMSE.
- M2 is the best current combined mdot/temperature diagnostic.
- M3 is thermally better by RMSE but hydraulically worse.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig04_mode_error_bars.svg`.

**Speaker Notes**

This is a central result slide. The audience should hear that the lowest temperature error does not equal the best physical model. M3 gives lower probe RMSE but worsens mdot because dropping the test-section term changes buoyancy forcing.

## Slide 7: Why Full CFD Heat Replay Was Not Enough

**Title:** Matching the Heat Ledger Did Not Fix the State

**Bullets**

- M1 prescribes realized CFD segment heat fluxes.
- It still leaves large thermal-state errors in the current 1D representation.
- This points to reference-state handling, wall/shell drive, energy storage/development, and pressure closure as coupled issues.
- A perfect heat ledger can still be applied through the wrong reduced-order state model.

**Figure Suggestion**

- Better figure to create: per-case M1 error bars for Salt2/Salt3/Salt4 using `case_mode_error_matrix.csv`, with `Tmean error`, `all-probe RMSE`, and `mdot error`.

**Speaker Notes**

This slide rules out an oversimplified story. If exact CFD heat placement was sufficient, M1 would have closed the state. It did not. That tells us the 1D model state and boundary drives need attention, not just total heat accounting.

## Slide 8: Test-Section Tradeoff

**Title:** The Test Section Cannot Be Deleted

**Bullets**

- M2 includes CFD test-section net heat as a compatibility negative source.
- M3 removes that term.
- Removing it improves average all-probe RMSE from `26.972 K` to `18.023 K`.
- But mdot error worsens from `10.397%` to `16.826%`.
- Conclusion: the test section affects buoyancy and circulation state.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig05_test_section_tradeoff.svg`.

**Speaker Notes**

Describe this as a tradeoff, not an improvement. A deleted physical term can make one metric look better while making circulation less correct. The next model should represent the test section as a distributed boundary, not a negative-source workaround.

## Slide 9: The Cooling Leg Is the Largest Boundary Lever

**Title:** Cooler/HX Closure Is the First Setup-Only Target

**Bullets**

- Current fixed-mdot airside-HX cooler model RMSE: `102.886 W`.
- Salt2-fit constant-UA bulk-drive diagnostic RMSE: `4.638 W` across non-Salt1 rows.
- Imposed CFD cooler rows are zero-error by construction and not predictive.
- The useful path is a setup-only UA/effectiveness model scored without realized CFD cooler duty.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg`.

**Speaker Notes**

This slide turns the audit into action. Cooler/HX is where the current model leaves the largest heat-removal mismatch. The diagnostic constant-UA result shows the form is promising, but the final version must be driven by setup inputs.

## Slide 10: Heater Entry Looks Tractable

**Title:** Heater Closure May Be a Low-Dimensional Fix

**Bullets**

- Electrical 1:1 heater entry RMSE: `24.629 W`.
- Salt2-fit constant heater-efficiency diagnostic RMSE: `0.68 W`.
- This suggests a scalar heater-entry or thermal-resistance correction may transfer.
- It still needs a setup-only justification before predictive admission.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg`.

**Speaker Notes**

Use careful wording. The heater is "tractable," not solved. A fitted scalar is a compact diagnostic clue; the thesis-safe claim requires turning it into a physical setup parameter or independent calibration.

## Slide 11: Setup-Predictive Variant Is Now Implemented

**Title:** We Added the Right Hooks for Setup-Only Heat Loss

**Bullets**

- `outer_closure_mode: external_boundary_table` now changes actual passive heat-loss calculation.
- Supports external `h`, `Ta`, `Tsur`, emissivity, coverage multipliers, and drive selectors.
- Supports bulk, pipe-wall, and outer-surface driving-temperature choices.
- Compatible with setup-only `hx_ua_multiplier`.
- Does not use realized CFD wallHeatFlux, CFD mdot, imposed cooler duty, or validation temperatures at runtime.

**Figure Suggestion**

- Better figure to create: configuration-to-physics diagram showing setup dictionaries feeding passive loss and HX UA calculations.

**Speaker Notes**

This is a software/modeling progress slide. The important point is that the previous API blocker has moved from "we cannot express it" to "we can now score it." Avoid saying this admits the model; it only enables the next scorecard.

## Slide 12: mdot Error and TP/TW Error Are Coupled

**Title:** mdot vs Temperature Error Is a Triage View, Not a Fit Objective

**Bullets**

- Across pressure-root non-Salt1 rows: Pearson `r = 0.47`, `n = 9`.
- Boundary modes change heat placement and buoyancy forcing simultaneously.
- The same change can improve TP/TW RMSE while degrading mdot.
- Use this plot to triage model forms, not to fit a single scalar.

**Figure Suggestion**

- Existing figure: `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/figures/mdot_error_vs_probe_rmse.svg`.
- Better figure to create: color points by boundary mode and shape by Salt case.

**Speaker Notes**

This slide is useful for intuition but dangerous if overinterpreted. Say explicitly that correlation is descriptive, because each point changes multiple boundary assumptions.

## Slide 13: Salt Steady-State Trust Check

**Title:** The Consumed Salt Windows Are Steady Enough for This Audit

**Bullets**

- Original oscillation package: 8 selected Salt thermal training/testing rows, `456` stats rows, `96` figures.
- Revised user train-scope package: 12 resolved cases, `684` TP/TW/mdot stats rows, `144` figures.
- All representative TP/TW/mdot rows classify `steady` over the final `300 s`.
- Reported metrics include RMS fluctuation, variance, naive CLT SEM, and autocorrelation-corrected SEM.
- The CLT relation is `SEM = sigma/sqrt(N)`, but CFD autocorrelation inflates uncertainty through `N_eff = N/tau_int`.

**Figure Suggestion**

- Use created summary figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg`.
- Detailed last-window and CLT SEM SVGs remain under `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/figures/`.

**Speaker Notes**

This is the trust slide. We are not claiming the flows are perfectly constant; we quantified the final-window oscillations. Explain RMS and variance plainly: RMS is the typical fluctuation size around the mean; variance is its squared scale. Then explain CLT uncertainty in the mean, with the caveat that CFD time series are autocorrelated.

## Slide 14: What the Steady-State Numbers Look Like

**Title:** Oscillations Are Small Relative to the Mean

**Bullets**

- Salt2 Jin nominal representative final-window RMS:
  TP `0.0236 K`, TW `0.0231 K`, mdot `2.37e-06 kg/s`.
- Salt3 Jin nominal representative final-window RMS:
  TP `0.0341 K`, TW `0.0342 K`, mdot `4.28e-06 kg/s`.
- Native Salt2 validation comparison representative final-window RMS:
  TP `0.0392 K`, TW `0.0412 K`, mdot `3.51e-06 kg/s`.
- Larger perturbation rows remain steady by threshold but show larger thermal RMS, especially Salt4 +/-5Q.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg`.

**Speaker Notes**

Keep this slide short. It gives enough numbers to support the claim that the averages are not dominated by unresolved oscillations. Do not use it to admit internal-Nu or hydraulic coefficients; it is a time-window quality result.

## Slide 15: val_salt2 Is Now a Better External-Test Candidate

**Title:** Native Salt2 Validation Is Unlocked for External Testing

**Bullets**

- `val_salt_test_2_coarse_mesh` refreshed terminal window: `8302` to `8602 s`.
- Refreshed steady-state label: `steady`.
- mdot consensus: `0.01361622898 kg/s`.
- Section heat-loss ledger rows: `14`.
- Admission decision: `external_test_validation_candidate_unlocked`.
- Guardrail: use it for scoring/testing, not fitting.

**Figure Suggestion**

- Better figure to create: side-by-side card comparing Salt2 Jin train vs native `val_salt2` external test:
  mdot, TP/TW RMS, terminal window, heat-loss ledger status.

**Speaker Notes**

This is a real update from earlier. Previously val_salt2 was blocked by missing matching heat-loss ledger context. Now it is a usable external-test candidate, but only if we do not tune on it.

## Slide 16: Internal Nu and F6 Are Review-Ready, Not Admitted

**Title:** Repaired PM5 Data Unlocks Review, Not Coefficient Fits

**Bullets**

- PM5 rows reviewed: `12`; rows with wallHeatFlux: `12`.
- Local `h_proxy = q''/(Twall - Tbulk)` can be computed.
- Positive `h_proxy` rows: `8`.
- F6 fit-admissible rows: `0`.
- Internal-Nu fit-admissible rows: `0`.
- Segment sign/heat-balance pass rows: `0`.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig08_admission_gate_funnel.svg`.

**Speaker Notes**

This is where the audience may expect "we fixed wallHeatFlux, so Nu is solved." Say no: wallHeatFlux lets us compute a diagnostic local heat-transfer proxy, but the regime is recirculating and the sign/heat-balance gate has not admitted rows for single-stream coefficients.

## Slide 17: Scientific Result from Recirculation

**Title:** Recirculation Is a Finding, Not a Failure

**Bullets**

- Current upcomer evidence is recirculating/mixed-convective.
- Single-stream `Nu`, `f_D`, and `K` labels are invalid in that regime.
- Diagnostic section-effective quantities can still be useful.
- True coefficient fitting needs non-recirculating or near-transition anchors.
- Onset remains uncalibrated until ordinary/transition cases exist.

**Figure Suggestion**

- Better figure to create: conceptual flow-regime panel:
  ordinary single-stream -> transition/onset -> recirculating bidirectional section-effective.

**Speaker Notes**

Use this as a positive scientific result. We learned that the current Salt2-4 upcomer regime cannot support ordinary internal-Nu fitting. That prevents a bad thesis claim and defines the next experiment: matched planes at candidate Re 150/200/250 or other transition anchors.

## Slide 18: Current Admission Ledger

**Title:** What Is Trustworthy Today?

**Bullets**

- Setup-legal predictive HX/cooler candidates exist but still await final gates.
- Realized wallHeatFlux replay rows are diagnostic only.
- Imposed cooler-duty rows are diagnostic upper bounds/leakage checks only.
- Negative test-section source rows are compatibility probes, not final BC physics.
- Fitted internal-Nu rows remain `0` admitted fits.
- Final forward-v1 is still `blocked_no_go_final_forward_v1_not_admitted`.

**Figure Suggestion**

- Use `2026-07-15_thermal_row_admission_ledger/row_family_summary.csv`.
- Better figure to create: row-family stacked count chart:
  predictive candidates, diagnostic replay, diagnostic upper bound, blocked internal-Nu.

**Speaker Notes**

This is a defensibility slide. It stops the presentation from sounding more mature than the evidence. The key phrase: "candidate or diagnostic is not the same as admitted."

## Slide 19: Current Blockers Have Narrowed

**Title:** What Still Blocks the Thesis-Strength Model?

**Bullets**

- Closure-QOI mesh/GCI remains not publication-ready.
- Thermal CFD-to-1D parity remains open.
- Predictive heater/cooler/wall-layer submodels remain open but now have implementation hooks.
- Upcomer onset needs more Re/transition anchors.
- F6 friction/Re correction is ready for scorecard but not validated.
- Do not re-report stale blockers: OF13 reconstruction works, mesh families exist, and CFD `rcExternalTemperature` includes radiation.

**Figure Suggestion**

- Better figure to create: blocker board with three columns:
  resolved/stale, narrowed/open, next evidence required.

**Speaker Notes**

This is the weekly management slide. It should be concrete and calming: the blockers are not vague anymore. The next work is identifiable, but final predictive claims remain blocked until these gates pass.

## Slide 20: Proposed Next Week Plan

**Title:** Convert Diagnostics into Setup-Only Scorecards

**Bullets**

- Build setup-only cooler/HX UA or effectiveness scorecard; fit only on declared train rows.
- Build setup-only heater-efficiency or thermal-resistance model.
- Replace test-section compatibility negative source with a distributed physical boundary.
- Use `val_salt2` as external-test candidate without fitting on it.
- Resolve sign/heat-balance gate before any internal-Nu fitting.
- Design non-recirculating or transition matched-plane cases for onset.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig09_forward_v1_roadmap.svg`.

**Speaker Notes**

End with executable work, not just conclusions. The path is not "fit more coefficients"; it is "admit the right rows and convert the diagnostic model forms into setup-only model forms."

## Slide 21: Advisor Decision Requests

**Title:** Decisions Needed

**Bullets**

- Confirm user/requested train reporting scope: Salt1 Jin, Salt2 Jin, Salt3 Jin nominal as train rows; native Salt2 as external validation comparison.
- Decide whether Salt4 nominal remains training by user policy or becomes protected holdout in the next scorecard.
- Approve next scorecard priority: cooler/HX first, heater second, test-section distributed boundary third.
- Approve non-recirculating/onset case design or matched-plane extraction plan for internal-Nu/F6.

**Figure Suggestion**

- Simple decision table with recommended default in bold.

**Speaker Notes**

This slide is intentionally managerial. The technical work has multiple possible split policies; the deck should ask for the split policy before running more scorecards, because fitting decisions depend on it.

## Slide 22: Closing Message

**Title:** The Thesis Story Is Getting Cleaner

**Bullets**

- We now have a reproducible evidence chain from CFD time series to model-form error to admission gates.
- The model setup story is understandable: boundary placement, pressure closure, and thermal state are coupled.
- Steady-state evidence supports the consumed final windows.
- The biggest model improvements are not hidden: cooler/HX, heater entry, distributed test-section boundary, and recirculation-aware closure policy.
- The honest status: final forward-v1 is blocked, but the next gates are concrete.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig09_forward_v1_roadmap.svg`.

**Speaker Notes**

Close by emphasizing progress without overclaiming. The group should leave understanding that today’s work made the model more scientific: it separated what is measured, what is diagnostic, what is predictive, and what remains blocked.

## Backup Slide A: Detailed Boundary Mode Table

**Title:** Boundary Modes and Runtime Input Discipline

**Bullets**

- M1/M1b consume full realized CFD heat ledger.
- M2/M3 consume CFD heater/cooler/test-section terms.
- Fixed-mdot modes consume CFD mdot and isolate thermal behavior only.
- Predictive scorecards must remove CFD mdot, realized wallHeatFlux, imposed cooler duty, and validation temperatures from runtime inputs.

**Figure Suggestion**

- Use `boundary_model_matrix.csv` from setup/BC synthesis.

**Speaker Notes**

Use this if the audience asks why M1 is not "best possible" or why M2/M3 are still diagnostic.

## Backup Slide B: Assumptions and Guardrails

**Title:** Assumptions That Protect the Interpretation

**Bullets**

- Positive CFD wallHeatFlux means heat enters fluid; negative means heat leaves.
- CFD `rcExternalTemperature` includes radiation; do not double-count a separate radiation term.
- Fixed-mdot rows are thermal diagnostics only.
- TP/TW probe target definitions are not interchangeable.
- Salt split policy controls whether rows can be fitted, validated, or only diagnosed.

**Figure Suggestion**

- Use `assumptions_and_guardrails.csv` from setup/BC synthesis.

**Speaker Notes**

This backup is useful for technical challenge questions. It shows the presentation is not hiding sign conventions or runtime-input leakage.

## Backup Slide C: Salt Oscillation Statistics

**Title:** Last-Window RMS, Variance, and SEM

**Bullets**

- RMS fluctuation: `sqrt(mean((x_i - mean(x))^2))`.
- Variance: `mean((x_i - mean(x))^2)`.
- Naive CLT SEM: `sigma/sqrt(N)`.
- Autocorrelation-corrected SEM: `sigma/sqrt(N_eff)`, with `N_eff=N/tau_int`.
- All representative TP/TW/mdot rows in the revised 12-case package classify steady over final `300 s`.

**Figure Suggestion**

- Use created summary figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg`.
- Use detailed CLT SEM SVGs from `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/figures/` if the advisor asks for raw case traces.

**Speaker Notes**

Use this if the advisor asks what "steady" means numerically. Be clear that the SEM curve shows averaging uncertainty; it does not prove independent samples.

## Backup Slide D: val_salt2 External-Test Details

**Title:** Native Salt2 Validation Candidate

**Bullets**

- Terminal window: `8302-8602 s`.
- Steady label refreshed.
- mdot consensus: `0.01361622898 kg/s`.
- Section heat-loss ledger rows: `14`.
- Use: external-test/validation candidate.
- Guardrail: no tuning on this row if it is the blind external test.

**Figure Suggestion**

- Better figure to create: terminal mdot/TP/TW trace and heat-ledger status card for `val_salt2`.

**Speaker Notes**

This backup helps explain why native Salt2 was added after the first oscillation pass and how it should be used.

## Backup Slide E: F6/Internal-Nu Gate Detail

**Title:** Why PM5 WallHeatFlux Does Not Admit Nu

**Bullets**

- `12/12` PM5 rows have wallHeatFlux.
- `h_proxy` is computable.
- `8` positive h_proxy rows.
- `0` sign/heat-balance pass rows.
- `0` F6 fit rows and `0` internal-Nu fit rows.
- Recirculation blocks ordinary single-stream coefficient labels.

**Figure Suggestion**

- Use created figure: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig08_admission_gate_funnel.svg`.

**Speaker Notes**

Use this if someone asks why the new wallHeatFlux extraction did not immediately solve Nu. The correct answer is admission: fields are present, but the row physics and gates still fail for single-stream fitting.

## Created Better-Figure Checklist

1. **Loop schematic with score locations**
   - Inputs: TP/TW probe lists, mdot planes, segment labels.
   - Purpose: orient non-code audience.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig01_loop_schematic.svg`.

2. **Boundary-mode ladder**
   - Inputs: `boundary_model_matrix.csv`, `mode_error_summary.csv`.
   - Purpose: explain M1/M1b/M2/M3 before showing numbers.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig03_boundary_mode_ladder.svg`.

3. **M1/M2/M3 performance bars**
   - Inputs: `mode_error_summary.csv`.
   - Purpose: show mdot/temperature tradeoff cleanly.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig04_mode_error_bars.svg`.

4. **M2 vs M3 test-section tradeoff**
   - Inputs: `case_mode_error_matrix.csv` or existing Part3 increment table.
   - Purpose: make "test section cannot be dropped" visually obvious.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig05_test_section_tradeoff.svg`.

5. **Heater and cooler model-form RMSE bars**
   - Inputs: `heater_cooler_model_form_errors.csv`.
   - Purpose: show why cooler/HX is the first model target and heater is tractable.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig06_heater_cooler_rmse.svg`.

6. **Steady-state RMS / SEM panel**
   - Inputs: `representative_metrics.csv`, CLT SEM SVGs.
   - Purpose: defend use of final-window averages.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig07_steady_state_rms_sem.svg`.

7. **Admission gate funnel for F6/internal-Nu**
   - Inputs: `final_forward_v1_unblock_requirements.csv`, `internal_nu_admission_decision.csv`.
   - Purpose: distinguish "review unlocked" from "fit admitted."
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig08_admission_gate_funnel.svg`.

8. **Forward-v1 roadmap**
   - Inputs: current blocker register and setup-predictive variant status.
   - Purpose: turn the weekly update into next-week execution.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig09_forward_v1_roadmap.svg`.

9. **Definitions/equations slide**
   - Inputs: `term_glossary.csv`, `equation_register.csv`.
   - Purpose: define M1/M1b/M2/M3, PM5, F6, H1, `h_proxy`, `Nu`, `f_D`, `K`, `UA`, and SEM before results.
   - Created: `work_products/2026-07/2026-07-15/2026-07-15_integrated_powerpoint_figures_and_definitions/figures/fig02_glossary_equations.svg`.

## Source Index for Deck Builder

- mdot/temperature report: `work_products/2026-07/2026-07-15/2026-07-15_mdot_temperature_error_report_and_presentation/`
- setup/BC synthesis: `work_products/2026-07/2026-07-15/2026-07-15_setup_bc_model_error_synthesis_report/`
- original oscillation package requested by user: `work_products/2026-07/2026-07-15/2026-07-15_salt_training_testing_oscillation_steady_state/`
- revised oscillation train-scope package: `work_products/2026-07/2026-07-15/2026-07-15_salt_oscillation_user_train_scope/`
- setup-predictive Fluid variant: `work_products/2026-07/2026-07-15/2026-07-15_setup_predictive_heat_loss_fluid_variant/`
- thermal row admission ledger: `work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger/`
- F6/internal-Nu gate: `work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/`
- val_salt2 admission unlock: `work_products/2026-07/2026-07-15/2026-07-15_val_salt2_postprocessing_admission_unlock/`
