---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_modeling_approach_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_model_form_section.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_split_policy_section.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md
  - reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/13_two_tap_recirc_section_effective_pressure_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md
  - reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md
  - reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md
  - reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md
  - reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md
  - reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_current_draft_packet/README.md
  - operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md
tags: [thesis-dossier, current-sections, paper-ready, section-index]
related:
  - reports/thesis_dossier/Chapters_and_sections/dated/README.md
  - reports/thesis_dossier/README.md
task: AGENT-502
date: 2026-07-17
role: Coordinator/Writer/Cleaner
type: report
status: reference
supersedes: []
superseded_by:
---
# Current Sections

This folder is the copy-ready thesis/paper layer. Files here should be stable,
topic-named, and readable without chat context. Dated notes remain in
`../dated/` as the audit trail.

## Sections

| File | Use |
| --- | --- |
| `01_modeling_approach.md` | Methodology bridge from CFD evidence to 1D model construction. |
| `02_model_form_fluid_walls.md` | Stable definition of the steady `fluid+walls` model form. |
| `03_split_policy_and_evidence_classes.md` | Final split policy, evidence classes, and runtime leakage rules. |
| `04_upcomer_recirculation_modeling.md` | Paper-safe upcomer recirculation and hybrid-model section. |
| `05_junction_aware_ledgers.md` | Segment-only versus junction-aware ledgers for structured heat and pressure residuals. |
| `06_intermediate_model_forms_and_endpoint_strategy.md` | Thesis endpoint strategy, intermediate model-form bakeoff, numerical algorithms, cost comparison, and SAM-facing interpretation. |
| `07_wall_test_section_coupled_score_and_physics_plan.md` | Paper-facing coupled wall/test-section score result and next source/temperature-shape physics plan. |
| `08_thesis_claim_ledger.md` | Thesis-critical claim table mapping claims to evidence, split role, blockers, figure/table sources, and caveats. |
| `09_fluid_walls_segment_atlas.md` | One-table segment atlas for geometry, materials, pressure, thermal circuits, roles, recirculation, uncertainty, and admission status. |
| `10_uncertainty_chapter_package.md` | Chapter-ready package combining time-window, mesh/GCI, property, sensor, split, runtime, recirculation, and wall/test-section uncertainty. |
| `11_sam_facing_interpretation.md` | SAM-facing interpretation of branchwise losses, heat ledgers, recirculation flags, and admission status without claiming SAM validation. |
| `12_thesis_figures_and_diagrams_plan.md` | Figure brief for segment atlas diagrams, upcomer hybrid schematic, model-form ladder, junction-aware comparison, and SAM-facing flowchart. |
| `13_two_tap_recirc_section_effective_pressure_model.md` | Paper-ready two-tap pressure-basis and recirculating section-effective model section; explains why current corner rows block ordinary `K` while enabling a recirculation-aware residual lane. |
| `14_csem_narrative_integration_plan.md` | Chapter/paper narrative map for CSEM thesis writing, including evidence placement, figure/table ledger, ready-vs-blocked list, and draft prose bank. |
| `15_ch1_csem_motivation_and_contribution.md` | Chapter-ready CSEM motivation and contribution section framing CFD as high-fidelity reference, not experimental validation. |
| `16_ch3_csem_cfd_evidence_database.md` | Chapter-ready CFD evidence/database section using existing Salt-family paper evidence and trust boundaries. |
| `17_ch5_csem_fluid_walls_model.md` | Chapter-ready steady `fluid+walls` model-form section with equations, segment state, runtime contract, and figure placement. |
| `18_ch6_csem_closure_admission_uncertainty.md` | Chapter-ready closure admission and uncertainty section covering split, runtime leakage, source/property labels, pressure/thermal gates, and blockers. |
| `19_ch7_csem_pressure_thermal_predictive_results.md` | Chapter-ready results integration section for CFD redistribution, junction/stub heat, pressure diagnostics, wall/test-section negative results, and predictive-model path. |
| `20_ch8_csem_sam_limitations_conclusions.md` | Chapter-ready limitations, SAM/CSEM relevance, future-work, and conclusion section. |
| `21_csem_figure_table_incorporation_package.md` | Figure/table routing ledger for CSEM thesis chapters using existing diagrams, paper figures, LaTeX tables, and CSV ledgers. |
| `25_litrev_csem_thesis_incorporation.md` | LitRev-to-CSEM incorporation bridge for source envelopes, pressure-corner rules, model-form hierarchy, and dissertation insertion planning. |
| `26_predictive_model_studies_roadmap.md` | Study roadmap for strengthening the final predictive model thesis path while preserving split, source/property, residual-attribution, and blocked-scorecard discipline. |

## Study Dispatch Packages

| Package | Use |
| --- | --- |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md` | Board-backed S0-S6 portfolio, analysis requirements, figure/table wishlist, and dependency order for continuing thesis writing and model-study work. |
| `operational_notes/07-26/21/2026-07-21_THESIS_RESEARCH_STUDIES_BOARD_DISPATCH.md` | Start-here handoff for agents claiming S0-S3 writing integration, S4 recirculation guard, S5 release gate, S6 frozen scorecard, or quantitative figure/table assembly. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/README.md` | Board-backed S7-S11 continuation package for sensor mapping, wall/test-section candidates, upcomer onset/exchange UQ, pressure/F6 anchor UQ, candidate-specific release refresh, and negative-results writing. |
| `operational_notes/07-26/21/2026-07-21_THESIS_NEXT_STUDIES_BOARD_DISPATCH.md` | Start-here handoff for the next thesis studies queue and rows to claim rather than duplicate. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md` | Publication-grade execution workflow, required artifacts, templates, claim/admission rules, validation checklist, and per-study packets for running S7-S11 rigorously. |
| `operational_notes/07-26/21/2026-07-21_THESIS_STUDY_EXECUTION_DOCUMENTATION_PACKAGE.md` | Start-here handoff for applying the execution contract to each thesis study row. |
| `operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md` | Current post-S8/S9/S10 continuation handoff; routes implementers to S12, S13, S14, and trigger-gated S15 before any S11/S6 refresh. |
| `operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md` | Salt2/Salt4 upcomer visual-evidence insertion note for F-03A, including exact source paths, chapter placement, and no-admission caption guardrails. |
| `work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/README.md` | Thesis-facing CFD run/QoI chart: one wide CSV row per CFD case with `mdot`, TP, and TW targets; `val_salt2` is grouped in `holdout_test` with `external_test` subtype. |
| `work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md` | Cross-workspace contract for parallel LaTeX writers and `ethan_runs` artifact producers; use before importing current sections into the actual CSEM dissertation LaTeX. |
| `operational_notes/07-26/21/2026-07-21_THESIS_LATEX_PARALLEL_WORKFLOW_CONTRACT.md` | Start-here handoff for claimable LaTeX chapter sync rows, artifact handoff fields, runtime-leakage checks, and papers-board promotion. |

## Editing Rule

Edit these files when prose is ready to be incorporated into the thesis or a
paper. Preserve provenance by adding dated source notes or work-product
packages to frontmatter. Keep speculative, meeting-specific, or transient
material in `../dated/` until it is consolidated.
