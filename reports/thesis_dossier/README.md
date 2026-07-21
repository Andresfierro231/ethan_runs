---
provenance:
  - .agent/STATE.md
  - .agent/BLOCKERS.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md
  - reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md
  - reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md
  - operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md
tags: [thesis-dossier, thesis-source, map-of-content, outline, chapters-and-sections]
related:
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/mentor_thesis_outline.md
  - reports/thesis_dossier/Chapters_and_sections/README.md
  - reports/powerpoint/README.md
  - operational_notes/maps/README.md
  - .agent/STATE.md
  - .agent/BLOCKERS.md
task: AGENT-490
date: 2026-07-17
role: Coordinator/Writer/Cleaner
type: report
status: reference
supersedes: []
superseded_by:
---
# Thesis Dossier

This folder is the clean thesis front door. It should stay small:

- `README.md`: where to start and what is current.
- `mentor_thesis_outline.md`: corrected canonical proposed outline and chapter
  structure.
- `Outline.md`: internal roadmap with model forms, equations, claims, and work
  plan.
- `Chapters_and_sections/current/`: stable copy-ready thesis/paper sections.
- `Chapters_and_sections/dated/`: dated chapter/section material and context
  notes kept as provenance.

PowerPoint-specific outlines and decks live outside this dossier in
`reports/powerpoint/`.

## Open First

1. `reports/thesis_dossier/mentor_thesis_outline.md`
   - Corrected canonical proposed master's thesis outline from July 20 advisor
     feedback.
   - Use this as the chapter structure and thesis framing source of truth.

2. `reports/thesis_dossier/Outline.md`
   - Internal execution roadmap.
   - Includes the `fluid+walls` model form, segment pressure/thermal equations,
     split policy, claim ledger, and figure/table starter bank.
   - Keep it consistent with `mentor_thesis_outline.md` when updating chapter
     structure.

3. `operational_notes/07-26/18/2026-07-18_THESIS_NEXT_CONTEXT_AND_STEPS.md`
   - Latest thesis restart note for the external UT master's scaffold,
     thesis-safe claims, active blockers, strengthening research avenues, and
     exact next task sequence.

4. `reports/thesis_dossier/Chapters_and_sections/current/README.md`
   - Copy-ready thesis/paper section index.

5. `operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md`
   - Claimable board-task queue for turning the CSEM narrative integration map
     into chapter drafts, figure/table assembly, and trigger-gated refreshes.

6. `operational_notes/07-26/21/2026-07-21_THESIS_LITREV_CSEM_INCORPORATION_START_HERE.md`
   - LitRev-to-CSEM incorporation bridge for adding source-envelope,
     pressure-corner, model-form, heat-loss, and admission-gate material to the
     external master's dissertation through the papers board.

7. Current thesis sections:
   - `reports/thesis_dossier/Chapters_and_sections/current/01_modeling_approach.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/02_model_form_fluid_walls.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/03_split_policy_and_evidence_classes.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/06_intermediate_model_forms_and_endpoint_strategy.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/07_wall_test_section_coupled_score_and_physics_plan.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md`
   - `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md`

8. `operational_notes/07-26/21/2026-07-21_THESIS_RESEARCH_STUDIES_BOARD_DISPATCH.md`
   - Start-here note for the current thesis research-study board dispatch.
   - Use it to claim S0-S3 writing integration, S4 recirculation guard, S5
     source/property split release, S6 frozen scorecard, or the quantitative
     figure/table package without duplicating active S0-S3 implementation.

9. `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md`
   - Study portfolio, figure/table wishlist, dependency order, and board-row
     proposal summary for continuing thesis writing and research rigorously.

10. `work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/README.md`
   - Board-backed S7-S11 and negative-results continuation plan for unblocking
     or falsifying a runtime-legal frozen candidate before S6.

11. `operational_notes/07-26/21/2026-07-21_THESIS_NEXT_STUDIES_BOARD_DISPATCH.md`
   - Start-here handoff for the next thesis studies queue and rows to claim
     rather than duplicate.

12. `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md`
   - Publication-grade execution workflow, gate templates, claim/admission
     rules, validation checklist, and per-study packets for S7-S11.

13. `operational_notes/07-26/21/2026-07-21_THESIS_STUDY_EXECUTION_DOCUMENTATION_PACKAGE.md`
   - Start-here handoff for applying the execution contract to each thesis
     study row.

14. `operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md`
   - Current post-S8/S9/S10 continuation handoff for claiming S12 thermal
     shape, S13 upcomer exchange, S14 pressure/F6, and trigger-gated S15 before
     any S11/S6 refresh.

15. `operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md`
   - Start-here note for using existing Salt2/Salt4 upcomer velocity-arrow and
     velocity-profile visuals as diagnostic recirculation evidence paired with
     thesis schematic F-03.

16. `reports/thesis_dossier/Chapters_and_sections/README.md`
   - Index explaining the current/dated section layers.

17. `reports/powerpoint/README.md`
   - Index of PowerPoint outlines and deck files.

18. `.agent/STATE.md` and `.agent/BLOCKERS.md`
   - Generated current-state and blocker registers. Trust these over stale
     prose when there is a conflict.

## Current Thesis Story

The thesis is about a defensible CFD-to-1D closure workflow for the TAMU
molten-salt natural-circulation loop. Ethan OpenFOAM CFD is the current
high-fidelity reference, not experimental validation.

The current model target is steady `fluid+walls`: each segment carries a fluid
state, wall/material stack, pressure model, thermal circuit, source/sink role,
boundary-layer/development state, recirculation/admission flags, and uncertainty
status. The contribution is a branchwise closure ledger, not one tuned global
coefficient.

The final predictive split is now:

| Role | Rows |
| --- | --- |
| final training | `salt1_nominal`, `salt2_jin_nominal`, `salt3_jin_nominal`, `salt4_nominal` |
| training support | `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`, `salt4_hi5q` |
| holdout/testing | `salt2_lo5q`, `salt2_hi5q` |
| external test | `val_salt2`, after matching heat-loss/admission package |

Older Salt2/Salt3/Salt4 train-validation-holdout language remains dated
method-development context only.

## Current Blockers

Use `.agent/BLOCKERS.md` for live status. As of the July 17 dossier refresh, the
human-facing open set is:

- `predictive-wall-test-section-submodels`
- `upcomer-onset-data-sparsity`
- `f6-friction-re-correction`

Resolved or superseded blockers should not be reintroduced in new thesis prose
unless a later dated note reopens them.

## Figure And Table Leads

| Candidate | Source | Use |
| --- | --- | --- |
| Pressure decomposition figures | `work_products/2026-07/2026-07-09/2026-07-09_pressure_decomposition_figures/` | Hydraulic closure chapter. |
| Time-series uncertainty table | `work_products/2026-07/2026-07-13/2026-07-13_time_series_uncertainty_story/` | Steady-state and uncertainty chapter. |
| Literature gate matrix | `work_products/2026-07/2026-07-13/2026-07-13_litrev_todo_campaign_index/` | Literature-to-modeling bridge. |
| Predictive external-BC scorecards | `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/` | Forward-model pathway. |
| Heat-loss discrepancy study | `work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/README.md` | Boundary-model results and limitations. |
| `fluid+walls` model form | `operational_notes/07-26/16/2026-07-16_fluid_walls_steady_1d_model_form.md` | Final 1D model equations and segment ledger. |
| Thesis claim ledger | `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md` | Master table mapping every thesis claim to evidence, split role, blocker, source, and caveat. |
| `fluid+walls` segment atlas | `reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md` | Loop-region implementation atlas for model and admission status. |
| Uncertainty package | `reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md` | Time-window, mesh/GCI, property, sensor, split, and model-form uncertainty chapter source. |
| SAM-facing interpretation | `reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md` | Systems-code interpretation without claiming SAM validation. |
| Thesis figures and diagrams | `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md` | Figure brief for segment atlas diagrams, upcomer hybrid schematic, model-form ladder, and SAM-facing flowchart. |
| Initial thesis SVG figures | `reports/thesis_dossier/figures/README.md` | Static SVG figure set, captions, claim crosswalk, and source manifest. |
| Upcomer recirculation visual evidence | `operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md` | Exact Salt4 Jin and Salt2 validation/external upcomer velocity-arrow paths, Salt2 Jin velocity-profile fallback, and caption guardrails for F-03A. |
| CSEM narrative integration map | `reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md` | Chapter/paper routing plan that places existing reports, figures, model-form math, CFD evidence, LitRev claims, negative results, and blocked final-score claims. |
| CSEM motivation and contribution | `reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md` | Chapter-ready introduction framing TAMU loop need, CFD as high-fidelity reference, and the branchwise CFD-to-1D closure/admission contribution. |
| CSEM current draft packet | `work_products/2026-07/2026-07-21/2026-07-21_thesis_csem_current_draft_packet/README.md` | Ordered reading manifest, reviewer checklist, and trigger-gated refresh ledger for the current CSEM thesis package. |
| CSEM limitations and SAM relevance | `reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md` | Chapter-ready limitations, SAM/CSEM relevance, future-work, and conclusion prose without SAM-validation or final predictive-score claims. |
| CSEM board dispatch | `operational_notes/07-26/21/2026-07-21_THESIS_CSEM_BOARD_DISPATCH.md` | Claimable task queue and start-here instructions for chapter drafts, figure/table assembly, and trigger-gated narrative refreshes. |
| LitRev-to-CSEM incorporation bridge | `reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md` | Chapter-level bridge for importing LitRev source envelopes, pressure-corner rules, CFD postprocessing contracts, model-form hierarchy, heat-loss separation, and future-work triggers into the external CSEM dissertation. |
| Predictive model studies roadmap | `reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md` | Study sequence for strengthening final predictive-model claims while separating train/support, validation, holdout, and external-test evidence. |
| Thesis research studies board dispatch | `work_products/2026-07/2026-07-21/2026-07-21_thesis_research_studies_board_dispatch/README.md` | Board-backed S0-S6 study portfolio, dependency order, and figure/table wishlist for continuing thesis writing without duplicating active S0-S3 work or overclaiming final predictive results. |
| Thesis next studies board dispatch | `work_products/2026-07/2026-07-21/2026-07-21_thesis_next_studies_board_dispatch/README.md` | Board-backed S7-S11 and negative-results continuation plan for sensor mapping, wall/test-section candidates, upcomer onset/exchange UQ, pressure/F6 anchor UQ, and candidate-specific release refresh. |
| Thesis study execution documentation package | `work_products/2026-07/2026-07-21/2026-07-21_thesis_study_execution_documentation_package/README.md` | Publication-grade workflow, required artifacts, templates, claim/admission rules, and validation checklist for running S7-S11 rigorously. |
| Post-S8/S10 evidence requirements | `operational_notes/07-26/21/2026-07-21_THESIS_POST_S8_S10_EVIDENCE_AND_STUDY_REQUIREMENTS.md` | Current start-here note after S8/S9/S10 completed with `0` S11-ready candidates; routes follow-on work to S12, S13, S14, and trigger-gated S15. |

## Update Policy

Update this dossier when a result changes the thesis story, a blocker changes
state, a current section becomes the better thesis/paper entry point, or a new
weekly presentation should be reflected in thesis context.

Keep routine task status in the task package, journal, import manifest, and
topic maps. Keep dated audit notes in `Chapters_and_sections/dated/` and
PowerPoint material in `reports/powerpoint/`.
