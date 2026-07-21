---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/20/2026-07-20_THESIS_RECIRCULATION_IMAGE_CANDIDATES.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s9_upcomer_onset_anchor_exchange_uq/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s9_upcomer_exchange_evidence/caption_bank.md
  - reports/thesis_dossier/Chapters_and_sections/current/04_upcomer_recirculation_modeling.md
  - reports/thesis_dossier/Chapters_and_sections/current/12_thesis_figures_and_diagrams_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
tags: [journal, thesis-dossier, upcomer, recirculation, figures]
related:
  - .agent/status/2026-07-21_TODO-THESIS-UPCOMER-RECIRCULATION-VISUAL-EVIDENCE-INSERTION-2026-07-21.md
  - imports/2026-07-21_thesis_upcomer_recirculation_visual_evidence_insertion.json
task: TODO-THESIS-UPCOMER-RECIRCULATION-VISUAL-EVIDENCE-INSERTION-2026-07-21
date: 2026-07-21
role: Writer/Reviewer/Figures
type: journal
status: complete
supersedes: []
superseded_by:
---
# Thesis Upcomer Recirculation Visual Evidence Insertion

## Attempted

Claimed a narrow thesis writing/figure task and inserted F-03A into the current
thesis figure planning layer. The insertion uses existing artifacts only:
Salt4 Jin upcomer velocity-arrow SVG, Salt2 validation/external upcomer
velocity-arrow SVG, and Salt2 Jin nominal velocity-profile SVG as a fallback.

## Observed

The existing thesis already had F-03, a conceptual hybrid upcomer schematic, and
Chapter 4 already carried reverse-flow metrics. The missing piece was a real
CFD visual placement that writers could use to discuss why ordinary
single-stream upcomer closure is not valid in the recirculating rows.

Salt4 Jin has direct upcomer velocity-arrow SVG/PDF/PNG outputs. The Salt2
velocity-arrow render available under `figures/figures_rendered` is the
`val_salt2` validation/external case, while nominal Salt2 Jin has a registry
velocity-profile SVG rather than the same arrow-render artifact.

## Inferred

The Salt2/Salt4 visuals can safely enrich the thesis as diagnostic evidence for
model-form selection. They support a statement that ordinary single-stream and
2D-axisymmetric upcomer closure are not adequate working bases in this
recirculating regime, provided the caption clearly states the evidence is not
closure admission.

## Caveats

- The external Salt2 arrow render must not be described as Salt2 Jin nominal
  training evidence.
- The nominal Salt2 Jin fallback is a velocity-profile plot, not the same
  ParaView velocity-arrow artifact.
- The image insertion does not unblock S13 exchange QOIs, same-window UQ, or
  any S11/S6 final scorecard.

## Next Useful Actions

1. If the external thesis build requires local figure assets, claim a figure
   production row to copy/export F-03A into the dissertation figure tree.
2. Insert the F-03A caption into the external manuscript after the reverse-flow
   metrics and before the model-form interpretation.
3. Continue S13 for production exchange QOIs and same-window UQ before any
   exchange-cell coefficient language changes.

## Validation

Commands run:

```text
python3.11 -c "<path and CSV validation>"
rg -n "F-03A|2D-axisymmetric|val_salt2|Salt2 Jin" ...
git diff --check -- <task paths>
python3.11 tools/docs/build_repo_index.py
python3.11 tools/docs/build_repo_index.py --check
```

Results:

- Five cited SVG/PDF visual paths exist.
- `figure_claim_crosswalk.csv` parses and contains F-03A.
- `source_manifest.csv` parses and contains the Salt4 F-03A source path.
- F-03A and split-role caveats are discoverable from the current thesis docs
  and the operational note.
- `git diff --check` reported no whitespace errors.
- Documentation index regenerated successfully and blocker register check
  passed.
