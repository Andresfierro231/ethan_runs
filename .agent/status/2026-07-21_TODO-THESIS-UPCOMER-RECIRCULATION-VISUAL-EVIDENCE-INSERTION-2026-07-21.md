---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - reports/thesis_dossier/figures/README.md
  - reports/thesis_dossier/figures/figure_claim_crosswalk.csv
  - reports/thesis_dossier/figures/source_manifest.csv
  - operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md
tags: [status, thesis-dossier, upcomer, recirculation, figures]
related:
  - .agent/journal/2026-07-21/thesis-upcomer-recirculation-visual-evidence-insertion.md
  - imports/2026-07-21_thesis_upcomer_recirculation_visual_evidence_insertion.json
task: TODO-THESIS-UPCOMER-RECIRCULATION-VISUAL-EVIDENCE-INSERTION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Figures
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-THESIS-UPCOMER-RECIRCULATION-VISUAL-EVIDENCE-INSERTION-2026-07-21

## Objective

Insert existing Salt2/Salt4 upcomer velocity-arrow and velocity-profile visuals
into the thesis figure plan and upcomer narrative as diagnostic evidence for
recirculation-dominated model-form selection.

## Outcome

Complete. Added F-03A as an existing-CFD visual companion to the F-03 conceptual
upcomer schematic. The current thesis docs now name the Salt4 Jin upcomer arrow
render, the Salt2 validation/external upcomer arrow render, and the Salt2 Jin
nominal velocity-profile fallback with separate provenance and split-role
labels.

The inserted wording says the visuals support disabling ordinary single-stream
and 2D-axisymmetric upcomer closure as the working basis for recirculating
regimes. It explicitly does not admit ordinary upcomer `Nu`, `f_D`, component
`K`, exchange-cell coefficients, final predictive scores, or SAM validation.

## Changes Made

- `.agent/BOARD.md`
- `reports/thesis_dossier/README.md`
- `reports/thesis_dossier/Chapters_and_sections/current/README.md`
- `reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md`
- `reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md`
- `reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md`
- `reports/thesis_dossier/figures/README.md`
- `reports/thesis_dossier/figures/figure_claim_crosswalk.csv`
- `reports/thesis_dossier/figures/source_manifest.csv`
- `operational_notes/07-26/21/2026-07-21_THESIS_UPCOMER_RECIRCULATION_VISUAL_EVIDENCE_INSERTION.md`
- `.agent/journal/2026-07-21/thesis-upcomer-recirculation-visual-evidence-insertion.md`
- `imports/2026-07-21_thesis_upcomer_recirculation_visual_evidence_insertion.json`

## Validation

- `python3.11 -c "<path and CSV validation>"`: passed; checked five cited
  SVG/PDF source paths, confirmed F-03A in `figure_claim_crosswalk.csv`, and
  confirmed Salt4 visual path in `source_manifest.csv`.
- `rg -n "F-03A|2D-axisymmetric|val_salt2|Salt2 Jin" ...`: passed; confirmed
  F-03A placement and split-role caveats in current thesis docs and the
  operational note.
- `git diff --check -- <task paths>`: passed with no output.
- `python3.11 tools/docs/build_repo_index.py`: passed; indexed 2287 docs, 42
  board rows, and 15 blockers.
- `python3.11 tools/docs/build_repo_index.py --check`: passed; blocker register
  OK with 15 entries.

## Guardrails

- Native CFD/OpenFOAM outputs: not modified.
- Rendered figure assets: not modified or regenerated.
- Registry/admission state: not modified.
- Scheduler/solver/postprocessing/sampler/harvest: not run.
- Fluid/external repos: not modified.
- Blocker register source: not modified.
- Runtime leakage: no CFD `mdot`, realized `wallHeatFlux`, imposed cooler duty,
  realized test-section heat, validation temperatures, holdout temperatures, or
  external-test temperatures were promoted to predictive runtime inputs.
