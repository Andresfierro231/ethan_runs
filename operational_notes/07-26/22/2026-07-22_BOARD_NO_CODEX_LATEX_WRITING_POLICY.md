---
provenance:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md
  - reports/thesis_dossier/README.md
  - operational_notes/07-26/22/2026-07-22_THESIS_TOMORROW_CONTEXT_PROGRESS_HANDOFF.md
tags: [board-policy, thesis, external-writer, evidence-packet, no-latex-writing]
related:
  - .agent/status/2026-07-22_TODO-BOARD-NO-CODEX-LATEX-WRITING-POLICY-2026-07-22.md
  - .agent/journal/2026-07-22/board-no-codex-latex-writing-policy.md
  - imports/2026-07-22_board_no_codex_latex_writing_policy.json
task: TODO-BOARD-NO-CODEX-LATEX-WRITING-POLICY-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Cleaner
type: operational_note
status: complete
---
# Board Policy: No Codex LaTeX Writing

## Why This Exists

The thesis workflow is now split intentionally:

- Codex in `ethan_runs` prepares source-backed evidence packets, analyses,
  assumptions, caveats, caption/source ledgers, copy/no-copy manifests, and
  writer instructions.
- The outside thesis writer owns full prose development and LaTeX chapter
  composition.

This keeps the heavy CFD workspace focused on evidence and provenance while
making the outside writer effective without raw CFD trees or chat history.

## Open First

1. `.agent/BOARD.md`
   - Confirm no open row is scoped as direct LaTeX prose writing.
   - Historical completed `TODO-THESIS-LATEX-*` rows remain provenance only.

2. `work_products/2026-07/2026-07-22/2026-07-22_thesis_external_writer_evidence_packet_contract/README.md`
   - Use this contract for evidence-packet schema and required fields.

3. `reports/thesis_dossier/README.md`
   - Use this as the thesis context front door.

4. `operational_notes/07-26/22/2026-07-22_THESIS_TOMORROW_CONTEXT_PROGRESS_HANDOFF.md`
   - Use current progress and blocker context, but follow this policy for the
     division between Codex evidence work and outside prose writing.

## Current Board Correction

The previously open row
`TODO-THESIS-LATEX-COMPACT-EVIDENCE-APPENDIX-PLAN-2026-07-22` was renamed and
reframed as
`TODO-THESIS-COMPACT-EVIDENCE-APPENDIX-PACKET-PLAN-2026-07-22`.

That row now produces:

- compact evidence/support packet plan;
- copy/no-copy manifest;
- evidence-directory/import instructions;
- appendix/table target suggestions;
- exact source paths;
- explicit exclusion of native CFD trees, raw sampled fields, and broad
  generated-output folders.

It does not write thesis prose, edit LaTeX, or mutate the external papers repo.

## Allowed Codex Outputs

Codex-owned thesis-support rows may produce:

- evidence packets under `work_products/**`;
- equation, definition, source-path, and assumption ledgers;
- caveat and forbidden-claim ledgers;
- figure/table target manifests and caption banks;
- import/copy manifests for small artifacts;
- validation reports and task closeout documentation;
- operational notes that tell an outside writer what evidence is trusted and
  what claims are forbidden.

## Forbidden Codex Scope On This Board

Do not create or claim an `ethan_runs` board row whose objective is:

- actual LaTeX prose writing;
- full thesis chapter composition;
- direct mutation of `../papers/**` manuscript files;
- broad prose polish of chapter bodies;
- replacing outside-writer judgment with generated chapter text.

If a future workflow needs selected artifacts in a manuscript repository, this
board should produce exact artifact-transfer instructions. The external
writer/papers workflow should own any prose composition.

## Historical Rows

Completed LaTeX sync rows in `.agent/BOARD.md` are not deleted. They are useful
provenance for what already happened. They should not be interpreted as current
authorization for new Codex manuscript writing.

## Next Task Sequence

1. Claim `TODO-THESIS-GOVERNING-EQUATIONS-DEFINITIONS-GLOSSARY-PACKET-2026-07-22`.
2. Claim `TODO-THESIS-COMPACT-EVIDENCE-APPENDIX-PACKET-PLAN-2026-07-22`.
3. Claim `TODO-THESIS-EVIDENCE-PACKET-CH7-CH8-RESULTS-NEGATIVE-BLOCKED-2026-07-22`.
4. Then produce recirculation, thermal accounting, and pressure-basis evidence
   packets as separate rows.

## Do Not Do

- Do not mutate native CFD/OpenFOAM outputs.
- Do not edit registry/admission state.
- Do not launch scheduler, solver, sampler, harvest, or UQ work from this
  policy row.
- Do not edit Fluid or external repos.
- Do not release source/property or coefficient admission.
- Do not relax runtime-leakage rules.
- Do not refresh generated docs indexes from this policy row.
