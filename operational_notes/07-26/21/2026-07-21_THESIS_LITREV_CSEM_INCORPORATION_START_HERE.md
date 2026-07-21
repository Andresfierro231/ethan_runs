---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.txt
tags: [start-here, litrev, csem-thesis, board-dispatch, manuscript-handoff]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
task: TODO-THESIS-LITREV-CSEM-INCORPORATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: operational-note
status: current
---
# Start Here: LitRev to CSEM Thesis Incorporation

## Why This Avenue Exists

The LitRev now provides source-audited model-form, pressure-basis,
CFD-postprocessing, heat-loss, and admission-gate material that should enrich
the CSEM master's dissertation. The incorporation must remain conservative:
LitRev evidence controls naming, basis, and admission rules; it does not admit
new TAMU closures.

## Files To Open First

1. `work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/README.md`
2. `work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/chapter_incorporation_matrix.csv`
3. `work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/latex_insertion_manifest.csv`
4. `reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md`
5. `../papers/UTexas_Research/csem-Masters_dissertation/README.txt`

## Trusted Packages

- New LitRev model-form extraction package:
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/`
- Throughflow/recirculation exchange-cell design:
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/`
- Thermal heat-loss contract alignment:
  `work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/`
- CSEM narrative integration plan:
  `reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md`

## Active Or Future Board Rows

Use the Ethan board for evidence packages and `../papers/.agent/BOARD.md` for
external dissertation edits.

Recommended papers-board rows:

| Row | Role | External files |
| --- | --- | --- |
| `csem-litrev-background-source-envelope-2026-07-21` | Writer/Reviewer | `chapters/02_background_literature.tex` |
| `csem-litrev-reduction-pressure-contract-2026-07-21` | Writer/Reviewer | `chapters/04_cfd_to_1d_reduction.tex` |
| `csem-litrev-model-form-admission-2026-07-21` | Writer/Reviewer | `chapters/05_coupled_fluid_walls_model.tex`; `chapters/06_closure_admission_uncertainty.tex` |
| `csem-litrev-results-limits-futurework-2026-07-21` | Writer/Reviewer | `chapters/07_reduced_cfd_evidence.tex`; `chapters/08_predictive_model_assessment.tex`; `chapters/09_implications_conclusions_future_work.tex` |
| `csem-litrev-appendix-ledger-refresh-2026-07-21` | Writer/Reviewer | appendix claim/source tables only if new claims require them |
| `csem-litrev-integration-review-build-2026-07-21` | Reviewer | whole CSEM dissertation tree read-only except review status |

## Output Contract

Each manuscript row must leave:

- papers-board task row with exact file scope;
- papers status and journal entry;
- source-path citations back to the Ethan incorporation package;
- targeted `rg` validation;
- LaTeX build result or explicit reason build was not run.

## Do-Not-Do Guardrails

- Do not use LitRev to admit component `K`, F6, internal `Nu`, recirculation
  thresholds, transient losses, or ROM terms.
- Do not treat CFD as experimental validation.
- Do not relax split or runtime-input guardrails.
- Do not edit native CFD/OpenFOAM outputs, registry/admission state, scheduler
  state, Fluid source, or external model code.
