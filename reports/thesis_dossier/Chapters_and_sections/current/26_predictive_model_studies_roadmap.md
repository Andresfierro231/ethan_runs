---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/staged_implementation_plan.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/next_study_queue.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/freeze_readiness_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/residual_lane_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s8_wall_test_section_axial_mixing_candidate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s10_pressure_f6_low_recirc_anchor_uq/README.md
  - operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md
  - .agent/BLOCKERS.md
tags: [thesis-section, current-section, predictive-model, studies-roadmap, forward-model, closure-admission]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_model_execution_path/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_predictive_final_model_starter/README.md
task: TODO-THESIS-PREDICTIVE-STUDIES-ROADMAP-2026-07-21
date: 2026-07-21
role: Forward-pred/Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# Predictive Model Studies Roadmap

This section defines the studies to perform, document, and defend while moving
from the current `fluid+walls` modeling target toward the final predictive
model. The endpoint model should accept setup-facing inputs and return loop
mass flow rate, branch temperatures, TP/TW sensor temperatures, and attributed
pressure and thermal residuals.

This is not a final scorecard and it does not admit a new closure. The current
starter result is `starter_implemented_final_freeze_still_blocked`: the
baseline contract exists, but no frozen final candidate exists, the
source/property fit-release gate remains closed, and wall/test-section/passive
thermal shape remains a live blocker.

## Claim Discipline

The thesis should keep four claim classes separate.

| Claim class | Allowed use | Forbidden use | Thesis wording |
| --- | --- | --- | --- |
| Train/calibration | Fit predeclared admitted terms using Salt1-4 nominal rows after source/property release. | Reporting blind performance from these rows. | "The model was calibrated or selected on these rows." |
| Development validation/support | Check sensitivity, robustness, and failure modes on predeclared support rows. | Treating support rows as blind holdout evidence. | "The model was stress-checked on development/support rows." |
| Holdout/testing | Score a frozen model on Salt2 +/-5Q rows after freeze. | Any tuning, refitting, source choice, or model selection. | "The frozen model was tested on held-out perturbations." |
| External test | Score `val_salt2` or later admitted external CFD only after freeze and external-ledger admission. | Back-propagating external-test residuals into the model. | "The frozen model was externally tested under a separate setup ledger." |

Every study below should report which rows it used, whether those rows were
train/support/holdout/external, and whether any result is diagnostic rather
than predictive.

## Current Starting Point

The baseline is now a legal reference surface, not a successful final
prediction. The starter package provides:

- `baseline_model_contract.csv`: current baseline rows and missing-prediction
  declarations.
- `runtime_and_split_gate_audit.csv`: checks that no scorecard row is silently
  released into fitting.
- `residual_lane_readiness.csv`: pressure and thermal residual lanes that must
  be populated before a final claim.
- `next_study_queue.csv`: the ordered implementation queue.
- `freeze_readiness_matrix.csv`: gates that must pass before a final candidate
  can be frozen.

The immediate scientific fact is negative but useful: the thesis can already
claim disciplined model-development infrastructure, split protection, residual
attribution design, and narrowed blocker location. It cannot yet claim final
predictive accuracy.

## Post-S8/S10 Evidence Frontier

The current frontier is sharper than the original S0-S6 roadmap. S8, S9, and
S10 have now closed as negative or diagnostic studies, each with `0` S11-ready
candidates. This means the next work should not reopen final scoring or repeat
the same candidate sweeps. It should generate the missing evidence named by
the completed gates.

| New study row | Scientific requirement | Required figures/tables | Release condition |
| --- | --- | --- | --- |
| S12 thermal-shape ownership candidate | Introduce a new physical owner for TW5/TW6 and wall/test-section residuals; compare against M3/prior families without runtime leakage. | TW5/TW6 residual atlas, heat-path ownership waterfall, candidate comparison table, runtime-leakage audit, admission matrix. | Exactly one runtime-legal thermal candidate reaches S11, or a negative result documents why none does. |
| S13 upcomer exchange production harvest/UQ | Produce or fail-close `V_recirc`, `mdot_exchange`, `tau_recirc`, same-window temperature/pressure support, and near-onset/non-recirculating anchor evidence. | Onset-regime map, exchange-cell schematic, exchange-QOI/UQ table, ordinary-closure disabled map, S11 decision table. | Exchange-cell candidate reaches S11, or ordinary upcomer closures remain disabled with exact missing-QOI evidence. |
| S14 pressure/F6 nonrecirculating-anchor evidence | Find or falsify nonrecirculating/low-reverse pressure anchors with same-QOI UQ and pressure-basis decomposition. | Pressure-basis decomposition figure, pressure/F6 gate waterfall, anchor table, component-K rejection table, S11 decision row. | Named pressure/F6 candidate reaches S11, or pressure/F6 remains diagnostic with exact missing-anchor evidence. |
| S15 candidate freeze/source-property score release | Run only after S12, S13, or S14 names exactly one candidate; audit source/property, split, runtime, protected rows, and uncertainty before final scoring. | Source/property release ledger, frozen-candidate manifest, split/protected-row audit, uncertainty table, final or blocked scorecard. | S6 opens with one frozen runtime-legal candidate, or the thesis records a no-freeze result with `0` final score values. |

These rows are now present on `.agent/BOARD.md` so implementation agents can
claim them directly. They preserve the same guardrail as the original roadmap:
diagnostic CFD responses can support residual ownership and blocker decisions,
but they cannot become hidden predictive runtime inputs.

## Study Sequence

| ID | Study | Primary question | Inputs and evidence | Outputs to publish | Acceptance signal | Thesis value if successful | Thesis value if still blocked |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | Baseline current model and scorecard control surface | What does the current legal model predict, and where are predictions explicitly missing? | Current `fluid+walls` target, final scorecard shell, source/property labels, runtime audit. | Baseline scorecard table, missing-prediction table, runtime-input audit, split-use ledger. | Every target has a prediction, a declared missing value, or a blocked reason; zero runtime leakage. | Establishes the reference model against which later residual reductions are measured. | Still thesis-positive because it prevents hidden calibration and documents why no final score is yet defensible. |
| S1 | External boundary-condition dictionary | Can the model represent setup-facing external convection, radiation, wall/layer resistance, and drive temperatures without using realized CFD wall heat flux? | Segment/patch roles, material stack, ambient/surrounding-temperature assumptions, source-envelope labels, LitRev thermal boundary rules. | External BC dictionary, coverage map, missing-field ledger, radiation double-counting audit. | Every segment/role has an external BC row or explicit `setup_unavailable`; no realized `wallHeatFlux`, validation temperature, or imposed cooler duty is used as runtime input. | Converts the model from replay-oriented to setup-oriented thermal prediction. | Defines the exact missing setup data that limit predictive release and strengthens the methods chapter. |
| S2 | Heat-loss network and wall/test-section lane | Which heat paths explain thermal residuals without hiding them in internal Nu? | Heater, cooler/HX, passive wall, bare-quartz test-section, junction/stub, radiation/external, storage/future, sensor-map policy. | Heat-path residual ledger, wall/test-section candidate table, thermal attribution plots, coupled mdot/TP/TW/all-probe score table. | Heat lanes remain separate and wall/test-section candidates reduce residuals without worsening held-out or prohibited gates. | Supports a final predictive thermal network and gives physically named residual attribution. | A negative result still narrows the blocker to source placement, axial mixing, local wall temperature, or missing external BC data. |
| S3 | Pressure source-envelope and pressure-basis lane | Are pressure residuals ordinary straight losses, section/cluster losses, recirculation-effective terms, or unsupported component K claims? | LitRev model-form ladder, pressure corner extraction findings, F6/two-tap basis audits, straight-loss subtraction rules, uncertainty status. | Pressure source-envelope table, pressure-plane basis ledger, hydraulic residual attribution, non-admission table for unsupported K/F6 claims. | Every pressure residual is labeled as straight, section, cluster, component, recirculation-effective, or unresolved; component K remains blocked unless isolation/recovery pass. | Produces a defensible hydraulic ladder and may unlock a named pressure model. | A disciplined non-admission is thesis-valuable because it prevents global multipliers, clipped K, and basis-mismatched pressure claims. |
| S4 | Recirculation guard and hybrid upcomer lane | Where are single-stream branch closures illegal, and what hybrid throughflow-plus-recirculation variables are needed? | Reverse-flow metrics, upcomer onset evidence, branch masks, throughflow/recirculation exchange-cell design, pressure/thermal residual lanes. | Single-stream disable table, hybrid interface specification, recirculation residual columns, ordinary-closure exclusion list. | Ordinary `Nu`, `f_D`, and `K` fits are disabled where recirculation gates fail; hybrid residual terms are explicit and not absorbed into ordinary pipe closures. | Makes the final model regime-aware and protects branch correlations from contamination. | Even without calibration, it explains why current upcomer rows are not ordinary pipe evidence. |
| S5 | Source/property and split release | Are all model terms tied to permitted source envelopes and permitted split roles before scoring? | Source/property labels, literature/source-page audits, train/support/holdout/external partition contract, final scorecard guardrails. | Source/property release ledger, split-use table, row-level `fit_allowed` and `model_selection_allowed` flags, release-blocker table. | No blank source/property labels; fit-enabled rows only come from permitted training rows; support, holdout, and external rows remain score-only where required. | Allows a defensible candidate freeze if the physical lanes pass. | Provides a rigorous explanation for why the final model remains unscored rather than weakly scored. |
| S6 | Frozen candidate and final scorecard | After all gates pass, what does the frozen model predict on train/support, validation, holdout, and external-test rows? | One predeclared frozen candidate, runtime audit, external BC dictionary, pressure and thermal residual lanes, source/property release, split ledger. | Final scorecard, residual attribution, uncertainty table, train/support/validation/holdout/external-test separation, thesis-ready figures. | Frozen candidate exists; no runtime leakage; no holdout/external tuning; residual lanes populated. | Supports the final predictive-model claim. | If no candidate freezes, publish the blocked scorecard shell and shortest next evidence action instead of overclaiming. |

## Study Details

### S0 Baseline Current Model

The baseline study should be the first figure/table package for the predictive
chapter. It should report target availability before model improvement:
`mdot`, branch heat, branch temperatures, loop mean temperature, loop
temperature rise/drop, TP/TW sensors, pressure residuals, thermal residuals,
and uncertainty status.

This study should not tune anything. It should answer: "What would the current
model be allowed to say if the final scorecard were run today?" Missing
predictions should remain visible because they are evidence of blocked model
form, not clerical errors.

Minimum outputs:

- baseline target matrix;
- runtime-input audit;
- source/property label completeness table;
- split-role table;
- scorecard release guardrail table.

### S1 External BC Dictionary

The final predictive model needs an input contract that a setup user can
populate. The external BC dictionary should therefore carry, by segment or
patch role, terms such as `h`, `Ta`, `Tsur`, emissivity, wall/layer resistance,
and drive-temperature selector. The key distinction is between setup inputs and
realized CFD/postprocessed responses.

This study should document cases where the setup file does not contain enough
information. Those cases should be labeled `setup_unavailable`, not filled from
held-out wall temperatures or realized wall heat flux.

Minimum outputs:

- segment/patch external BC dictionary;
- radiation and convection ownership table;
- missing setup-field ledger;
- no-double-count audit for passive wall, test section, cooler, and junction
  heat paths.

### S2 Heat-Loss Network

The heat-loss network should split thermal residuals before any attempt to
improve internal heat-transfer coefficients. At a minimum, heater transfer,
cooler/HX removal, passive external loss, bare-quartz test-section heat,
junction/stub heat, radiation/external terms, optional storage/future terms,
internal-Nu diagnostics, and unresolved residual should be separate columns.

The thesis benefit is high even if no candidate is admitted. Recent negative
wall/test-section rows already show that improving `mdot` alone is not enough
when TP/TW and all-probe residuals worsen. This should be written as a
physically specific falsification result, not as a generic failure.

Minimum outputs:

- heat-path residual attribution table;
- candidate heat-loss-network comparison;
- TP/TW and all-probe residual table;
- plot of thermal residual by heat path and case role.

### S3 Pressure Source Envelope

Pressure work should run through source-envelope and pressure-basis gates
before any new coefficient is fit. The goal is not to force an ordinary
component K onto a recirculating or basis-mismatched row. The study should
label residuals as straight/developing loss, section or cluster loss, component
loss, recirculation-effective loss, or unresolved pressure residual.

This study strengthens the thesis whether it admits a model or not. A clean
non-admission explains why F6, two-tap, corner, and upcomer rows cannot be
collapsed into a single global multiplier without losing physical meaning.

Minimum outputs:

- pressure-plane/basis ledger;
- source-envelope table by feature family;
- residual attribution by pressure family;
- non-admission table for unsupported component K or F6 claims.

### S4 Recirculation Guard

The upcomer and nearby sections require a guard before they can contribute to
ordinary branch closures. The study should generate a disable table for
ordinary `Nu`, `f_D`, and `K` fits when reverse-flow, onset, or section-basis
evidence violates single-stream assumptions. A hybrid
throughflow-plus-recirculation interface can be specified before coefficients
exist.

Minimum outputs:

- branch/regime disable table;
- reverse-flow and onset evidence ledger;
- hybrid exchange-cell variable contract;
- list of rows allowed only for diagnostic residual attribution.

### S5 Source/Property and Split Release

Before the model can be frozen, every term must have a source/property label
and every row must have a split role. This study should be treated as a release
gate, not a narrative afterthought. The expected result today is still blocked:
the current freeze matrix reports no final candidate and zero fit-enabled rows
after the source/property gate.

Minimum outputs:

- source/property release ledger;
- row-level split-use table;
- holdout and external-test protection check;
- blocker-to-next-action table.

### S6 Frozen Candidate and Final Scorecard

Only after S1-S5 pass should one model be frozen and joined to the final
scorecard shell. The final scorecard should report performance by claim class,
not as a single undifferentiated average. Train/support residuals, validation
support results, blind holdout results, and external-test results should appear
in distinct table sections.

Minimum outputs:

- frozen model manifest;
- train/support score table;
- validation/support score table, if separately defined by the final split;
- holdout/testing score table;
- external-test score table;
- pressure and thermal residual attribution;
- runtime leakage audit;
- uncertainty and source/property release table.

## Chapter Mapping

| Thesis location | Roadmap material to use | Claim boundary |
| --- | --- | --- |
| Methodology | S0 runtime/split/source discipline, S1 setup-facing BC dictionary, S5 release gates. | Methods can be claimed before final predictive success. |
| Model-form chapter | S1 heat boundary inputs, S2 heat-loss network, S3 pressure source envelope, S4 hybrid recirculation guard. | Model forms are candidate or diagnostic until admitted. |
| Closure admission and uncertainty | S2-S5 acceptance gates, uncertainty ledgers, non-admission tables. | Negative admission results are valid results if source and split rules are explicit. |
| Results chapter | S0 baseline, S2 thermal residual attribution, S3 pressure residual attribution, S6 final scorecard if frozen. | Do not merge train/support, holdout, and external-test claims. |
| Limitations and future work | Blocked S1-S6 gates, exact missing setup fields, unadmitted source envelopes, recirculation data sparsity. | Future work should be the shortest evidence action, not broad "more data." |

## Minimum Thesis Products

If no final candidate freezes before the thesis deadline, the publishable set is
still coherent:

- current baseline and missing-prediction scorecard;
- setup-facing external BC dictionary and missing-field ledger;
- pressure source-envelope non-admission and residual attribution;
- heat-loss network residual attribution and wall/test-section falsification;
- recirculation guard and ordinary-closure exclusion table;
- source/property and split-release blocker table;
- final scorecard shell with explicit `FINAL_FREEZE_TBD absent` status.

If a final candidate freezes, add:

- frozen model manifest;
- train/support scores;
- validation/support scores where predeclared;
- holdout/testing scores;
- external-test scores;
- residual attribution and uncertainty table;
- exact statement that holdout and external rows were not used for fitting,
  tuning, source choice, or model selection.

## High-Value Figures and Tables

1. Stage-gate flow diagram from baseline to frozen scorecard.
2. Split-role table showing train/support, validation/support, holdout, and
   external-test permissions.
3. External BC dictionary coverage heat map by segment/patch role.
4. Thermal residual waterfall by heater, cooler, passive wall, test section,
   junction/stub, radiation/external, internal-Nu diagnostic, and residual.
5. Pressure residual waterfall by straight, section/cluster, component,
   recirculation-effective, and unresolved terms.
6. Recirculation guard map showing branches where ordinary closures are
   disabled.
7. Final scorecard table or blocked-scorecard shell, depending on freeze state.

## Guardrails

- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures, or
  external-test temperatures as predictive runtime inputs.
- Do not fit or select models using Salt2 +/-5Q, `val_salt2`, PM10, future
  +/-10Q, or new external CFD rows.
- Do not call support rows blind holdout rows.
- Do not hide passive-wall, cooler, heater, radiation, junction/stub, or
  test-section residuals inside internal Nu.
- Do not admit F6, component K, ordinary upcomer `Nu`, ordinary upcomer `f_D`,
  or ordinary upcomer K from current recirculating rows.
- Do not clip negative K, install a hidden global pressure multiplier, or
  collapse basis-mismatched pressure rows into a single coefficient.
- Do not write final predictive accuracy claims until a frozen candidate exists
  and the scorecard is run without runtime leakage.

## Immediate Next Steps

1. Incorporate completed S0-S10 evidence into the thesis chapters as methods,
   diagnostic results, negative results, and limitations.
2. Claim S12 if the next goal is to unblock thermal prediction; start from a
   physical TW5/TW6 residual owner, not another passive selector sweep.
3. Claim S13 if the next goal is upcomer exchange admission; produce
   same-window exchange QOIs and UQ before any exchange-cell coefficient.
4. Claim S14 if the next goal is hydraulic admission; supply low-reverse or
   nonrecirculating pressure anchors before any F6/component-K language.
5. Claim S15 only after one candidate exists; otherwise keep S6 as a blocked
   scorecard shell with `0` final score values.
