---
task: TODO-THESIS-LITREV-CSEM-INCORPORATION-PACKAGE-2026-07-21
date: 2026-07-21
role: Coordinator / Writer / Reviewer
type: work_product
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/litrev_source_inventory.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/model_form_candidates.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - ../papers/UTexas_Research/csem-Masters_dissertation/README.txt
tags: [litrev-synthesis, csem-thesis, thesis-incorporation, source-envelope, pressure-corner, model-forms]
related:
  - reports/thesis_dossier/Chapters_and_sections/current/25_litrev_csem_thesis_incorporation.md
  - operational_notes/07-26/21/2026-07-21_THESIS_LITREV_CSEM_INCORPORATION_START_HERE.md
---
# LitRev CSEM Thesis Incorporation Package

## Purpose

This package turns the new LitRev extraction into a manuscript-ready bridge for
`../papers/UTexas_Research/csem-Masters_dissertation/`. It is an evidence and
coordination package only. It does not edit the external dissertation tree, fit
closures, admit coefficients, or change CFD/admission state.

## Open First

1. `chapter_incorporation_matrix.csv` - chapter-by-chapter routing for the
   LitRev items.
2. `source_envelope_thesis_table.csv` - compact source-envelope table for the
   literature review chapter.
3. `pressure_corner_thesis_rules.csv` - rules for pressure increases around
   corners and coefficient naming.
4. `model_form_thesis_ladder.csv` - MF-01 to MF-06 placement and status.
5. `latex_insertion_manifest.csv` - exact CSEM chapter insertion manifest.
6. `papers_board_row_proposals.md` - exact rows proposed for the papers board.

## Controlling Interpretation

The LitRev enriches the thesis by adding source envelope, pressure basis,
model-form hierarchy, and admission discipline. It does not admit new TAMU
component `K`, F6, internal `Nu`, recirculation, wall/test-section, transient,
or ROM closures.

The highest-value thesis addition is the pressure-corner rule: a local static
pressure increase around a bend, corner, tee, junction, reducer, or clustered
component can reflect hydrostatic correction, kinetic recovery, source-defined
pressure basis, recovery-plane placement, or section-effective behavior. It
should not be reported as negative dissipation or admitted negative component
`K` without source-matched basis, component isolation, recovery diagnostics,
recirculation gates, and same-QOI uncertainty.

## Phase Handoff

The next work should happen through `../papers/.agent/BOARD.md` because the
actual dissertation files live in the papers workspace. Recommended rows are
listed in `papers_board_row_proposals.md` and aligned to chapter insertions in
`latex_insertion_manifest.csv`.

## Guardrails

- Do not edit `../papers/**` from this Ethan package row.
- Do not use CFD as experimental validation.
- Do not promote diagnostic LitRev or CFD rows into predictive closures.
- Do not hide pressure residuals in global F6/friction multipliers.
- Do not hide heat-loss residuals in internal `Nu` or a global `UA`.
- Do not claim SAM validation.
