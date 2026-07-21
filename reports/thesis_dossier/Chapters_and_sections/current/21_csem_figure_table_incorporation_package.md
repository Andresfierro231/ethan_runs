---
provenance:
  - operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/figures/README.md
  - reports/thesis_dossier/figures/figure_claim_crosswalk.csv
  - reports/thesis_dossier/figures/source_manifest.csv
  - ../papers/UTexas_Research/3d_analysis/figures/README.md
  - ../papers/UTexas_Research/3d_analysis/notes/asset_import_log.md
  - ../papers/UTexas_Research/3d_analysis/tables/table_artifact_provenance.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt_case_matrix.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt_family_quantitative_summary.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_salt2_matched_case_summary.tex
  - ../papers/UTexas_Research/3d_analysis/tables/table_trust_boundaries.tex
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_enrichment_writing_pass/figure_table_insertions.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/figure_table_ledger_update.csv
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/README.md
  - figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg
  - figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.svg
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_x.svg
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.svg
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_y.svg
  - figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_z.svg
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_val_salt2_upcomer_side_neg_x_arrow_view/README.md
tags: [thesis-section, current-section, csem, figures, tables, incorporation-ledger]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
task: TODO-THESIS-CSEM-FIGURE-TABLE-ASSEMBLY
date: 2026-07-21
role: Writer/Reviewer/Figures
type: thesis-section
status: current-draft
supersedes: []
superseded_by:
---
# CSEM Figure And Table Incorporation Package

## Purpose

This package is the figure/table routing ledger for the ready CSEM thesis
sections. It does not edit images, regenerate figures, or create new numeric
overlays. It tells the thesis writer where existing conceptual diagrams,
quantitative CFD figures, paper tables, and CSV ledgers belong.

## Placement Summary

| Thesis area | Primary assets |
| --- | --- |
| Chapter 3 CFD evidence | 3D paper Salt-family figures and artifact/case tables. |
| Chapter 5 `fluid+walls` model | Thesis diagrams F-01 and F-02. |
| Chapter 6 admission and uncertainty | Claim ledger, uncertainty tables, trust boundaries, LitRev contract tables, F-03/F-03A/F-04 as needed. |
| Chapter 7 results | 3D paper result figures, junction heat tables, PB2/PB3 negative-result tables, F-03A recirculation visual pair, M0-M6 ladder F-05. |
| Chapter 8 SAM/CSEM relevance | SAM-facing flowchart F-06. |

## Thesis Conceptual Diagrams

| ID | Source path | Target section | Caption draft | Claim IDs | Status and caveat |
| --- | --- | --- | --- | --- | --- |
| F-01 | `reports/thesis_dossier/figures/svg/F01_fluid_walls_loop_segment_atlas.svg` | Chapter 5 model form | Loop-region atlas for the steady `fluid+walls` model, showing named regions and local pressure, heat, recirculation, uncertainty, and admission lanes. | CL-03, CL-11, CL-16, CL-17 | Ready conceptual diagram. Do not show target values as runtime inputs. |
| F-02 | `reports/thesis_dossier/figures/svg/F02_segment_local_ledger_inset.svg` | Chapter 5 equations or Chapter 6 admission | Segment-local pressure and thermal ledger inset, separating model slots from coefficient admission. | CL-02, CL-03, CL-17, CL-18 | Ready conceptual diagram. Slot presence does not imply admitted coefficient. |
| F-03 | `reports/thesis_dossier/figures/svg/F03_upcomer_hybrid_schematic.svg` | Chapter 6 recirculation uncertainty or Chapter 7 limitations | Hybrid upcomer schematic with throughflow plus recirculation/exchange lane. | CL-14, CL-15 | Ready conceptual diagram. Ordinary single-stream labels remain blocked in recirculating rows. |
| F-03A | Existing external CFD visual assets listed below | Chapter 5 upcomer model form, Chapter 6 recirculation gate, or Chapter 7 negative/diagnostic results | Salt2/Salt4 upcomer velocity-arrow evidence paired with the F-03 schematic to show why ordinary single-stream and 2D-axisymmetric upcomer closure are not adequate for recirculating regimes. | CL-14, CL-15 | Ready as existing diagnostic visual evidence. Do not caption as admitted ordinary `Nu/f_D/K` or exchange-cell closure. |
| F-04 | `reports/thesis_dossier/figures/svg/F04_junction_aware_vs_segment_only.svg` | Chapter 7 junction/stub and pressure ownership result | Segment-only versus junction-aware ownership, with `val_salt2` junction heat and diagnostic corner-K caveat. | CL-11, CL-12, CL-13 | Ready conceptual diagram. `val_salt2` is external-test evidence, not training input. |
| F-05 | `reports/thesis_dossier/figures/svg/F05_model_form_ladder.svg` | Chapter 7 predictive-model path | M0-M6 model-form ladder from setup-only baseline to pending frozen predictive candidate. | CL-04, CL-05, CL-23, CL-24 | Ready conceptual diagram. M6 is pending until final scorecard lands. |
| F-06 | `reports/thesis_dossier/figures/svg/F06_sam_facing_flowchart.svg` | Chapter 8 SAM/CSEM relevance | SAM-facing closure/admission flowchart transferring ledger discipline while not claiming SAM validation. | CL-02, CL-16, CL-20, CL-25 | Ready conceptual diagram. No SAM validation claim. |

## Quantitative CFD Figures

| Source path | Target section | Caption draft | Status and caveat |
| --- | --- | --- | --- |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_heat_loss.pdf` | Chapter 3 CFD evidence and Chapter 7 thermal results | Salt 2 loopwise heat-loss redistribution from the promoted Salt paper evidence layer. | Ready. Grouped heat channels depend on thermal-role metadata. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt4_heat_loss.pdf` | Chapter 3 CFD evidence and Chapter 7 thermal results | Salt 4 loopwise heat-loss redistribution from the promoted Salt paper evidence layer. | Ready. Salt-only evidence, not Water synthesis. |
| `figures/figures_rendered/paraview_velocity_arrows/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows.svg` | Chapter 5 upcomer model form or Chapter 7 recirculation result | Salt4 Jin upcomer velocity-arrow render showing the flow field used as diagnostic evidence for recirculation-dominated model-form selection. | Ready existing SVG; PDF/PNG siblings exist. Diagnostic only; no ordinary upcomer or exchange-cell coefficient admission. |
| `figures/figures_rendered/paraview_velocity_arrows_orthogonal/viscosity_screening_salt_test_4_jin_coarse_mesh/upcomer/svg/viscosity_screening_salt_test_4_jin_coarse_mesh_upcomer_velocity_magnitude_arrows_side_x.svg` | Chapter 5 upcomer model form or Chapter 7 recirculation result | Salt4 Jin upcomer velocity-arrow side view normal to `x`, orthogonal to the original front-view camera. | Ready new SVG; PDF/PNG siblings exist. Diagnostic only; use to show the upcomer from the normal camera direction, not as closure admission. |
| `figures/figures_rendered/paraview_velocity_arrows/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows.svg` | Chapter 6 split/admission caveat or Chapter 7 recirculation result | Salt2 validation/external upcomer velocity-arrow render, useful as a visual companion for why the external Salt2 row remains diagnostic/test evidence rather than ordinary closure training evidence. | Ready existing SVG; PDF/PNG siblings exist. Label as `val_salt2` external/native source, not nominal Salt2 Jin training evidence. |
| `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_x.svg` | Chapter 6 split/admission caveat or Chapter 7 recirculation result | Salt2 validation/external upcomer side view normal to `x`, generated from the staged ParaView render input as an orthogonal companion to the liked front-view image. | Ready new SVG; PDF/PNG siblings exist. Diagnostic external/test visual only; do not use as closure training or admission evidence. |
| `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_neg_x.svg` | Chapter 6 split/admission caveat or Chapter 7 recirculation result | Salt2 validation/external upcomer opposite side view normal to `-x`, generated as the reverse camera side of `side_x`. | Ready new SVG; PDF/PNG siblings exist. Diagnostic external/test visual only; x-normal views are slender projections and should not be overinterpreted as closure evidence. |
| `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_y.svg` | Chapter 6 split/admission caveat or Chapter 7 recirculation result | Salt2 validation/external upcomer side view normal to `y`; this is the clearest page-aligned loop-head view in the orthogonal set. | Ready new SVG; PDF/PNG siblings exist. Diagnostic external/test visual only; do not use as closure training or admission evidence. |
| `figures/figures_rendered/paraview_velocity_arrows_orthogonal/val_salt_test_2_coarse_mesh_laminar/upcomer/svg/val_salt_test_2_coarse_mesh_laminar_upcomer_velocity_magnitude_arrows_side_z.svg` | Chapter 6 split/admission caveat or Chapter 7 recirculation result | Salt2 validation/external upcomer side view normal to `z`, preserving the original front-view axis convention while using the requested `side_z` suffix. | Ready new SVG; PDF/PNG siblings exist. Diagnostic external/test visual only; do not use as closure training or admission evidence. |
| `registry/salt2/ethan_modern_runs_staged/salt_test_2_jin/viscosity_screening_salt_test_2_jin_coarse_mesh/plots/velocity_profiles/svg/registry_velocity_final.svg` | Chapter 5 or appendix support | Salt2 Jin nominal registry velocity-profile fallback if the thesis needs Salt2 nominal evidence rather than the external Salt2 arrow render. | Ready existing SVG. Velocity profile, not the same artifact as the external Salt2 upcomer arrow render. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_azimuthal_means.pdf` | Chapter 3 CFD evidence | Salt 2 circumferential-mean azimuthal wall-transport comparison. | Ready. Trend-level diagnostic, not local closure admission. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt4_azimuthal_means.pdf` | Chapter 3 CFD evidence | Salt 4 circumferential-mean azimuthal wall-transport comparison. | Ready. Trend-level diagnostic, not local closure admission. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_friction_pressure_zoomed.pdf` | Chapter 3 CFD evidence and Chapter 7 pressure result | Matched Salt 2 friction and wall-registered pressure-gradient redistribution. | Ready diagnostic. Do not treat as admitted pressure closure. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_thermal_resistance.pdf` | Chapter 3 CFD evidence and Chapter 7 thermal result | Matched Salt 2 effective thermal transport and resistance comparison. | Ready diagnostic. Effective, QC-masked metrics only. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_family_branch_thermal_safe_subset.pdf` | Chapter 7 thermal result | Salt-family safe-branch effective thermal comparison. | Ready. Headline branch set is scrutiny-cleared only. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt2_branch_thermal_safe_subset.pdf` | Chapter 7 matched Salt 2 mechanism | Matched Salt 2 branch-level effective thermal comparison on the safe subset. | Ready. Corners and junctions remain excluded from this branch-local view. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_branch_trust_heatmap.pdf` | Appendix or Chapter 6 support | Branch trust heatmap explaining why some branch claims are withheld. | Support-only. Not a headline result. |
| `../papers/UTexas_Research/3d_analysis/figures/fig_salt_safe_branch_support.pdf` | Appendix or Chapter 6 support | QC support for safe-branch thermal promotion. | Support-only. Not a headline result. |

## Tables And Ledgers

| Source path | Target section | Table role | Status and caveat |
| --- | --- | --- | --- |
| `../papers/UTexas_Research/3d_analysis/tables/table_artifact_provenance.tex` | Chapter 3 or appendix | Evidence hierarchy and artifact provenance map. | Ready. Promotion surface and numeric source package are distinct. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt_case_matrix.tex` | Chapter 3 | Case definitions and retained windows. | Ready. Preserve Salt 2 validation window `8598-8602 s`. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt_family_quantitative_summary.tex` | Chapter 7 | Quantitative family heat and safe-branch thermal summary. | Ready. Hotspots depend on grouped thermal-role definitions. |
| `../papers/UTexas_Research/3d_analysis/tables/table_salt2_matched_case_summary.tex` | Chapter 7 | Quantitative matched Salt 2 pressure/thermal mechanism summary. | Ready. Preserve continuation caveat. |
| `../papers/UTexas_Research/3d_analysis/tables/table_trust_boundaries.tex` | Chapter 6 and limitations | Allowed/disallowed wording for 3D paper evidence. | Ready. Use to prevent overclaiming. |
| `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md` | Chapter 6 and appendix | Master claim-to-evidence ledger. | Ready. Add rows before introducing new claims. |
| `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md` | Chapter 5 and appendix | Segment atlas and admission map. | Ready. Holdout/external realized heat/pressure are target-only or diagnostic. |
| `work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder/coupled_delta_vs_m3.csv` | Chapter 7 | PB2/PB3 negative-result delta table. | Ready. `0/4` admitted. |
| `work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/model_form_scores.csv` | Chapter 7 | M0-M4 score/status table. | Ready. Partial/diagnostic rows only; M6 not scored. |
| `work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/scorecard_summary.csv` | Chapter 7 | Final scorecard shell status. | Ready as contract. No final scores. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv` | Chapter 5 or literature chapter | Source-bounded reduced-model candidates. | Ready as gate inventory. All candidates are `not admitted here`. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv` | Chapter 6 and Chapter 7 pressure | Pressure-basis and corner-naming rules. | Ready as method/admission gate. Current corner rows remain diagnostic. |
| `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv` | Chapter 4 or Chapter 6 | Required CFD reduction fields for pressure, heat, recirculation, and naming. | Ready as contract. Missing fields keep rows diagnostic. |

## Enrichment Insertions

The enrichment pass adds these near-term quantitative callouts. They are table
or ledger insertions, not new figure generation.

| Source artifact | Target section | Use | Caveat |
| --- | --- | --- | --- |
| `work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/baseline_control_surface.csv` | Chapter 7 | Baseline control-surface table for current legal model coverage. | No final predictive accuracy. |
| `work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/first_key_study_wave_status.csv` | Chapter 6 or 7 | S0-S3 release-gate status table. | Infrastructure and non-admission evidence only. |
| `work_products/2026-07/2026-07-21/2026-07-21_predictive_first_key_studies_wave/external_bc_completion_matrix.csv` | Chapter 5 | External-BC dictionary coverage/status table. | Do not fill setup gaps from realized CFD response fields. |
| `work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_2_split_heat_loss_evidence/heat_path_evidence_matrix.csv` | Chapter 7 | Heat-path residual-owner table. | Do not absorb heat-path residuals into internal `Nu`. |
| `work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_same_qoi_scientific_synthesis/attempt_outcome_matrix.csv` | Chapter 7 | Pressure-corner attempt/outcome matrix. | No component K, F6, clipped K, or global multiplier. |
| `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight/exchange_variable_availability.csv` | Chapter 6 or 8 | Recirculation exchange-variable availability table. | No exchange-cell or ordinary upcomer closure admission. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/diagnostic_claim_matrix.csv` | Chapter 6 or 7 | Diagnostic claim-boundary matrix for recirculation, energy, pressure, and thermal residual evidence. | Every row is diagnostic or blocked; no admitted coefficient or final predictive score. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/recirculation_guard_evidence_table.csv` | Chapter 5 or 7 | RAF/RMF/SVF evidence used as recirculation guard and missing-exchange-state queue. | Reverse-flow evidence disables ordinary labels but does not fit exchange cells. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/ordinary_closure_exclusion_table.csv` | Chapter 6 | Ordinary single-stream closure exclusion table for upcomer and adjacent recirculating branches. | Ordinary `Nu/f_D/K` admitted rows remain zero. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_diagnostic_evidence_integration/residual_ownership_matrix.csv` | Chapter 7 | Pressure and thermal residual owner matrix with forbidden absorption paths. | Residual ownership is attribution, not runtime input authorization. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/ordinary_closure_disable_table.csv` | Chapter 6 | Source S4 table supporting ordinary upcomer closure exclusion. | Use as source evidence only; not a new fitted table. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/reverse_flow_onset_evidence_ledger.csv` | Chapter 7 | Source S4 reverse-flow/onset evidence ledger. | Caption as diagnostic recirculation evidence. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/throughflow_recirc_variable_contract.csv` | Chapter 5 or 8 | Future throughflow-plus-recirculation variable contract. | Variables are a missing-field contract, not current Fluid inputs. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/caption_bank.md` | Chapter 5 or 7 | Caption source for the F-03/F-03A upcomer visual pair and exchange-QOI blocked-contract tables. | Use for diagnostic recirculation visuals only; exchange QOIs remain requirements, not coefficients. |

## Ready Versus Blocked Figure Work

Ready now:

- use the six existing thesis SVG diagrams as conceptual figures;
- use the 3D paper PDFs as quantitative CFD evidence figures;
- use existing LaTeX tables and CSV ledgers as source tables;
- draft captions and caveats in prose.

Blocked or out of scope for this row:

- exporting new PDF/PNG variants from SVG;
- editing SVG artwork;
- regenerating 3D paper plots;
- adding quantitative overlays to thesis conceptual diagrams;
- adding final predictive-score figures before frozen scorecard evidence
  exists;
- adding admitted component-K or wall/test-section closure figures before
  admission evidence exists.

## Runtime And Split Caveats For Captions

Captions should carry these caveats where relevant:

- realized CFD `wallHeatFlux` is target/diagnostic evidence, not a predictive
  runtime input;
- CFD `mdot` is not a predictive runtime input;
- imposed CFD cooler duty and realized test-section heat are not final
  runtime inputs;
- TP/TW temperatures are score targets, not runtime inputs;
- holdout and external rows are not fit/tune/model-selection rows;
- diagnostic pressure K, internal Nu, and upcomer ordinary-pipe coefficients
  are not admitted unless a later package says so;
- SAM-facing figures show transfer of closure discipline, not SAM validation.
