---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - .agent/BOARD.md
  - reports/thesis_dossier/README.md
tags: [status, thesis, external-writer, evidence-packet, board-dispatch]
related:
  - .agent/journal/2026-07-22/thesis-external-writer-evidence-packet-contract.md
  - imports/2026-07-22_thesis_external_writer_evidence_packet_contract.json
task: TODO-THESIS-EXTERNAL-WRITER-EVIDENCE-PACKET-CONTRACT-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer
type: status
status: complete
---
# TODO-THESIS-EXTERNAL-WRITER-EVIDENCE-PACKET-CONTRACT-2026-07-22

## Objective

Establish the new thesis-coordination philosophy: future agents should prepare
compact, source-backed evidence packets for external LaTeX writers instead of
moving huge raw CFD or generated artifact trees into the thesis repo.

## Outcome

Published a compact evidence-packet contract under
`work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/`
and linked it from the thesis dossier README.

The board was rectified so LaTeX-facing rows now require or point to evidence
packets with exact numbers, source paths, equations, definitions, assumptions,
caveats, allowed/forbidden claims, split/admission state, runtime-leakage audit,
and figure/table targets.

## Changes Made

- Added active/complete coordination row to `.agent/BOARD.md`.
- Added an external-writer evidence-packet requirement to the Planned /
  Unclaimed board section.
- Added seven planned rows:
  - `TODO-THESIS-EVIDENCE-PACKET-CH1-CH4-FOUNDATIONS-2026-07-22`
  - `TODO-THESIS-GOVERNING-EQUATIONS-DEFINITIONS-GLOSSARY-PACKET-2026-07-22`
  - `TODO-THESIS-EVIDENCE-PACKET-CH7-CH8-RESULTS-NEGATIVE-BLOCKED-2026-07-22`
  - `TODO-THESIS-LATEX-COMPACT-EVIDENCE-APPENDIX-PLAN-2026-07-22`
  - `TODO-THESIS-STUDY-RECIRCULATION-FRACTION-ONSET-EVIDENCE-PACKET-2026-07-22`
  - `TODO-THESIS-STUDY-THERMAL-ACCOUNTING-TRACEABILITY-EVIDENCE-PACKET-2026-07-22`
  - `TODO-THESIS-STUDY-PRESSURE-BASIS-LADDER-EVIDENCE-PACKET-2026-07-22`
- Tightened existing Chapter 4 and figure/table planned rows so they cite the
  evidence-packet contract.
- Added `reports/thesis_dossier/README.md` pointer to the new package.
- Added package files:
  - `README.md`
  - `evidence_packet_schema.csv`
  - `chapter_evidence_packet_queue.csv`
  - `scientific_study_dispatch_matrix.csv`
  - `latex_repo_compact_evidence_manifest.csv`
  - `recommended_papers_board_rows.md`
- Added this status, journal, and import manifest.

## Validation

- `python3.11 -c "... csv.DictReader ..."` parsed all four CSV files:
  - schema: `19` rows.
  - chapter queue: `5` rows.
  - scientific study dispatch: `7` rows.
  - compact LaTeX manifest: `10` rows.
- `rg -n "evidence packet|External-writer|TODO-THESIS-EVIDENCE-PACKET|TODO-THESIS-STUDY-RECIRCULATION|TODO-THESIS-LATEX-COMPACT" ...` found the README pointer, board rows, and package content.
- `git diff --check -- .agent/BOARD.md reports/thesis_dossier/README.md work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract` passed.

## Key Findings

- The actual CSEM LaTeX repo has chapter files and limited selected figures,
  but it lacks a compact `evidence/` packet layer for external writers.
- Chapters 5 and 6 are already implemented in actual LaTeX and awaiting review.
- The next prose-enabling packet should be Chapter 1/4 foundations, especially
  Chapter 4 reduction and split discipline.
- The highest-value scientific enrichment packets are recirculation/onset,
  thermal accounting traceability, pressure-basis ladder, source/property
  release atlas, and governing-equation glossary.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid
source, external repo files, LaTeX files, thesis chapter bodies,
validation/holdout/external scores, fitting, tuning, model selection,
source/property release, Qwall release, coefficient admission, S11/S12/S13/S15/S6
trigger, blocker-register source, generated index files, deletion, commit, push,
or runtime-leakage rule was changed.
