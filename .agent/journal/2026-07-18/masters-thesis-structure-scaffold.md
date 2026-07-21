---
provenance:
  - AGENTS.md
  - .agent/BOARD.md
  - .agent/FILE_OWNERSHIP.md
  - .agent/ROLES.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/mentor_thesis_outline.md
  - reports/thesis_dossier/Outline.md
  - reports/thesis_dossier/Chapters_and_sections/current/README.md
  - reports/thesis_dossier/Chapters_and_sections/dated/2026-07-17_current_context.md
  - .agent/STATE.md
  - .agent/BLOCKERS.md
tags: [thesis-dossier, masters-thesis, latex-scaffold, thesis-structure, writing]
related:
  - .agent/status/2026-07-18_AGENT-542.md
  - imports/2026-07-18_masters_thesis_structure_scaffold.json
  - reports/thesis_dossier/mentor_thesis_outline.md
task: AGENT-542
date: 2026-07-18
role: Writer/Coordinator/Reviewer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Master's Thesis Structure Scaffold

## Attempted

Started the UT CSEM master's thesis manuscript structure in the external repo:
`../papers/UTexas_Research/csem-Masters_dissertation`.

Read the Ethan repo startup files, the papers workspace instructions, both board/ownership/role files, the thesis dossier front door, mentor-facing outline, current section index, latest context note, generated state, and generated blocker register.

## Observed

The dissertation repo was a clean UT report-style template with `masterthesis.tex` delegating manuscript content to `structural/body.tex`. The body included Introduction, Motivation, and a template appendix only.

The current thesis dossier already defines the high-level story: a defensible CFD-to-1D closure workflow for the TAMU molten-salt natural-circulation loop, with Ethan OpenFOAM as high-fidelity reference rather than experimental validation, a steady `fluid+walls` final model target, strict runtime-leakage rules, and current open blockers limited to:

- `predictive-wall-test-section-submodels`
- `upcomer-onset-data-sparsity`
- `f6-friction-re-correction`

## Inferred

The right first manuscript action is a source-aware scaffold rather than importing large prose immediately. Chapter placeholders should preserve source contracts and TODO markers so later writing can pull from the correct dossier sections without accidentally promoting diagnostic or blocked evidence.

## Changed

Updated the external dissertation structure:

- `README.txt`
- `structural/body.tex`
- `chapters/02_background_literature.tex`
- `chapters/03_physical_system_and_evidence.tex`
- `chapters/04_cfd_to_1d_reduction.tex`
- `chapters/05_coupled_fluid_walls_model.tex`
- `chapters/06_closure_admission_uncertainty.tex`
- `chapters/07_results_and_predictive_assessment.tex`
- `chapters/08_systems_code_implications.tex`
- `chapters/09_conclusions.tex`
- `chapters/appendix_claim_ledger.tex`
- `chapters/appendix_segment_atlas.tex`
- `chapters/appendix_validation_split.tex`

Also recorded matching task rows/status/journal records in the Ethan and papers coordination layers.

## Validation

Ran:

```bash
rg -n -e '\\include\\{' -e 'TODO\\[source\\]' -e '\\chapter\\{' -e '\\label\\{' structural/body.tex chapters intro_adjacent README.txt
```

Result: command succeeded and listed the intended body includes, chapter declarations, labels, and TODO source markers.

One earlier `rg` attempt failed because the shell/regex escaping was wrong; the corrected command above was the validation used.

Full LaTeX compilation was not run in this pass.

## Caveats

The scaffold does not claim final predictive results, SAM validation, or closure admission. Existing front matter in `structural/about.tex` and the commented `\input{structural/about}` line in `masterthesis.tex` were left unchanged because this task focused on chapter structure.

## Next Useful Actions

- Convert Chapter 3 split-policy and evidence classes into compact tables from the current dossier.
- Import the steady `fluid+walls` equations and segment metadata into Chapter 5.
- Convert the claim ledger and segment atlas appendices into LaTeX tables.
- Run a full LaTeX compile after deciding whether to enable `structural/about.tex`.
