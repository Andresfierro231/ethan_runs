---
provenance:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
  - reports/thesis_dossier/figures/README.md
  - reports/thesis_dossier/figures/figure_claim_crosswalk.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
  - ../papers/UTexas_Research/3d_analysis/sections/01_introduction_and_claim.tex
  - ../papers/UTexas_Research/3d_analysis/sections/02_dataset_and_case_selection.tex
  - ../papers/UTexas_Research/3d_analysis/sections/03_postprocessing_method_and_provenance.tex
  - ../papers/UTexas_Research/3d_analysis/sections/04_salt_family_results.tex
  - ../papers/UTexas_Research/3d_analysis/sections/05_salt2_mechanism_results.tex
  - ../papers/UTexas_Research/3d_analysis/sections/06_trust_limits_and_interpretation.tex
  - ../papers/UTexas_Research/3d_analysis/sections/07_conclusions.tex
  - ../papers/UTexas_Research/3d_analysis/figures/README.md
  - ../papers/UTexas_Research/3d_analysis/notes/asset_import_log.md
tags: [thesis-section, current-section, csem, narrative-map, paper-integration, evidence-ledger]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
task: TODO-THESIS-CSEM-NARRATIVE-INTEGRATION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# CSEM Narrative Integration Plan

## Purpose

This plan says where the current evidence belongs in the thesis and in a
paper-length CSEM narrative. It is an incorporation map, not a new analysis.
It does not fit a closure, admit a coefficient, rerun a model, or promote a
diagnostic CFD observation into a predictive runtime input.

The thesis story should stay centered on one defensible claim:

> The contribution is a provenance-controlled CFD-to-1D closure workflow for
> the TAMU molten-salt natural-circulation loop. Ethan OpenFOAM CFD is the
> high-fidelity reference used to construct, diagnose, gate, and score reduced
> model terms; it is not experimental validation.

## Thesis Structure Map

Use this table as the chapter-to-evidence routing plan. The "write status"
column is the current writing disposition, not a scientific admission change.

| Narrative section | Target thesis chapter / paper section | Existing evidence to incorporate | Claim IDs | Write status | Guardrail |
| --- | --- | --- | --- | --- | --- |
| Motivation | Ch. 1 introduction; paper introduction | `Outline.md`; `01_modeling_approach.md`; 3D paper `01_introduction_and_claim.tex` | CL-01, CL-02 | Ready now | Say CFD is the current reference, not experimental validation. |
| CFD evidence | Ch. 3 physical system and CFD database; Ch. 7 results; paper dataset/results | 3D paper sections `02` to `05`; Salt-family and matched Salt 2 figures/tables; `table_artifact_provenance.tex` | CL-01, CL-11, CL-19, CL-21 | Ready as CFD diagnostic/result layer | Effective thermal metrics and pressure-gradient reductions are diagnostics, not admitted 1D coefficients. |
| 1D model form | Ch. 4 CFD-to-1D reduction; Ch. 5 `fluid+walls` model | `01_modeling_approach.md`; `02_model_form_fluid_walls.md`; `09_fluid_walls_segment_atlas.md`; LitRev `model_form_candidates.csv` | CL-02, CL-03, CL-17, CL-18 | Ready now | Keep model slots distinct from admitted coefficients. |
| Closure/admission ledger | Ch. 6 closure admission and uncertainty; appendix claim ledger | `03_split_policy_and_evidence_classes.md`; `08_thesis_claim_ledger.md`; `10_uncertainty_chapter_package.md`; LitRev `cfd_postprocessing_contract.csv` | CL-04 to CL-08, CL-16 to CL-22 | Ready now | Split role and runtime legality travel with every row. |
| Pressure results | Ch. 6 hydraulic closure; Ch. 7 results; paper pressure-basis subsection | `05_junction_aware_ledgers.md`; `13_two_tap_recirc_section_effective_pressure_model.md`; LitRev `pressure_corner_extraction_findings.csv`; 3D paper Salt 2 friction/pressure results | CL-13, CL-16, CL-26 | Partly ready as diagnostic pressure evidence | Do not admit ordinary `component_K`, F6, or global hydraulic multipliers from current recirculating two-tap rows. |
| Thermal results | Ch. 6 thermal closure; Ch. 7 results | 3D paper heat-loss and thermal-resistance results; `05_junction_aware_ledgers.md`; `07_wall_test_section_coupled_score_and_physics_plan.md`; `10_uncertainty_chapter_package.md` | CL-09 to CL-12, CL-17, CL-18 | Ready for CFD heat evidence and negative result; blocked for final passive wall/test-section closure | Do not use realized CFD `wallHeatFlux` or validation temperatures as predictive runtime inputs. |
| Predictive-model path | Ch. 7 predictive assessment; paper model ladder or methods/results bridge | `06_intermediate_model_forms_and_endpoint_strategy.md`; endpoint bakeoff package; final scorecard shell | CL-04, CL-05, CL-23, CL-24 | Ready as model-form ladder and scorecard contract | Final predictive scores are not available; `FINAL_FREEZE_TBD` is a placeholder. |
| Uncertainty | Ch. 6 uncertainty; appendix tables | `10_uncertainty_chapter_package.md`; `.agent/BLOCKERS.md`; 3D paper `06_trust_limits_and_interpretation.tex`; `table_trust_boundaries.tex` | CL-19 to CL-22 | Ready now | Uncertainty can qualify a claim, but cannot promote a diagnostic coefficient. |
| Limitations | Ch. 8 or Ch. 9 limitations; paper trust limits/conclusions | `.agent/BLOCKERS.md`; `07_wall_test_section_coupled_score_and_physics_plan.md`; `13_two_tap_recirc_section_effective_pressure_model.md`; 3D paper `06` and `07` | CL-10, CL-13 to CL-16, CL-24, CL-25 | Ready now | State blockers as results only with their current status. |
| SAM/CSEM relevance | Ch. 8 systems-code interpretation; conclusion | `11_sam_facing_interpretation.md`; `06_intermediate_model_forms_and_endpoint_strategy.md`; claim ledger | CL-02, CL-16, CL-20, CL-25 | Ready now | Claim transfer of closure discipline, not SAM validation. |

## Narrative Spine

The thesis should move in this order.

1. The TAMU loop needs reduced-order prediction, but a credible reduced model
   cannot hide pressure, heat, property, mesh, recirculation, and boundary
   errors in one coefficient.
2. Ethan OpenFOAM cases provide a high-fidelity CFD reference and a
   provenance-controlled evidence base. The 3D Salt paper supplies the mature
   transport-redistribution evidence layer.
3. The CFD reductions motivate a steady `fluid+walls` model in which every
   segment owns a fluid state, wall/material stack, pressure lane, thermal
   circuit, source/sink role, recirculation flag, admission status, and
   uncertainty status.
4. Literature and CFD postprocessing do not automatically admit closures. They
   define candidate model forms, required basis corrections, source envelopes,
   and no-silent-threshold rules.
5. Current pressure evidence is valuable but diagnostic: recirculating
   two-tap corner rows motivate section-effective pressure residuals rather
   than ordinary component `K`.
6. Current thermal evidence is stronger for heater/cooler setup-facing terms
   and junction/stub heat ownership than for passive wall/test-section closure.
   PB2/PB3 wall/test-section candidates are a useful negative result because
   they improve mdot while worsening temperature shape.
7. The predictive endpoint is still a frozen setup-only model scored on the
   locked split. Until the final freeze exists, the thesis should report the
   M0-M6 ladder, the scorecard shell, and blocked submodel gates.
8. The final value to SAM/CSEM is a vetted closure/admission workflow that can
   inform systems-code component construction without claiming SAM validation.

## Figure And Table Incorporation Ledger

### Thesis Diagrams

| Source figure/table | Target section | Use | Required caveat |
| --- | --- | --- | --- |
| `reports/thesis_dossier/figures/svg/F01_fluid_walls_loop_segment_atlas.svg` | Ch. 4 CFD-to-1D reduction or Ch. 5 model form | Opening model architecture figure. | Values, if added later, must be target/diagnostic labels, not runtime inputs. |
| `reports/thesis_dossier/figures/svg/F02_segment_local_ledger_inset.svg` | Ch. 5 `fluid+walls` equations | Visual companion to segment pressure and thermal equations. | A model slot is not an admitted coefficient. |
| `reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg` | Ch. 6 recirculation/onset uncertainty; Ch. 7 limitations | Shows throughflow plus exchange/recirculation lane. | Ordinary `Nu`, `f_D`, and `K` labels stay blocked in recirculating rows. |
| `reports/thesis_dossier/figures/svg/F04_junction_aware_vs_segment_only.svg` | Ch. 6 closure/admission ledger; Ch. 7 thermal/pressure results | Explains why junction/stub and corner ownership lanes are needed. | `val_salt2` junction heat is external-test evidence; corner K is diagnostic. |
| `reports/thesis_dossier/figures/svg/F05_model_form_ladder.svg` | Ch. 7 predictive-model path | M0-M6 ladder from baseline to final frozen candidate. | M6 remains pending unless final scorecard lands. |
| `reports/thesis_dossier/figures/svg/F06_sam_facing_flowchart.svg` | Ch. 8 SAM/CSEM relevance; Ch. 9 conclusion | Transfer of closure/admission discipline to systems-code work. | No SAM validation claim. |
| `reports/thesis_dossier/figures/figure_claim_crosswalk.csv` | Appendix figure ledger | Trace each figure to claim IDs and source sections. | Update if claim ledger IDs change. |

### Existing 3D Paper Figures

| Source figure/table | Target section | Use | Required caveat |
| --- | --- | --- | --- |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_heat_loss.pdf` | Ch. 3 CFD evidence; Ch. 7 thermal results | Salt 2 loopwise heat-loss redistribution. | Grouped heat channels depend on thermal-role metadata. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt4_heat_loss.pdf` | Ch. 3 CFD evidence; Ch. 7 thermal results | Salt 4 loopwise heat-loss redistribution. | Salt-only family evidence, not Water synthesis. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_azimuthal_means.pdf` | Ch. 3 CFD evidence | Circumferential-mean wall transport for Salt 2. | Trend-level wall transport, not local closure admission. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt4_azimuthal_means.pdf` | Ch. 3 CFD evidence | Circumferential-mean wall transport for Salt 4. | Trend-level wall transport, not local closure admission. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_friction_pressure_zoomed.pdf` | Ch. 3 CFD evidence; Ch. 6 pressure diagnostics | Matched Salt 2 friction and wall-registered pressure-gradient redistribution. | Use as CFD diagnostic evidence; do not use as admitted pressure closure. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_thermal_resistance.pdf` | Ch. 3 CFD evidence; Ch. 7 thermal results | Matched Salt 2 effective thermal transport and resistance. | Effective, QC-masked diagnostic metrics; not unrestricted local HTC truth. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_family_branch_thermal_safe_subset.pdf` | Ch. 7 thermal results | Safe-branch family thermal comparison. | Headline branch set is limited to scrutiny-cleared branches. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_branch_thermal_safe_subset.pdf` | Ch. 7 matched Salt 2 mechanism | Safe-branch matched Salt 2 thermal mechanism. | Corners and junctions remain excluded from this branch-local figure. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_branch_trust_heatmap.pdf` | Appendix or Ch. 6 trust limits | Why some branches are promoted and others withheld. | Support figure only, not a headline result. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_safe_branch_support.pdf` | Appendix uncertainty/support | QC support for safe-branch promotion. | Support figure only. |

### Existing Tables And CSV Ledgers

| Source table | Target section | Use | Required caveat |
| --- | --- | --- | --- |
| `../papers/UTexas_Research/3d_analysis/tables/table_artifact_provenance.tex` | Ch. 3 evidence provenance; appendix | Artifact hierarchy for Salt-family paper assets. | Promotion surface and numeric source package are distinct. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt_case_matrix.tex` | Ch. 3 CFD database | Salt-family case definitions and retained windows. | Keep validation continuation caveat. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt_family_quantitative_summary.tex` | Ch. 7 pressure/thermal results | Quantitative family heat and safe-branch thermal summary. | Hotspot labels depend on grouped thermal-role definitions. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt2_matched_case_summary.tex` | Ch. 7 matched Salt 2 mechanism | Quantitative matched-case pressure/thermal summary. | Validation row uses retained window `8598-8602 s`. |
| `../papers/UTexas_Research/3d_analysis/tables/table_trust_boundaries.tex` | Ch. 6 uncertainty and limitations | Allowed and disallowed wording for 3D paper evidence. | Use to prevent overclaiming. |
| `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md` | Ch. 6 main ledger; appendix | Master claim-to-evidence table. | Add a row before introducing any new claim. |
| `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md` | Ch. 5 model atlas; appendix | One-table segment implementation and admission map. | Holdout/external realized heat and pressure remain target/diagnostic only. |
| `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/coupled_delta_vs_m3.csv` | Ch. 7 negative thermal result | PB2/PB3 coupled deltas versus M3. | Candidate family has `0/4` admissions. |
| `work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/model_form_scores.csv` | Ch. 7 model-form ladder | M0-M4 score/status table. | Numeric rows are partial or diagnostic where stated; final M6 is not scored. |
| `work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/scorecard_summary.csv` | Ch. 7 final predictive path | Final scorecard shell status. | Shell has placeholders only; no final scores. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv` | Ch. 2 literature; Ch. 5 model form | Source-bounded candidate architectures. | All candidates in this package are `not admitted here`. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv` | Ch. 6 pressure admission | Pressure-recovery, basis, and corner-naming rules. | Current corner rows remain diagnostic. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv` | Ch. 4 methods; Ch. 6 admission | Required CFD reduction fields for pressure, heat, recirculation, and naming. | Missing fields make a row diagnostic only. |

## Ready To Write Now

The following thesis/paper sections have sufficient evidence for draft prose
now.

| Section | Evidence basis | What can be written |
| --- | --- | --- |
| Motivation and contribution | `01_modeling_approach.md`; claim ledger; 3D paper introduction | The problem, CFD-to-1D workflow, and branchwise ledger contribution. |
| CFD evidence database | 3D paper dataset/method sections; artifact provenance table | Salt-family evidence layers, retained-window provenance, and wall-BC setup boundaries. |
| `fluid+walls` model equations | `02_model_form_fluid_walls.md`; segment atlas | Steady segment energy balance, wall circuit, test-section balance, pressure model, and runtime contract. |
| Split and runtime legality | `03_split_policy_and_evidence_classes.md`; final scorecard shell | Training/support/holdout/external split and forbidden runtime inputs. |
| Junction/stub heat ownership | `05_junction_aware_ledgers.md`; claim ledger | Segment-only models miss structured local heat loss; `val_salt2` has about `40.926087 W` junction/stub heat target evidence. |
| Pressure-basis limitation | `13_two_tap_recirc_section_effective_pressure_model.md`; LitRev pressure findings | Current two-tap corner pressure evidence motivates section-effective residual modeling, not ordinary component K admission. |
| Wall/test-section negative result | `07_wall_test_section_coupled_score_and_physics_plan.md` | PB2/PB3 candidates improve mdot but worsen temperature shape by about `35-49 K`; `0/4` admitted. |
| M0-M6 ladder and final scorecard contract | `06_intermediate_model_forms_and_endpoint_strategy.md`; endpoint bakeoff; final scorecard shell | The endpoint strategy, model-form comparison, and blocked final scorecard state. |
| Uncertainty and trust boundaries | `10_uncertainty_chapter_package.md`; `.agent/BLOCKERS.md`; 3D paper trust table | Time-window, mesh/GCI disposition, property-lane, sensor-map, split, recirculation, and model-form uncertainty. |
| SAM/CSEM relevance | `11_sam_facing_interpretation.md` | Transferable closure discipline and systems-code construction guidance without SAM validation. |

## Blocked Until More Model Work

Do not write these as completed results yet.

| Blocked claim | Blocking evidence | Required future signal |
| --- | --- | --- |
| Final frozen predictive performance | Final scorecard shell reports no final scores and `FINAL_FREEZE_TBD`. | One frozen prediction artifact joined into the scorecard shell with train/support/holdout/external residuals. |
| Admitted passive wall/test-section closure | `predictive-wall-test-section-submodels` remains open; PB2/PB3 and later wall/source lanes admit `0` candidates in current blocker register. | Runtime-legal candidate improves mdot, TP/TW, and all-probe gates without target leakage. |
| Ordinary component `K` for current corner rows | Open two-tap blockers: component isolation fails, same-QOI UQ missing, material reverse flow. | Same-QOI uncertainty plus non-recirculating/component-isolated or source-consistent section/cluster evidence. |
| F6 friction recorrection | `f6-friction-re-correction` remains open; current inventory has `0` ordinary F6 fit-eligible rows. | Non-recirculating anchors or explicit recirculation-modeled pressure closure that beats current admitted form without hidden multiplier. |
| Ordinary upcomer single-stream `Nu`, `f_D`, or `K` | `upcomer-onset-data-sparsity` remains open with no non-recirculating anchors. | Near-onset or non-recirculating anchors with same-window pressure, thermal, recirculation, and UQ labels. |
| SAM validation | No SAM model, frozen SAM inputs, SAM scorecard, or experimental comparison in current evidence. | Separate SAM/experiment comparison package. |
| Salt-versus-Water synthesis | 3D paper trust limits keep Water as future-work context. | Defended Water closure/rebuild package and matching evidence gates. |

## Draft Prose Bank

### Motivation

The objective of this thesis is to develop a reduced-order modeling workflow
for the TAMU molten-salt natural-circulation loop without hiding model-form
errors inside a single tuned coefficient. The available Ethan OpenFOAM cases
provide the current high-fidelity reference for this workflow. They are used to
identify where hydraulic resistance, heat transfer, boundary-condition effects,
recirculation, property choice, and uncertainty enter a one-dimensional model.
They are not treated as experimental validation. The thesis contribution is
therefore a CFD-to-1D closure and admission framework: each pressure or thermal
term must carry its source path, split role, runtime-input status, uncertainty
status, and admission decision before it can become a predictive model input.

### CFD Evidence

The existing Salt-family paper supplies the mature CFD evidence layer for the
thesis. Its promoted result is a transport-redistribution statement rather than
a universal closure claim. Across the promoted Salt 2 and Salt 4 subsets, the
dominant intended-transfer burden remains in the test-section span, while the
dominant parasitic-loss burden remains in the left lower leg. The matched Salt
2 trio then shows how property-model choice redistributes friction, direct
pressure-gradient diagnostics, effective thermal transport, and thermal
resistance on a shared loop family. These figures and tables belong early in
the thesis as evidence that the 1D model needs local ownership lanes. They
should not be described as admitted local friction, heat-transfer, or
component-loss coefficients.

### 1D Model Form

The reduced model target is a steady `fluid+walls` network. Each segment
carries a bulk fluid state coupled to a wall or material stack and includes
separate pressure, thermal, source/sink, boundary, recirculation, uncertainty,
and admission fields. The segment energy balance accounts for heater input,
cooler removal, passive wall loss, test-section source/loss, junction or local
heat terms, and residuals. The pressure model balances loop buoyancy against
distributed loss, reset/development effects, local fitting or cluster losses,
recirculation terms, and residuals. In this formulation a residual is an
accounting result, not an automatic closure. A term becomes predictive only
after the corresponding literature, CFD reduction, uncertainty, split, and
runtime-input gates pass.

### Closure Admission

The admission framework is the thesis control system. Final training rows may
fit admitted terms, training-support rows may support labeled trends, and
holdout or external rows may only score a frozen model. The same rule applies
to quantities: a case can be legal for scoring while a specific pressure or
thermal coefficient from that case remains diagnostic. Predictive runtime
models may use setup-known geometry, property modes, heater and cooler setup
inputs, external-boundary dictionaries, and previously admitted coefficients.
They may not use scored-row CFD `mdot`, realized CFD `wallHeatFlux`, imposed
CFD cooler duty, validation temperatures, or pressure/heat targets from the row
being scored. This separation is what keeps CFD replay useful without letting
it masquerade as prediction.

### Pressure Results

The current pressure story is strongest as a diagnostic and model-form result.
Matched Salt 2 friction and wall-registered pressure-gradient reductions show
redistribution of hydraulic loading in the CFD reference. The two-tap
`corner_lower_right` evidence then shows why current corner pressure rows
should not be promoted to ordinary component `K`. The finite endpoint pressure
and velocity fields fail ordinary admission gates because the rows are
materially recirculating, not component-isolated, and missing same-QOI
uncertainty. The next defensible model form is a section-effective pressure
residual with explicit pressure basis, kinetic correction, hydrostatic
correction, straight/developing reference, velocity basis, and recirculation
status. This is a useful thesis result precisely because it prevents a
misleading closure admission.

### Thermal Results

The current thermal evidence supports both positive and negative results. The
3D Salt-family figures show structured loopwise heat redistribution and
safe-branch effective thermal differences. The junction-aware ledger shows that
local junction and stub heat ownership is thesis-relevant, including the
`val_salt2` external-test evidence of about `40.926087 W` across four
junction/stub buckets. At the same time, the wall/test-section closure remains
blocked. The PB2/PB3 wall-distribution candidates were runtime-legal and
coupled to admitted cooler evidence, but they improved mdot while worsening
all-probe and wall-temperature errors by roughly `35-49 K`; the candidate
family therefore has `0/4` admissions. The appropriate conclusion is that the
remaining thermal error is controlled by source placement, temperature-shape,
wall/fluid coupling, or upcomer exchange physics, not by a simple passive
heat-removal multiplier.

### Predictive-Model Path

The thesis should report the predictive path as an endpoint ladder, not as a
finished final score. M0 is a setup-only baseline contract, M1 is diagnostic CFD
thermal-boundary replay, M2 contains admitted heater/cooler boundary evidence
but not a full wall/test-section solution, M3 is the segment-only
`fluid+walls` network, M4 adds junction-aware attribution, M5 represents the
hybrid upcomer direction, and M6 is the desired frozen final predictive
candidate. Current files define the ladder and scorecard shell, but final
predictive scores are unavailable because no admitted Salt1-4 nominal freeze
has landed. That absence should be stated as the result of the admission
discipline, not hidden.

### Uncertainty

The uncertainty chapter should avoid a single global error bar. The evidence
base carries time-window uncertainty for the CFD reference, row-specific
mesh/GCI disposition, property-lane sensitivity, sensor-map caveats, split-role
limits, runtime-leakage status, recirculation/onset uncertainty, and
wall/test-section model-form uncertainty. These categories decide what each
quantity can prove. They can qualify a result, widen an interval, or mark a row
as diagnostic, but they cannot convert a blocked coefficient into an admitted
predictive input.

### Limitations

The current limitations are part of the scientific narrative. Passive
wall/test-section closure is not admitted. Current corner pressure rows do not
admit ordinary component `K` or F6 recorrection. Upcomer rows with material
reverse flow do not support ordinary single-stream pipe coefficients. The final
predictive scorecard is a shell until a frozen candidate exists. The existing
Salt-focused 3D paper does not establish a Salt-versus-Water law. These limits
should be stated near the corresponding result, not deferred only to the end,
because they are the reason the thesis uses a closure ledger instead of a
single tuned model.

### SAM/CSEM Relevance

The SAM/CSEM relevance of this work is methodological. The thesis identifies
which reduced-order terms should remain separate when CFD evidence is
translated into a systems-code component network: distributed pressure loss,
reset/development behavior, local fitting or cluster losses, junction/stub heat
ownership, heater and cooler source terms, passive wall loss, external
convection and radiation, test-section source/loss, recirculation flags, and
residual lanes. It also identifies what should not transfer directly:
diagnostic corner `K`, realized CFD wall heat flux, CFD mdot, validation
temperatures, and holdout/external targets. The result is a disciplined route
from CFD evidence to SAM-facing inputs and caveats, not a validation of SAM.

## Paper-Scale Integration

For a paper, compress the thesis into this structure:

| Paper section | Contents |
| --- | --- |
| Introduction | Need for CFD-to-1D closure discipline; central claim that local ledgers avoid hidden global multipliers. |
| CFD evidence and reduction | Salt-family evidence layer, retained windows, wall-BC setup, and 3D-to-1D reductions. |
| Model form | Steady `fluid+walls` equations and segment atlas. |
| Admission framework | Split policy, runtime leakage, source-envelope and uncertainty gates. |
| Results | CFD transport redistribution; junction/stub heat ownership; pressure basis/corner-K diagnostic result; PB2/PB3 negative thermal result; M0-M6 ladder status. |
| Discussion | What is ready for predictive modeling, what remains blocked, and why the blockers are meaningful. |
| Systems-code relevance | SAM/CSEM transfer of closure discipline without validation claim. |

The paper should not lead with final predictive scores unless a later frozen
scorecard lands. Until then, lead with the workflow and the strongest existing
results: CFD transport redistribution, `fluid+walls` model architecture,
admission discipline, junction/stub heat ownership, pressure non-admission, and
the wall/test-section negative result.

## Board Dispatch

The implementation queue for this plan is now documented in:

`operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md`

That note is the start-here document for agents claiming chapter-writing,
figure/table assembly, or trigger-gated refresh rows. It lists exact task IDs,
edit paths, read-only context, output contracts, validation commands, and
guardrails.

Current claimable rows added from this plan:

| Task ID | Purpose |
| --- | --- |
| `TODO-THESIS-CH1-CSEM-MOTIVATION-DRAFT` | Chapter 1 motivation and contribution. |
| `TODO-THESIS-CH3-CSEM-CFD-EVIDENCE-DRAFT` | Chapter 3 CFD evidence/database layer. |
| `TODO-THESIS-CH5-CSEM-FLUID-WALLS-DRAFT` | Chapter 5 `fluid+walls` model form. |
| `TODO-THESIS-CH6-CSEM-ADMISSION-UNCERTAINTY-DRAFT` | Chapter 6 admission framework and uncertainty. |
| `TODO-THESIS-CH7-CSEM-RESULTS-INTEGRATION-DRAFT` | Chapter 7 existing pressure, thermal, negative-result, and predictive-path results. |
| `TODO-THESIS-CH8-CSEM-SAM-LIMITATIONS-DRAFT` | SAM/CSEM relevance, limitations, and conclusions. |
| `TODO-THESIS-CSEM-FIGURE-TABLE-ASSEMBLY` | Chapter-ready figure/table incorporation package. |
| `TODO-THESIS-CSEM-POST-FREEZE-NARRATIVE-REFRESH` | Trigger-gated final predictive score refresh after frozen scorecard evidence lands. |
| `TODO-THESIS-CSEM-PRESSURE-ADMISSION-REFRESH` | Trigger-gated pressure narrative refresh after new pressure admission or diagnostic package lands. |
| `TODO-THESIS-CSEM-WALL-TS-CLOSURE-REFRESH` | Trigger-gated wall/test-section closure narrative refresh after admission or definitive falsification lands. |
