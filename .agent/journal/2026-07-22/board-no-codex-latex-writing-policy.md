---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/22/2026-07-22_BOARD_NO_CODEX_LATEX_WRITING_POLICY.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
tags: [journal, board-policy, thesis, external-writer, evidence-packet]
related:
  - .agent/status/2026-07-22_TODO-BOARD-NO-CODEX-LATEX-WRITING-POLICY-2026-07-22.md
  - imports/2026-07-22_board_no_codex_latex_writing_policy.json
task: TODO-BOARD-NO-CODEX-LATEX-WRITING-POLICY-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Cleaner
type: journal
status: complete
---
# Board No-Codex-LaTeX-Writing Policy

Task: `TODO-BOARD-NO-CODEX-LATEX-WRITING-POLICY-2026-07-22`

## Attempted

Converted the user's direction into durable board policy: no new Codex-owned
`ethan_runs` task should be actual LaTeX writing. Codex should instead produce
evidence artifacts and instructions that allow an outside writer to write well.

## Observed

The board contained historical completed LaTeX sync rows and one open row whose
ID still began `TODO-THESIS-LATEX-*`. The open row was not primarily prose
composition, but its name and wording could lead a future agent to treat it as a
manuscript-writing lane.

The external-writer evidence-packet contract already had the right general
philosophy, but one section still referred to rows that directly write LaTeX.
The July 22 thesis handoff also still recommended direct LaTeX sync rows as the
best next work.

## Inferred

The safest correction is to preserve historical completed rows as provenance
while changing the live/open work queue and the front-door docs. Deleting or
rewriting completed history would make provenance worse and is unnecessary for
future task routing.

## Contradictions Or Caveats

Older completed rows still contain direct LaTeX-writing descriptions because
they describe work that already happened. They should be read as historical
records only. The current live policy and open board rows govern future work.

## Next Useful Actions

- Claim the governing-equations/definitions glossary packet.
- Claim the compact evidence appendix packet plan.
- Claim the Chapter 7/8 negative-results evidence packet.
- Keep direct prose and LaTeX chapter composition in the outside-writer lane.

## Guardrails

This was documentation and board coordination only. No native output, scheduler,
registry/admission, Fluid, external repo, LaTeX/manuscript, validation/holdout,
fitting/model-selection, source/property release, coefficient admission,
blocker-register, generated-index, or runtime-leakage state was changed.
