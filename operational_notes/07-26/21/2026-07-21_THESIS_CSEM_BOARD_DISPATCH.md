---
provenance:
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md
  - reports/thesis_dossier/Chapters_and_sections/current/09_fluid_walls_segment_atlas.md
  - reports/thesis_dossier/Chapters_and_sections/current/10_uncertainty_chapter_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/11_sam_facing_interpretation.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
  - ../papers/UTexas_Research/3d_analysis/sections/01_introduction_and_claim.tex
  - ../papers/UTexas_Research/3d_analysis/sections/07_conclusions.tex
tags: [thesis-handoff, csem, board-dispatch, writing, start-here]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - .agent/BOARD.md
  - .agent/status/2026-07-21_TODO-THESIS-CSEM-BOARD-DISPATCH-2026-07-21.md
task: TODO-THESIS-CSEM-BOARD-DISPATCH-2026-07-21
date: 2026-07-21
role: Coordinator/Writer
type: operational_note
status: complete
supersedes: []
superseded_by:
---
# Thesis CSEM Board Dispatch

Use this note when claiming CSEM/thesis writing work from `.agent/BOARD.md`.
It turns the narrative integration plan into small, non-overlapping tasks that
future agents can implement without reading chat.

## Why This Exists

`reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md`
now maps the current evidence into thesis and paper sections. The next useful
step is chapter assembly, but agents need exact board rows, allowed edit paths,
read-only context, and guardrails so they do not overlap files or promote
diagnostic evidence.

## Open First

Every CSEM writing agent should open these files before drafting:

1. `AGENTS.md`
2. `.agent/BOARD.md`
3. `.agent/FILE_OWNERSHIP.md`
4. `.agent/ROLES.md`
5. `.agent/BLOCKERS.md`
6. `reports/thesis_dossier/README.md`
7. `reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md`
8. `reports/thesis_dossier/Chapters_and_sections/current/08_thesis_claim_ledger.md`

Then open the row-specific context listed on the board row.

## Claimable Rows

Rows added on `2026-07-21`:

| Task ID | Start condition | Output file |
| --- | --- | --- |
| `TODO-THESIS-CH1-CSEM-MOTIVATION-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md` |
| `TODO-THESIS-CH3-CSEM-CFD-EVIDENCE-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/16_ch3_csem_cfd_evidence_database.md` |
| `TODO-THESIS-CH5-CSEM-FLUID-WALLS-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/17_ch5_csem_fluid_walls_model.md` |
| `TODO-THESIS-CH6-CSEM-ADMISSION-UNCERTAINTY-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/18_ch6_csem_closure_admission_uncertainty.md` |
| `TODO-THESIS-CH7-CSEM-RESULTS-INTEGRATION-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/19_ch7_csem_pressure_thermal_predictive_results.md` |
| `TODO-THESIS-CH8-CSEM-SAM-LIMITATIONS-DRAFT` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/20_ch8_csem_sam_limitations_conclusions.md` |
| `TODO-THESIS-CSEM-FIGURE-TABLE-ASSEMBLY` | Ready now | `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md` |
| `TODO-THESIS-CSEM-POST-FREEZE-NARRATIVE-REFRESH` | Trigger-gated after frozen predictive scorecard | `reports/thesis_dossier/Chapters_and_sections/current/22_csem_post_freeze_predictive_results_addendum.md` |
| `TODO-THESIS-CSEM-PRESSURE-ADMISSION-REFRESH` | Trigger-gated after pressure admission or updated diagnostic package | `reports/thesis_dossier/Chapters_and_sections/current/23_csem_pressure_admission_refresh.md` |
| `TODO-THESIS-CSEM-WALL-TS-CLOSURE-REFRESH` | Trigger-gated after wall/test-section admission or definitive falsification package | `reports/thesis_dossier/Chapters_and_sections/current/24_csem_wall_test_section_closure_refresh.md` |

## Suggested Task Sequence

1. Claim `TODO-THESIS-CH6-CSEM-ADMISSION-UNCERTAINTY-DRAFT`.
   This chapter is the control layer for all later claims.
2. Claim `TODO-THESIS-CH5-CSEM-FLUID-WALLS-DRAFT`.
   This gives the model equations and segment architecture.
3. Claim `TODO-THESIS-CH3-CSEM-CFD-EVIDENCE-DRAFT`.
   This imports the Salt-family CFD result layer with its caveats.
4. Claim `TODO-THESIS-CH7-CSEM-RESULTS-INTEGRATION-DRAFT`.
   This should only use already-ready results and should state blockers.
5. Claim `TODO-THESIS-CH1-CSEM-MOTIVATION-DRAFT` and
   `TODO-THESIS-CH8-CSEM-SAM-LIMITATIONS-DRAFT` after the middle chapters have
   stable wording.
6. Claim `TODO-THESIS-CSEM-FIGURE-TABLE-ASSEMBLY` in parallel with writing if
   no figure-generation row owns the same files.
7. Leave the trigger-gated rows alone until their evidence packages land.

## Output Contract

Every row should emit:

- one chapter-ready current-section markdown file with frontmatter;
- `.agent/status/<date>_<TASK>.md`;
- `.agent/journal/<date>/<slug>.md`;
- `imports/<date>_<slug>.json`;
- optional additive update to `reports/thesis_dossier/Chapters_and_sections/current/README.md`;
- validation with `python3 tools/docs/build_repo_index.py` and
  `python3.11 tools/agent/finish_task.py --task-id <TASK>`.

Chapter files should include:

- source paths for every claim;
- claim IDs from `08_thesis_claim_ledger.md` where available;
- figure/table placements;
- ready/diagnostic/blocked status for each result;
- an explicit runtime-input statement for predictive claims.

## Do-Not-Do Guardrails

- Do not mutate native CFD/OpenFOAM outputs.
- Do not mutate registry/admission state.
- Do not launch solver, postprocessing, or scheduler jobs from writing rows.
- Do not edit Fluid or external paper/thesis trees unless a board row explicitly
  claims those paths.
- Do not fit, tune, select, or admit a model from prose.
- Do not promote diagnostic CFD evidence to predictive closure.
- Do not use CFD `mdot`, realized CFD `wallHeatFlux`, imposed CFD cooler duty,
  realized test-section heat, validation temperatures, or scored-row
  pressure/heat targets as predictive runtime inputs.
- Do not use holdout or external rows for fitting, tuning, or model selection.
- Do not claim SAM validation or Salt-versus-Water synthesis from current
  evidence.

## Current Blocked Claims

These remain blocked until later model work lands:

- final frozen predictive performance;
- admitted passive wall/test-section closure;
- ordinary component `K` for current corner rows;
- F6 friction recorrection;
- ordinary upcomer single-stream `Nu`, `f_D`, or `K`;
- SAM validation;
- Salt-versus-Water synthesis.
