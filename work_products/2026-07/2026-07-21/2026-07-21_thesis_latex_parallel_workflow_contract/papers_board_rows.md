---
provenance:
  - ../papers/.agent/BOARD.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/latex_sync_contract.csv
tags: [papers-board, csem-thesis, latex-sync, claimable-rows]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_latex_parallel_workflow_contract/README.md
task: TODO-THESIS-LATEX-PARALLEL-WORKFLOW-CONTRACT-2026-07-21
date: 2026-07-21
role: Coordinator
type: board-packet
status: proposed
supersedes: []
superseded_by:
---
# Papers Board Rows To Add

The papers workspace requires rows in `../papers/.agent/BOARD.md` before actual
LaTeX edits. Add these as `Backlog` rows first. A Coordinator should promote
one row to `Active` with a real owner before an agent edits any target path.

## Backlog Rows

| Task ID | Requested role | Goal | Likely paths | Notes |
| --- | --- | --- | --- | --- |
| csem-latex-ch1-motivation-sync-2026-07-21 | Writer / Reviewer | Sync ready motivation and contribution prose into Chapter 1, keeping CFD as high-fidelity reference rather than experimental validation. | `UTexas_Research/csem-Masters_dissertation/intro_adjacent/introduction.tex`; `UTexas_Research/csem-Masters_dissertation/intro_adjacent/motivation.tex`; `.agent/status/csem-latex-ch1-motivation-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch1-motivation-sync-2026-07-21.md` | Open first: `ethan_runs/reports/thesis_dossier/Chapters_and_sections/current/15_ch1_csem_motivation_and_contribution.md`; validate with `scripts/check_guardrails.sh` and `scripts/build_thesis.sh`. |
| csem-latex-ch3-evidence-refresh-2026-07-21 | Writer / Reviewer | Refresh Chapter 3 CFD evidence database with provenance, Salt-family roles, figure/table calls, and legal-use limits. | `UTexas_Research/csem-Masters_dissertation/chapters/03_physical_system_and_evidence.tex`; figure/table paths only if explicitly copied under a promoted row; `.agent/status/csem-latex-ch3-evidence-refresh-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch3-evidence-refresh-2026-07-21.md` | Open first: `16_ch3_csem_cfd_evidence_database.md`, `21_csem_figure_table_incorporation_package.md`, 3D analysis figures README, and closed upcomer visual packages. |
| csem-latex-ch4-reduction-split-sync-2026-07-21 | Writer / Reviewer | Make CFD-to-1D reduction, split discipline, evidence classes, and runtime-leakage prevention explicit. | `UTexas_Research/csem-Masters_dissertation/chapters/04_cfd_to_1d_reduction.tex`; `.agent/status/csem-latex-ch4-reduction-split-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch4-reduction-split-sync-2026-07-21.md` | No new science required; enforce forbidden runtime inputs in predictive prose. |
| csem-latex-ch5-model-form-sync-2026-07-21 | Writer / Reviewer | Insert ready fluid+walls model-form architecture, equations, segment state, wall stack, external BCs, source/sink role, and recirculation flag text. | `UTexas_Research/csem-Masters_dissertation/chapters/05_coupled_fluid_walls_model.tex`; `.agent/status/csem-latex-ch5-model-form-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch5-model-form-sync-2026-07-21.md` | Open first: `02_model_form_fluid_walls.md`, `17_ch5_csem_fluid_walls_model.md`, and `09_fluid_walls_segment_atlas.md`. |
| csem-latex-ch6-admission-uncertainty-sync-2026-07-21 | Writer / Reviewer | Strengthen closure/admission and uncertainty chapter with no-silent-promotion gate, source/property labels, split roles, and blocker taxonomy. | `UTexas_Research/csem-Masters_dissertation/chapters/06_closure_admission_uncertainty.tex`; `.agent/status/csem-latex-ch6-admission-uncertainty-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch6-admission-uncertainty-sync-2026-07-21.md` | Do not change any admitted state unless a closed evidence package supports it. |
| csem-latex-ch7-ch8-results-sync-2026-07-21 | Writer / Reviewer | Write results as reduced CFD evidence, diagnostic results, negative results, and blocked final-scorecard logic. | `UTexas_Research/csem-Masters_dissertation/chapters/07_reduced_cfd_evidence.tex`; `UTexas_Research/csem-Masters_dissertation/chapters/08_predictive_model_assessment.tex`; `.agent/status/csem-latex-ch7-ch8-results-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch7-ch8-results-sync-2026-07-21.md` | Wait for current thermal/upcomer/pressure packages before any final predictive scorecard wording. Negative results may be written now. |
| csem-latex-ch9-limits-sam-sync-2026-07-21 | Writer / Reviewer | Sync limitations, SAM/CSEM relevance, future work, and conclusion language. | `UTexas_Research/csem-Masters_dissertation/chapters/09_implications_conclusions_future_work.tex`; `.agent/status/csem-latex-ch9-limits-sam-sync-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-ch9-limits-sam-sync-2026-07-21.md` | Frame contribution as vetted workflow and branchwise evidence map, not SAM validation. |
| csem-latex-artifact-import-2026-07-21 | Integrator / Reviewer | Import completed thesis-facing figures/tables from `ethan_runs` packages into the dissertation with captions and labels. | Exact figure/table destination paths must be named when promoted; exact `.tex` consumers must be named when promoted; `.agent/status/csem-latex-artifact-import-2026-07-21.md`; `.agent/journal/2026-07-21/csem-latex-artifact-import-2026-07-21.md` | Only import artifacts whose README satisfies `artifact_handoff_schema.json`. |
| csem-latex-integration-review-build-2026-07-21 | Reviewer | After chapter sync rows, run guardrail/build review and report residual evidence scaffolds or forbidden runtime-leakage phrases. | `UTexas_Research/csem-Masters_dissertation/**` read-only except `.agent/status/csem-latex-integration-review-build-2026-07-21.md` and `.agent/journal/2026-07-21/csem-latex-integration-review-build-2026-07-21.md` | Validation: `scripts/check_guardrails.sh`; `scripts/build_thesis.sh`. |
