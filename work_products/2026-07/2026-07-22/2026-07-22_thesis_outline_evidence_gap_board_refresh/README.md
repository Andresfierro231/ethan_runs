---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - .agent/BLOCKERS.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_cfd_legal_use_matrix/README.md
tags: [thesis, board-dispatch, evidence-gaps, scientific-studies, external-writer]
related:
  - .agent/status/2026-07-22_TODO-THESIS-OUTLINE-EVIDENCE-GAP-BOARD-REFRESH-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-outline-evidence-gap-board-refresh.md
  - imports/2026-07-22_thesis_outline_evidence_gap_board_refresh.json
task: TODO-THESIS-OUTLINE-EVIDENCE-GAP-BOARD-REFRESH-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
---
# Thesis Outline Evidence Gap Board Refresh

This package records the board refresh requested for thesis evidence planning.
It follows the current writing policy: local agents prepare compact evidence,
numbers, provenance, assumptions, caveats, and figure/table targets. They do
not rewrite the thesis prose or copy large CFD trees into the LaTeX repository.

## Board Rows Added

Six nonduplicative Planned/Unclaimed rows were added:

- `TODO-THESIS-OUTLINE-EVIDENCE-COMPLETENESS-MATRIX-2026-07-22`
- `TODO-THESIS-COMPACT-NUMERICAL-CLAIMS-LEDGER-2026-07-22`
- `TODO-THESIS-CH3-CFD-PROVENANCE-QOI-COMPACT-PACKET-2026-07-22`
- `TODO-THESIS-STUDY-THERMAL-TW-AFTER-TP-RESIDUAL-OWNERSHIP-2026-07-22`
- `TODO-THESIS-STUDY-PRESSURE-LOW-RECIRC-ANCHOR-DESIGN-AND-HARVEST-2026-07-22`
- `TODO-THESIS-STUDY-UPCOMER-ONSET-ANCHOR-DESIGN-AND-RECIRC-FRACTION-UQ-2026-07-22`

Existing rows already cover S13 post-sampler GCI/production harvest,
predictive heater/cooler/wall/test-section submodels, final model-form docs,
S11 candidate refresh, and S15 frozen score release. Those were not duplicated.

## What The Outline Still Needs

The outline has enough evidence to write motivation, modeling approach,
runtime-leakage discipline, split/admission policy, negative pressure results,
blocked scorecard logic, limitations, and SAM/CSEM relevance.

The highest-value missing context is:

- a single chapter evidence-completeness matrix;
- a compact numerical claims ledger with exact values, units, source paths,
  split/admission labels, and forbidden overclaims;
- a Ch3 CFD provenance/QOI appendix after the active Salt1-4 postprocessing
  inventory closes;
- a TW-after-TP residual-owner study to prevent wall-temperature residuals from
  being absorbed into internal Nu;
- defensible low-recirculation pressure anchors or an explicit fail-closed
  anchor absence result;
- recirculation-fraction/onset evidence with uncertainty labels and minimal
  follow-on CFD design if current Salt coverage remains too sparse.

## Files

- `outline_context_gap_matrix.csv`
- `board_rows_added.csv`
- `studies_waiting_and_needed.csv`
- `recommended_next_order.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid/external repository, thesis body/LaTeX file, protected score,
source/property release, Qwall release, coefficient admission, candidate
freeze, final score, blocker register, or generated docs index was changed.
