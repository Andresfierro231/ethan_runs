---
provenance:
  - operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s5_source_property_split_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s6_frozen_candidate_scorecard/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_cross_chapter_visual_ledger/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_ch6_ch7_polish_figtable_insertions/README.md
  - operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_negative_k_section_effective_thesis_case_dispatch/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/README.md
tags: [thesis-section, current-section, csem, admission-ledger, uncertainty, split-policy]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
task: TODO-THESIS-CH6-CSEM-ADMISSION-UNCERTAINTY-DRAFT
date: 2026-07-21
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Closure Admission And Uncertainty

## Chapter Claim

The closure-admission framework is the control layer for the thesis. It states
what a CFD-derived quantity is allowed to prove before that quantity appears in
a one-dimensional model, a score table, or a thesis claim. A small residual is
not admission by itself. A row must also have a legal split role, an allowed
runtime-input contract, source/property labels, pressure or thermal basis
metadata, uncertainty disposition, and blocker status.

This chapter supports CL-04 through CL-08 and CL-16 through CL-22 in the thesis
claim ledger. Its practical rule is:

> A coefficient without its admission metadata is not a predictive closure.

The chapter should therefore be read as a methods result, not only as
administration. It defines the conditions under which high-fidelity CFD
evidence can move into a reduced model without becoming a hidden replay of the
same CFD row. The discipline is especially important for the CSEM/SAM-facing
use case, where the eventual systems-code value is not a single tuned number
but a traceable decision about which terms are admitted, diagnostic, blocked,
or score-only.

## Evidence Classes

The final split separates model construction from model scoring. The current
split policy is:

| Evidence class | Rows or quantities | Allowed use |
| --- | --- | --- |
| Final training | Salt1-4 nominal rows when row-specific gates pass. | Fit or calibrate admitted final model terms. |
| Training support | Salt1 +/-10Q and Salt4 +/-5Q where admitted. | Support trend and sensitivity checks with labels preserved. |
| Holdout/testing | Salt2 +/-5Q. | Score a frozen model only. No fitting, tuning, or model selection. |
| External test | `val_salt2`. | External-style scoring or context only. No fitting, tuning, or model selection. |
| Diagnostic | Any row or quantity that explains model-form error but fails a term-specific gate. | Motivate model form, blockers, or future extraction. Not a predictive input. |
| Blocked | A row or quantity with an open named blocker for the intended claim. | Cannot support that claim until a later package resolves or supersedes the blocker. |

The class applies to both cases and quantities. A case may be valid for
holdout scoring while its pressure coefficient remains diagnostic because the
pressure basis, recirculation state, component isolation, or same-QOI
uncertainty is not acceptable for coefficient admission.

## Current Release-Gate Status

The current `ethan_runs` evidence supports a gate-by-gate thesis result even
before a final frozen candidate exists.

| Gate | Current status | Chapter use |
| --- | --- | --- |
| S0 baseline control surface | Complete in the first-key studies wave. | Shows target availability, missing predictions, and runtime/split audit. |
| S1 external-boundary dictionary | Contract complete; Fluid source integration remains separate. | Defines setup-facing thermal inputs and missing setup fields. |
| S2 split heat-loss evidence | Complete as residual-owner evidence; Phase 3 scoring remains open. | Supports heat-path separation before fitting. |
| S3 pressure source envelope | Complete as diagnostic non-admission. | Supports pressure-basis and source-envelope discipline. |
| S4 recirculation guard | Complete diagnostic guard; no coefficients admitted. | Blocks ordinary upcomer `Nu`, `f_D`, and `K` language while preserving exchange-cell requirements. |
| S5 source/property split release | Complete as a blocked release gate. | Shows label completeness and split permissions are auditable, while releasing `0` rows for fitting or model selection. |
| S6 frozen scorecard | Complete as a blocked scorecard shell. | Defines the final-score contract with `0` final score values until a runtime-legal candidate is frozen. |
| S7 TP/TW sensor-map contract | Complete as score-target discipline. | Classifies `17` sensors with `1` mapped, `15` bounded, `1` excluded, and `0` runtime-temperature, fit, or model-selection permissions. |
| S8 wall/test-section axial-mixing candidate | Complete as negative result. | Reports `15` prior candidate rows, `0` admitted candidate rows, and `0` S11-ready candidates. |
| S9 upcomer onset/exchange UQ | Complete as negative/diagnostic result. | Enriches the recirculation-validity boundary while releasing `0` S11-ready upcomer candidates. |
| S10 pressure/F6 same-QOI/anchor UQ | Complete as negative/diagnostic result. | Strengthens pressure/F6 non-admission while releasing `0` S11-ready pressure candidates. |
| S11 candidate-specific release refresh | Still trigger-gated. | Cannot run from the current S8/S9/S10 evidence because all three produced `0` S11-ready candidates. |
| Same-QOI Phase C admission table | Complete as a negative UQ gate result. | Same-QOI Phase C adds a negative UQ gate result: `0` accepted rows and `8` blocked rows, preserving non-admission until row-matched UQ exists. |
| S12 thermal-shape ownership candidate | Complete as a negative/blocked candidate contract. | S12 adds a new thermal-shape ownership contract, `S12-HIAX1`, but releases `0` admitted and `0` S11-ready candidates until train-only scoring and exchange-state UQ exist. |
| S13 seeded upcomer exchange inputs | Input-ready / heat-path fail-closed. | Salt2/Salt3/Salt4 have seeded CV/interface/wall-face manifests, but sampler readiness remains `0/3`; heat-path release has `0` `Q_wall_W`, source-side, same-window thermal, or sampler/UQ release rows. |
| S14 pressure/F6 branch-use scorecard | Complete as diagnostic non-admission. | Scores `53` pressure/F6 rows with `0` admitted, `11` diagnostic-only, `8` future-candidate, and `34` do-not-use rows. |
| F-J and Phase H/H2 thermal attribution | Complete train-only diagnostics. | Identifies heated-incline/TW5 as dominant residual owner and shows broad passive-hA sensitivity, but releases no repair, freeze, admission, validation, holdout, or external-test score. |

This table should be used as a chapter-level admission snapshot. Completed
gates can be written as methods/results infrastructure. S8, S9, and S10 are
now completed negative results: they sharpen the next evidence path without
admitting a closure or thawing the final scorecard.

**Table insertion:** Place the S0-S11 gate-flow table from
`work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/s0_s11_gate_flow_table.csv`
immediately after this admission snapshot. Caption it as a release-gate map,
not a prediction table. The required caveat is that S6 contains `0` final
score values and S11 remains trigger-gated until a named physical candidate is
released.

## Diagnostic Non-Admission Snapshot

The diagnostic evidence integration package makes the useful negative results
explicit. S4 is a positive guard result and a negative admission result:
`90` ordinary single-stream candidates were reviewed, `4` branch disable rows
were written, `45` reverse-flow/exchange diagnostic rows were preserved, `14`
exchange variables were audited, and `0` ordinary upcomer `Nu/f_D/K`,
exchange-cell, or scoreable-now rows were admitted.

The same boundary applies to pressure and thermal residual ownership. Current
pressure-corner evidence can be used as source-envelope and section-effective
diagnostic evidence, but not as negative loss, clipped `K`, component `K`, F6
fit, or a global pressure multiplier. Current thermal residual evidence can
attribute heat-path, wall/test-section, upcomer-exchange, and runtime-legality
owners, but it cannot authorize realized CFD `wallHeatFlux`, CFD `mdot`,
unresolved residuals, or realized test-section heat as predictive runtime
inputs.

## Runtime-Input Rule

A predictive runtime model may use only setup-known quantities and previously
admitted coefficients trained under the legal split. Allowed runtime inputs
include geometry, property mode, heater setup inputs, cooler/HX setup inputs,
ambient or external-boundary dictionaries, and admitted closure coefficients.

The following are forbidden as predictive runtime inputs:

- CFD mass flow rate;
- realized CFD `wallHeatFlux`;
- imposed CFD cooler duty from the scored row;
- realized test-section heat from the scored row;
- validation TP/TW or branch temperatures;
- pressure or heat targets from the row being scored;
- coefficients fit using a holdout or external row.

Those quantities may appear in diagnostic replay studies, target ledgers, or
score tables. They may not be used to run a final predictive claim. This rule
is the boundary between CFD-informed explanation and CFD-leaking prediction.

The runtime-leakage rule is a thesis contribution because it makes the reduced
model auditable before any accuracy number is shown. A model can match a CFD
target for the wrong reason if it is allowed to ingest the row response as a
boundary condition, source, or target-derived coefficient. The workflow avoids
that failure by making runtime status an explicit field in every closure,
score, and figure/table caption.

## Sensor-Map Release Discipline

The S7 sensor-map contract extends the runtime-input rule to TP/TW
temperatures. The package reviewed `17` sensor-policy rows and classified the
sensor evidence as `1` mapped, `15` bounded, and `1` excluded. Its thesis value
is not that probe temperatures become model inputs. The value is that every
probe used for scoring has an explicit path-position interpretation, bounded
status, or exclusion rationale before it appears in a residual table.

The admission rule is strict: S7 allows `0` TP/TW runtime target-temperature
inputs, `0` TP/TW fit targets, and `0` TP/TW model-selection permissions. Probe
temperatures are score-only outputs and diagnostic residuals. They remain
secondary to energy balance and branch heat parity until a later package
admits stronger evidence.

**Table insertion:** Use
`work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/sensor_overlay_table.csv`
as the primary Ch. 6 sensor-map table and
`work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/runtime_leakage_caveat_table.csv`
as the runtime caveat table. The caption must state that TP/TW temperatures
are post-solve score targets, never predictive runtime inputs.

## Source And Property Labels

Source and property labels are required before a closure-like row can be
admitted. The final scorecard shell and source/property gate work require every
fit/admission candidate to carry:

| Label | Why it matters |
| --- | --- |
| `property_mode` | Defines density, viscosity, heat capacity, conductivity, and derived groups before closure interpretation. |
| `property_sensitivity_label` | States whether property choice has been checked or remains a model-choice uncertainty. |
| `source_validity_envelope_status` | States whether a literature or source model overlaps the TAMU operating envelope. |
| `source_use_category` | Distinguishes reference, diagnostic, architecture, fit, or admitted use. |
| `provenance_author_title` | Preserves literature provenance by author/title rather than mutable citation numbers. |

Blank or conservative labels block admission. They do not block a diagnostic
discussion if the row is explicitly described as diagnostic.

## Pressure Admission Gates

Pressure reduction in a natural-circulation loop must separate static pressure
change from hydrostatic head, kinetic pressure change, straight/developing
reference loss, and local residual. The LitRev extraction makes this a required
postprocessing contract, not an optional refinement.

Before a pressure coefficient can be admitted, the row should carry:

- pressure plane metadata and averaging basis;
- gross static or reduced-static pressure difference;
- hydrostatic correction with density basis;
- kinetic correction with velocity basis;
- straight/developing reference policy;
- component versus section or cluster classification;
- recirculation diagnostics such as reverse area and reverse mass fraction;
- recovery diagnostics where a component coefficient is claimed;
- same-QOI time, mesh, or plane-sweep uncertainty;
- source envelope and coefficient-naming status.

Current two-tap `corner_lower_right` evidence does not satisfy ordinary
component-K admission. The open blocker register still lists component
isolation failure, same-QOI UQ missing, and material reverse flow for that
feature. Therefore the thesis may discuss those rows as pressure-basis,
recirculation, and section-effective residual evidence, but not as admitted
ordinary `component_K`, F6, or a hidden global hydraulic multiplier.

The negative-K dispatch now closes the current component-K forcing path for
these rows. The literature-supported interpretation is not that a negative
loss coefficient has been discovered. It is that the coefficient basis is
invalid for an ordinary one-stream component value. The sign must be preserved,
but the name must change. The allowed claim is a section-effective pressure
residual under recirculating endpoint planes. The forbidden claims are ordinary
component `K`, cluster `K`, F6 recorrection, clipped `K`, and hidden/global
hydraulic multiplier.

The numeric basis for that wording is small but useful. After hydrostatic and
kinetic correction, the available signed residuals are Salt2
`-1.25366731683 Pa`, Salt3 `-1.84957005859 Pa`, and Salt4
`-1.67833900273 Pa`. The no-fit bakeoff applies the Salt2 diagnostic
`K_eff_recirc` to the Salt3/Salt4 train rows without refitting; its maximum
transfer error is `0.47046606946166093438399 Pa`. This is a thesis-scale
model-form stress test. It is not a validation score, a holdout score, an
external-test result, or a freeze/admission decision.

| Pressure route | Current decision | Reason |
| --- | --- | --- |
| Current lower-right ordinary component `K` | Stop current attempts. | Reverse flow, missing same-basis straight/developing reference, missing component isolation, and missing same-QOI UQ block the basis. |
| Section-effective residual `Delta_p_recirc_section` | Use as thesis evidence. | Signed residual is finite after basis correction and can be carried as residual ownership. |
| Salt2-frozen diagnostic transfer | Use as no-fit diagnostic only. | Sub-Pa transfer error on train rows, with `0` protected rows and `0` refitting. |
| F3/Shah apparent comparison | Not numerically evaluated here. | Existing F3/F6 artifacts withhold comparison until an ordinary admissible F6 candidate exists. |

The S10 study closes the current low-recirculation/F6 review as
`negative_result_s11_still_blocked`. It reviews `11` candidate rows across
low-recirculation pressure anchors, current pressure-corner diagnostics, and
F6 endpoint pairs, and releases `0` S11-ready pressure/F6 candidates. The
result strengthens the hydraulic limitations chapter: the next useful
pressure work is a new nonrecirculating or low-reverse-flow anchor with
same-QOI uncertainty, not a clipped-K, hidden-multiplier, or mixed-basis
pressure correction.

S14 extends that decision into a broader branch-use scorecard. It scores `53`
pressure/F6 rows and releases `0` admitted rows: `11` rows are
diagnostic-only, `8` are future-candidate, and `34` are do-not-use. The
preferred future ordinary-pressure lanes remain `right_leg` and
`test_section_span`, while current F6 endpoint pairs remain diagnostic only.
This is a stronger non-admission result, not an F6 recorrection.

Same-QOI Phase C adds a negative UQ gate result to this pressure story. Its
`0` accepted rows and `8` blocked rows mean uncertainty is visible as an
admission gate, not borrowed from neighboring QOIs or filled by clipping a
pressure coefficient.

## Upcomer And Exchange Admission Gates

Upcomer evidence follows the same admission discipline. Existing CFD evidence
can show recirculation, reverse flow, and exchange-cell plausibility, but that
does not make a single-stream upcomer an ordinary pipe segment. The current
ordinary upcomer `Nu`, `f_D`, and `K` language remains disabled unless a later
package supplies near-onset or non-recirculating anchors, same-window exchange
QOIs, and uncertainty evidence.

The S9 study closes as `negative_result_s11_still_blocked`. It identifies
`14` grouped onset/exchange rows and `6` exchange-QOI contract rows, but
releases `0` S11-ready upcomer candidates. The required missing evidence is
specific: `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window pressure and
thermal residual support, and same-QOI uncertainty. This is a useful thesis
result because it converts recirculation from a qualitative caveat into a
release gate for future hybrid upcomer modeling.

S13 now gives that future hybrid lane a concrete extraction scaffold without
changing admission status. The seeded input manifest reports Salt2/Salt3/Salt4
as `3/3` ready for later scheduler-authorized seeded surface extraction, with
`38880` seeded CV cells, `38880` seeded internal interface faces, and `38880`
trusted wall faces per case. The downstream gate remains closed: sampler-ready
rows are `0/3` because raw sampled surface fields, `Q_wall_W`, same-window
sampler outputs, and same-QOI UQ are absent. The S13 heat-path lane release
adds a second guard by allowing `0` sampler refresh, harvest, or UQ rows until
the missing field and heat-path lanes exist.

## Thermal Admission Gates

Thermal closure admission must preserve the heat ledger. Heater input, cooler
removal, passive wall loss, test-section source/loss, junction/stub heat,
external convection, radiation, wall or storage effects, and residuals are
separate lanes. Internal `Nu` or effective `h` cannot absorb all unmatched heat.

Before an internal heat-transfer or wall-loss closure can be admitted, the row
should state:

- bulk-temperature and wall-temperature definitions;
- sign convention and heat-balance closure;
- wall/material stack and external-boundary representation;
- radiation policy;
- source and sink ownership;
- mesh/GCI or final-use disposition;
- split role and runtime-input audit;
- source/property labels.

The current evidence admits stronger setup-facing heater and cooler/HX
submodel claims than passive wall/test-section closure claims. The
`predictive-wall-test-section-submodels` blocker remains open because current
runtime-legal candidates did not improve mdot and TP/TW temperature shape
together. The PB2/PB3 wall/test-section distribution family is therefore a
negative diagnostic result, not an admitted passive-boundary closure.

The S8 wall/test-section axial-mixing package sharpens that limit. It closes
as `negative_result_no_s11_candidate`: existing setup-only wall/test-section,
axial-mixing, upcomer-stratification, UMX1, and TSWFC2 candidate families
provide `15` prior score rows but `0` admitted candidates and `0` S11-ready
candidates. That result can support falsification and future-study targeting.
It cannot admit a closure, thaw the S6 final scorecard, or authorize validation
temperatures, realized CFD heat fluxes, realized test-section heat, or row CFD
mass flow as runtime inputs.

S12 adds a new thermal-shape ownership contract after this negative S8 result.
The named `S12-HIAX1` lane points the dominant TW5/TW6 residual toward
heated-incline/upcomer exchange-shape physics rather than another passive
selector. It remains a contract only: no finite train-only candidate score,
exchange-state QOI set, same-QOI UQ, source/property release, S11 trigger, or
final score is released.

The F-J, Phase H, and H2 external-boundary diagnostics sharpen the same
thermal admission boundary. F-J recomputes the Salt2 train/support baseline
with all-probe RMSE `83.36187927489736 K`, TP RMSE `80.4585733904668 K`, TW
RMSE `84.6486516564125 K`, and mdot `0.00626567502343775 kg/s`; its top
residual owner is `heated_incline`, with maximum absolute residual
`109.09380824932663 K`. Phase H shows that lowering all passive `hA` by half
improves TW5 absolute residual by `51.63369382647278 K` and all-probe MAE by
`47.133590749185956 K`, while lower-leg-only `hA` halving improves TW5 by
only `4.59310690807564 K`. H2 therefore classifies the signal as broad
passive-wall and source-basis evidence requiring an independent
setup/geometry/literature passive-wall basis before repair. None of these
train-only diagnostics admits a passive `hA` multiplier, wall/test-section
closure, S11 candidate, freeze, or final score.

The admissibility rule is therefore positive and negative at the same time.
Phase E can be cited as a legal executable runtime path, but Phase F/G/I own
the residual and source/sink boundaries before any repair is selected. Phase H
can be cited as heat-path responsiveness, but the global response cannot be
admitted as a fit. The only allowed next step is an independently sourced
external heat-path or source/sink/redistribution candidate with a fresh runtime
audit.

**Table insertion:** Route the S8 gate status through Ch. 7 for results, but
refer to
`work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/acceptance_gate_matrix.csv`
from this Ch. 6 gate section when explaining why the wall/test-section family
remains diagnostic rather than admitted.

## Uncertainty Ledger

The uncertainty treatment is structured rather than scalar:

| Uncertainty source | Thesis use | Boundary |
| --- | --- | --- |
| Time-window uncertainty | Defines uncertainty in the CFD steady reference target. | Does not explain structural model bias by itself. |
| Mesh/GCI disposition | Gates coefficient admission and publication strength. | Row-specific; do not claim mesh is globally resolved. |
| Property-lane sensitivity | Controls `Re`, `Pr`, `Gz`, buoyancy, heat transfer, and pressure interpretation. | Closures are not property-independent unless shown. |
| Sensor map | Defines TP/TW score targets, path-position interpretations, bounded probes, and exclusions. | S7 allows `0` runtime target-temperature inputs, `0` fit targets, and `0` model-selection permissions. |
| Split role | Controls what a row is allowed to prove. | Score quality does not make a holdout row trainable. |
| Runtime leakage | Separates predictive runs from diagnostic replay. | A good replay can still be non-predictive. |
| Recirculation/onset | Blocks ordinary single-stream labels where reverse flow is material. | Requires near-onset or non-recirculating anchors before ordinary upcomer coefficients. |
| Wall/test-section heat placement | Explains why total heat removal and temperature shape can disagree. | Improving mdot alone is not admission. |

Uncertainty can qualify a claim, identify a diagnostic lane, or keep a result
out of the admitted set. It cannot promote a blocked coefficient.

## Current Blocker Status For This Chapter

The current open thesis-facing blockers are:

| Blocker | Chapter meaning |
| --- | --- |
| `predictive-wall-test-section-submodels` | Passive wall/test-section and temperature-shape closure is not admitted. |
| `upcomer-onset-data-sparsity` | Ordinary upcomer `Nu`, `f_D`, and `K` rows are not admitted in current recirculating states. |
| `f6-friction-re-correction` | F6 remains narrowed but unresolved; current pressure anchors do not admit an ordinary F6 replacement. |
| `two-tap-corner-lower-right-component-isolation-fails` | Current corner rows are apparent/cluster/section diagnostics, not isolated component K. |
| `two-tap-corner-lower-right-same-qoi-uq-missing` | Current two-tap pressure rows lack same-QOI UQ for admission. |
| `two-tap-corner-lower-right-material-reverse-flow` | Current corner rows fail ordinary one-stream reverse-flow gates. |

Resolved or superseded blockers should not be reintroduced as live limitations.
They may be mentioned only as historical context if a section names their
resolved status and source.

## Writer Import Notes

The Ch. 6 LaTeX writer should import the admission framework before importing
any result table. The immediate main-text table candidates are:

- S6 gate flow:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s6_blocked_scorecard_shell/s0_s11_gate_flow_table.csv`;
- S7 sensor policy:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s7_sensor_map_overlay/sensor_overlay_table.csv`;
- S9 exchange-QOI requirements:
  `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/exchange_qoi_figure_contract.csv`;
- S13 seeded heat-path fail-close:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_seeded_heat_path_lane_release/heat_path_lane_table.csv`.

The polish backlog for these tables lives in
`work_products/2026-07/2026-07-21/2026-07-21_thesis_post_study_writing_refresh/figure_table_polish_backlog.csv`.
The writer should condense wide CSVs for the main text and keep the full
source tables as appendix material. The captions must preserve the current
state: `0` final score values, `0` TP/TW runtime permissions, `0` ordinary
upcomer coefficient admissions, and `0` sampler/UQ release rows from S13.

## Chapter-Ready Wording

The admission framework is what prevents the reduced model from becoming a
tuned accounting exercise. A CFD-derived quantity may be useful in several
ways: it can define a target, explain a residual, motivate a model-form slot,
calibrate an admitted coefficient, or score a frozen prediction. Those uses are
not interchangeable. In this thesis, every closure-like quantity carries a
split role, runtime-input status, source/property labels, uncertainty
disposition, and admission state before it can be used predictively.

This discipline is most important for the pressure and thermal terms. Current
corner pressure rows identify structured local pressure behavior, but they
remain diagnostic because component isolation, recirculation, and same-QOI
uncertainty gates are open. Current wall/test-section candidates identify a
thermal-shape blocker, and S8 confirms that the current setup-only candidate
families provide no S11-ready closure. TP/TW probes are score-only outputs
under S7, and the S6 scorecard remains intentionally empty until a frozen,
runtime-legal candidate exists. The result is not a lack of progress; it is the
thesis method working as intended. The ledger preserves useful evidence while
preventing unsupported predictive closures.
