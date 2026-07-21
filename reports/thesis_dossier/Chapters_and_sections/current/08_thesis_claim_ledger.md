---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/README.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
tags: [thesis-section, current-section, claim-ledger, evidence-ledger, split-policy, caveats]
related:
  - TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
task: AGENT-516
date: 2026-07-17
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Thesis Claim Ledger

## Purpose

This ledger is the thesis claim control table. It maps each major claim to its
evidence, split role, blocker or admission state, figure/table source, and
caveat. Use it before writing results prose: if a claim is not represented here,
it needs a row or it should stay out of the thesis.

The ledger deliberately separates four categories:

- thesis-ready method claims;
- admitted or partially admitted model claims;
- diagnostic evidence that may motivate a model form but cannot be used as a
  fitted predictive coefficient;
- blocked or future claims.

## Claim Table

| ID | Thesis claim | Evidence | Split role | Blocker/status | Figure/table source | Caveat or use boundary |
| --- | --- | --- | --- | --- | --- | --- |
| CL-01 | Ethan OpenFOAM CFD is the current high-fidelity reference, not experimental validation. | Dossier methodology, case admission notes, final split policy. | All rows may reference CFD as the comparison target according to their role. | Thesis-ready context. | `01_modeling_approach.md`; `03_split_policy_and_evidence_classes.md`. | Do not say the 1D model is experimentally validated unless independent experiment comparisons are added. |
| CL-02 | The core contribution is a provenance-controlled CFD-to-1D closure workflow, not a single tuned coefficient. | Current methodology, model form, junction-aware, endpoint ladder sections. | Applies to training, support, holdout, and external evidence. | Thesis-ready method claim. | `01_modeling_approach.md`; `06_intermediate_model_forms_and_endpoint_strategy.md`. | Keep coefficient status attached to each row; do not collapse the ledger into one global correction factor. |
| CL-03 | The final 1D target is steady `fluid+walls`, not a fluid-only heat-leak model. | `fluid+walls` section and operational model-form note. | Training rows may fit admitted terms; score rows may only evaluate frozen terms. | Thesis-ready model-form claim; implementation still has blocked submodels. | `02_model_form_fluid_walls.md`; `09_fluid_walls_segment_atlas.md`. | Do not introduce transient storage terms in the current steady thesis model without a later reopening note. |
| CL-04 | Predictive runtime modes must use setup inputs only. | Split policy and scorecard shell runtime audits. | Final training fits admitted terms; holdout and external rows score only. | Thesis-ready guardrail. | `03_split_policy_and_evidence_classes.md`; `2026-07-17_final_predictive_scorecard_shell/README.md`. | CFD `mdot`, realized `wallHeatFlux`, imposed CFD cooler duty, pressure loss from the scored row, and validation temperatures are forbidden runtime inputs. |
| CL-05 | The canonical final split is Salt1-4 nominal training, Salt1 +/-10Q and Salt4 +/-5Q support, Salt2 +/-5Q holdout/testing, and `val_salt2` external test. | Canonical split policy package and dossier. | Locked split. | Thesis-ready split claim. | `operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md`. | Future +/-10Q and new CFD rows require terminal harvest and admission before scoring. |
| CL-06 | Salt1 is promoted as primary/final training evidence, while older Salt2/Salt3/Salt4-only language is dated method-development context. | Salt1 schema/admission promotion packages and updated dossier split. | Final training. | Current split state. | `work_products/2026-07/2026-07-17/2026-07-17_predict_salt1_schema_promotion/README.md`; `03_split_policy_and_evidence_classes.md`. | Do not silently use stale split prose from dated notes. |
| CL-07 | Salt2 +/-5Q rows are holdout/testing-only. | Salt2 +/-5Q readiness ledger. | Holdout/testing. | Fit/tune/model-selection forbidden. | `2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/fluid_walls_readiness_ledger.csv`. | These rows can score a frozen model or provide labeled diagnostic evidence, not train coefficients. |
| CL-08 | `val_salt2` is external-test-only. | `val_salt2` readiness, patch heat, junction split, and score shell packages. | External test. | Fit/tune/model-selection forbidden. | `2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md`; `2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md`. | Use as independent scoring/context evidence; do not reclassify into training. |
| CL-09 | Heater and cooler/HX setup-facing boundary evidence is more mature than passive wall/test-section closure. | Boundary submodel, cooler, endpoint, and wall/test-section sections. | Training evidence for admitted boundary terms; score rows must use frozen terms. | Partially admitted; wall/test-section remains open. | `06_intermediate_model_forms_and_endpoint_strategy.md`; `07_wall_test_section_coupled_score_and_physics_plan.md`. | Do not let admitted heater/cooler evidence imply all thermal boundary physics is admitted. |
| CL-10 | PB2/PB3 wall/test-section distribution candidates are diagnostic falsification evidence, not admitted closures. | Coupled wall/test-section score: 12/12 rows completed; 0/4 candidates admitted; mdot improves while all-probe/TW worsen by about 35-49 K. | Salt2-trained candidate screens, Salt3 validation, Salt4 holdout. | `predictive-wall-test-section-submodels` remains open. | `07_wall_test_section_coupled_score_and_physics_plan.md`; `2026-07-17_wall_test_section_distribution_ladder/coupled_delta_vs_m3.csv`. | The result narrows the blocker to temperature-shape/source-placement/coupling physics; it does not admit a passive hA distribution. |
| CL-11 | Segment-only ledgers miss structured local heat losses. | Salt2-4 junction split and `val_salt2` junction/stub ledger. | Salt2-4 mainline context plus `val_salt2` external evidence. | Thesis-ready model-form motivation; not a runtime training input. | `05_junction_aware_ledgers.md`; `val_salt2_junction_split_heat_ledger.csv`. | Realized junction heat is scoring/diagnostic target evidence unless a setup-facing runtime circuit is admitted. |
| CL-12 | `val_salt2` has about 40.93 W junction/stub heat loss across four buckets. | `05_junction_aware_ledgers.md` reports `40.926087 W`. | External-test evidence. | Thesis-useful local-role evidence. | `05_junction_aware_ledgers.md`; `2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_junction_split_heat_ledger.csv`. | Do not fit or tune on this value; use it to support the need for local junction/stub ownership. |
| CL-13 | Corner pressure K remains diagnostic, not admitted. | Corner pressure reviews report 0 fit-admitted rows; the July 20 two-tap recirculation package confirms current `corner_lower_right` rows are hydrostatic/buoyancy-dominated in static pressure, reverse-flow blocked, apparent-cluster-only, and missing same-QOI UQ. | Diagnostic across relevant cases; external score context. | Ordinary `component_K` remains blocked by pressure basis, isolation, recirculation, straight-loss/development separation, and mesh/time UQ gates. | `05_junction_aware_ledgers.md`; `13_two_tap_recirc_section_effective_pressure_model.md`; `2026-07-20_two_tap_recirc_section_effective_model/README.md`. | Do not use static apparent K as a locally buoyancy-corrected component coefficient; negative or diagnostic residuals are model-form evidence, not pressure-gain or K-admission claims. |
| CL-14 | The upcomer needs a hybrid throughflow plus recirculation-cell model lane. | Upcomer recirculation section, PM5/PM10 readiness, recirculation feature packages. | Training/support/holdout/external labels preserved. | `upcomer-onset-data-sparsity` remains open. | `04_upcomer_recirculation_modeling.md`; `2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/pm5_recirc_readiness_ledger.csv`. | Ordinary single-stream `Nu`, `f_D`, or `K` labels are invalid in recirculation-dominated rows. |
| CL-15 | F6/internal-Nu recorrection remains open and narrowed; production should stay on the currently admitted hydraulic form unless replaced by a gated candidate. | F6 resolution and lit-review hydraulic model-form packages. | Training candidates only after gate clearance; support/holdout external remain score-only. | `f6-friction-re-correction` open/narrowed. | `2026-07-17_f6_recorrection_resolution_plan/README.md`; `2026-07-17_f6_litrev_hydraulic_model_form_ladder/README.md`. | Do not promote PM5/upcomer rows into ordinary-pipe coefficients while recirculation/admission gates fail. |
| CL-16 | Current pressure rows are diagnostic; no fit-admitted pressure coefficient rows are available in the Salt2 +/-5Q/`val_salt2` readiness ledger. | Readiness package: 18 pressure rows, 0 fit-admitted pressure coefficient rows, 0 rows with admitted pressure model status. | Holdout/external evidence only in that package. | Diagnostic. | `2026-07-17_salt2_pm5q_val_salt2_readiness_ledger/README.md`; `pressure_readiness_ledger.csv`. | Use for pressure attribution and blocker diagnosis, not coefficient fitting. |
| CL-17 | Internal HTC/Nu rows must not absorb heat-loss, radiation, cooler, passive wall, or heater-placement errors. | Thermal closure policy, mesh/GCI, property sensitivity, wall/test-section falsification. | Training only after thermal gates; score rows are evaluation only. | Thermal coefficient admission remains gated. | `02_model_form_fluid_walls.md`; `10_uncertainty_chapter_package.md`. | Separate wall/external/source/cooler residuals before admitting internal `Nu`. |
| CL-18 | Radiation is embedded in realized CFD `rcExternalTemperature`/wall-heat-flux evidence and must not be double-counted. | Thermal boundary/radiation notes and model form section. | Diagnostic target evidence unless runtime external-boundary model is setup-facing and admitted. | Thesis-ready guardrail. | `02_model_form_fluid_walls.md`; `operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md`. | Predictive runtime models need setup `Ta`, `Tsur`, emissivity, and external resistance inputs; not realized scored-row fluxes. |
| CL-19 | Time-window uncertainty exists and should be reported separately from model error. | Time-series uncertainty story for Salt2-4. | Applies to CFD reference targets and score uncertainty. | Thesis-ready uncertainty component. | `2026-07-13_time_series_uncertainty_story/mainline_salt234_uncertainty_components.csv`; `10_uncertainty_chapter_package.md`. | Do not use steady-window SEM/drift to excuse structural model bias without showing scale. |
| CL-20 | Mesh/GCI status is a final-use disposition, not a blanket solved problem. | Mesh/GCI resolution tables show many closure rows not publication-ready or not fit-admissible. | Training/admission gates; diagnostic rows may remain useful. | Conservative: no broad publication-grade coefficient claim. | `2026-07-16_closure_qoi_mesh_gci_resolution/mesh_gci_gate_for_admitted_candidates.csv`. | Say which QOI row is admitted/diagnostic/blocked; avoid "GCI resolved" without row scope. |
| CL-21 | Property lane choice precedes friction and thermal closure fitting. | Property sensitivity summary: property modes shift Re, Pr, and Gz substantially while heat residuals are held for comparison. | Training sensitivity and model selection must obey split. | Thesis-ready model-choice claim. | `2026-07-13_litrev_property_sensitivity/property_sensitivity_summary.csv`. | Do not fit closures under one property lane and report them as property-independent. |
| CL-22 | Sensors are validation targets only; TP2 and TW10 require policy handling. | Sensor-map contract and July 17 sensor policy update. | Targets for scoring; never runtime inputs. | TP2 restored in later policy; TW10 excluded/blocked for active-HX shell prediction. | `2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv`; `2026-07-17_sensor_tp2_restore_tw10_exclude/sensor_policy_scorecard.csv`. | Preserve coordinate/projection caveats; do not use TP/TW temperatures to run the model. |
| CL-23 | The M0-M4 model-form ladder is a defensible thesis product while final M6 remains blocked. | Endpoint strategy and model-form bakeoff package. | Split-aware comparison; no fitting on holdout/external rows. | Current intermediate product; final freeze still pending. | `06_intermediate_model_forms_and_endpoint_strategy.md`; `2026-07-17_thesis_endpoint_model_form_bakeoff/README.md`. | Report missing final scores explicitly; do not imply M0-M4 replace the desired frozen predictive model. |
| CL-24 | The final scorecard shell exists, but final predictive scores and admissions wait for a frozen candidate. | Final predictive scorecard shell. | Salt1-4 training; Salt2 +/-5Q holdout; `val_salt2` external. | Blocked by `FINAL_FREEZE_TBD` and open submodel gates. | `2026-07-17_final_predictive_scorecard_shell/README.md`. | Placeholder rows are a contract, not results. |
| CL-25 | SAM relevance is interpretive transfer, not SAM validation. | Endpoint strategy and dedicated SAM-facing section. | All evidence may inform closure discipline; no SAM scoring role yet. | Thesis-safe interpretation. | `11_sam_facing_interpretation.md`. | Do not claim SAM validation, SAM calibration, or experimental confirmation unless an actual SAM/experiment comparison is added. |
| CL-26 | Recirculating two-tap corner pressure should be modeled as a section-effective pressure residual, not ordinary component K. | July 20 package emits a residual contract, current-row pressure/recirculation table, same-QOI UQ sampling contract, paper claim ledger, artifact crosswalk, and figure/table manifest. | Current rows are diagnostic/model-form evidence; future rows may become candidates only after same-QOI UQ and split-safe scoring. | Contract created; predictive closure and coefficient admission remain blocked. | `13_two_tap_recirc_section_effective_pressure_model.md`; `2026-07-20_two_tap_recirc_section_effective_model/section_effective_model_contract.csv`; `paper_methods_pressure_basis.md`; `paper_results_current_evidence.md`. | The allowed labels are `section_effective_pressure_residual`, `K_eff_recirc_diagnostic`, and `regime_diagnostic`; forbidden labels include ordinary `component_K`, F6 fit admission, and hidden global hydraulic multipliers. |

## How To Use This Ledger In The Thesis

When writing a chapter section, carry the claim ID into a margin note or drafting
comment until the prose is stable. The expected pattern is:

```text
Claim -> evidence table/figure -> split role -> admission status -> caveat.
```

For example, the junction-aware section should cite CL-11 through CL-13. The
uncertainty chapter should cite CL-19 through CL-22. The forward predictive
model chapter should cite CL-04, CL-05, CL-09, CL-10, and CL-23 through CL-24.

## Open Claim Follow-Ups

| Follow-up | Why it matters | Current owner/status |
| --- | --- | --- |
| Add final frozen M6 score rows when available. | Converts CL-23/CL-24 from endpoint contract to final result. | Pending active model-scoring work. |
| Add chapter-ready literature source-envelope table. | Supports CL-17 and CL-21 with author/title/equation/validity provenance. | Remaining follow-on under `TODO-THESIS-ENRICHMENT-RESEARCH-AVENUES`. |
| Add figures for segment atlas and junction heat split. | Makes CL-03 and CL-11 visual rather than only tabular. | Future writing/figure task. |
| Refresh CL-13/CL-26 after same-QOI UQ or a non-recirculating anchor lands. | Corner pressure is thesis-important but current rows are diagnostic/model-form evidence only. | Future two-tap UQ/anchor or junction-aware refresh row. |
