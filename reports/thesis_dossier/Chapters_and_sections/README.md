---
provenance:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/dated/README.md
tags: [thesis-dossier, chapters-and-sections, thesis-source, section-index]
related:
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/dated/README.md
task: AGENT-502
date: 2026-07-17
role: Coordinator/Writer/Cleaner
type: report
status: reference
supersedes: []
superseded_by:
---
# Chapters And Sections

This folder has two layers:

- `current/`: stable, topic-named thesis/paper sections.
- `dated/`: dated notes, context bridges, and historical section drafts kept as
  provenance.

Use `current/` as the writing surface for material that should be incorporated
into the thesis or a paper. Use `dated/` when preserving audit history, meeting
context, or transitional notes.

## Current Sections

| File | Use |
| --- | --- |
| `current/01_modeling_approach.md` | Comprehensive CFD-to-1D methodology bridge. |
| `current/02_model_form_fluid_walls.md` | Steady `fluid+walls` model form and equations. |
| `current/03_split_policy_and_evidence_classes.md` | Final split policy, evidence classes, and runtime leakage rules. |
| `current/04_upcomer_recirculation_modeling.md` | Upcomer recirculation and hybrid-model guardrails. |
| `current/05_junction_aware_ledgers.md` | Junction-aware versus segment-only ledgers for structured heat and pressure residuals. |
| `current/06_intermediate_model_forms_and_endpoint_strategy.md` | Endpoint strategy, model-form bakeoff, numerical algorithms, and SAM-facing implications. |
| `current/07_wall_test_section_coupled_score_and_physics_plan.md` | Coupled wall/test-section score result and next source/temperature-shape physics plan. |
| `current/08_thesis_claim_ledger.md` | Claim-to-evidence ledger with split role, blocker, figure/table source, and caveat. |
| `current/09_fluid_walls_segment_atlas.md` | Loop-region atlas for `fluid+walls` implementation and admission status. |
| `current/10_uncertainty_chapter_package.md` | Uncertainty chapter package spanning time window, mesh/GCI, properties, sensors, split, and model-form trust boundaries. |
| `current/11_sam_facing_interpretation.md` | SAM-facing interpretation section with explicit no-SAM-validation boundary. |
| `current/12_thesis_figures_and_diagrams_plan.md` | Figure brief for the thesis diagram package and future figure agent. |
| `current/14_csem_narrative_integration_plan.md` | CSEM thesis/paper chapter integration map with exact evidence, figure/table, ready-vs-blocked, and draft-prose routing. |
| `current/26_predictive_model_studies_roadmap.md` | Studies to perform and document on the path to the final predictive model, including baseline, external BC, pressure, heat-loss, recirculation, split-release, and final scorecard lanes. |

## Dated Sources

The dated audit trail is indexed at `dated/README.md`. Dated files should not be
the default thesis-writing surface after their content has been consolidated
into `current/`.
