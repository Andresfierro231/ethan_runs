---
provenance:
  created_by: codex
  created_on: 2026-07-22
tags: [thesis-latex, model-form-figures, scoreboard, start-here]
related:
  - ../papers/UTexas_Research/csem-Masters_dissertation/evidence/model_form_figure_package/README.md
  - .agent/BOARD.md
  - reports/thesis_dossier/README.md
---

# Thesis LaTeX Model-Form Figure Package Transfer

## Why This Exists

The current model-form figures and plotting scripts needed to be placed in the
CSEM thesis LaTeX repo so future thesis writing can use or regenerate them
without searching chat logs or redoing the analysis. The user also asked to
avoid expensive image viewing and to make the future scoreboard dependency
board-visible.

## Open First

1. `../papers/UTexas_Research/csem-Masters_dissertation/evidence/model_form_figure_package/README.md`
2. `../papers/UTexas_Research/csem-Masters_dissertation/evidence/model_form_figure_package/regeneration_contract.md`
3. `../papers/UTexas_Research/csem-Masters_dissertation/evidence/model_form_figure_package/transfer_manifest.csv`
4. `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md`
5. `work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/README.md`

## Copied Package

Target:

`../papers/UTexas_Research/csem-Masters_dissertation/evidence/model_form_figure_package/`

Contents:

- `current_package/`: current copied figure/CSV/caption/source package.
- `scripts/`: copied Ethan builder and test script snapshots.
- `source_snapshots/2026-07-22_thesis_master_model_form_scoreboard/`: current
  master scoreboard snapshot.
- `README.md`, `regeneration_contract.md`, `transfer_manifest.csv`, and
  `transfer_summary.json`.

## Board Rows

Completed/active transfer rows:

- Ethan:
  `TODO-THESIS-LATEX-MODEL-FORM-FIGURE-PACKAGE-TRANSFER-2026-07-22`
- Papers:
  `csem-latex-evidence-model-form-figure-package-2026-07-22`

Future dependency rows:

- Ethan:
  `TODO-THESIS-LATEX-SCOREBOARD-PLOT-REGENERATION-DEPENDENCY-2026-07-22`
- Papers:
  `csem-latex-scoreboard-plot-regeneration-dependency-2026-07-22`

## Future Task Sequence

1. Claim the dependency row when LaTeX figure writing starts.
2. Copy/upload the latest master model-form scoreboard into the CSEM evidence
   package and record the exact source path.
3. Decide whether copied figures are sufficient or regeneration is needed.
4. If regeneration is needed, adapt/check the copied script path assumptions and
   regenerate only the required figures.
5. Update captions/source manifests in the same evidence folder.

## Do-Not-Do Guardrails

- Do not view or render images unless the writing task requires it.
- Do not copy raw CFD/native solver outputs into the LaTeX repo.
- Do not edit thesis body `.tex` files from the Ethan board.
- Do not use protected rows for tuning or model selection.
- Do not claim final predictive accuracy, candidate freeze, source/property
  release, Qwall release, component K, F6, ordinary upcomer Nu, ordinary upcomer
  f_D, or ordinary upcomer K from this figure package.
