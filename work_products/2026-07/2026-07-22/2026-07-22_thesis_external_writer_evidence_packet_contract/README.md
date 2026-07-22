---
provenance:
  - .agent/BOARD.md
  - operational_notes/07-26/22/2026-07-22_THESIS_TOMORROW_CONTEXT_PROGRESS_HANDOFF.md
  - operational_notes/07-26/22/2026-07-22_BOARD_CLEANUP_AND_AVENUE_GAP_DISPATCH.md
  - reports/thesis_dossier/README.md
  - reports/thesis_dossier/Chapters_and_sections/current/14_csem_narrative_integration_plan.md
  - reports/thesis_dossier/Chapters_and_sections/current/21_csem_figure_table_incorporation_package.md
  - reports/thesis_dossier/Chapters_and_sections/current/26_predictive_model_studies_roadmap.md
  - ../papers/UTexas_Research/csem-Masters_dissertation
tags: [thesis, external-writer, evidence-packet, board-dispatch, csem]
related:
  - evidence_packet_schema.csv
  - chapter_evidence_packet_queue.csv
  - scientific_study_dispatch_matrix.csv
  - latex_repo_compact_evidence_manifest.csv
task: TODO-THESIS-EXTERNAL-WRITER-EVIDENCE-PACKET-CONTRACT-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer
type: work-product
status: current
---
# Thesis External Writer Evidence Packet Contract

## Guiding Philosophy

The thesis coordination task in `ethan_runs` is now to make external writing
easy to do accurately, not to perform the thesis prose-writing step here.
External prose writers should not need raw CFD trees, huge generated figure
folders, or chat history. They need compact evidence packets that contain the
exact numbers, source paths, equations, definitions, assumptions, caveats,
allowed claims, forbidden claims, and figure/table targets needed to write and
defend each section.

Do not delete existing prose. Existing thesis-dossier prose and implemented
LaTeX chapters remain useful. This contract adds the evidence layer that lets a
new writer scrutinize every claim before improving prose.

## Non-negotiable Claim Rules

- CFD is the current high-fidelity reference, not experimental validation.
- Diagnostic CFD evidence may support model-form selection, residual ownership,
  negative results, and limitations.
- Diagnostic CFD evidence must not be promoted to admitted predictive closure.
- Predictive runtime claims must not use CFD `mdot`, realized CFD
  `wallHeatFlux`, imposed CFD cooler duty, validation temperatures, holdout
  rows, or external-test rows as hidden inputs.
- A governing equation may include a model slot before the coefficient or term
  is admitted. Slot presence is not admission.
- Negative and blocked results are thesis results when they identify exact
  missing evidence, invalid assumptions, or forbidden reduction paths.

## What The LaTeX Repo Is Missing

The current CSEM LaTeX dissertation has chapter files and a small figure tree,
and Chapters 5 and 6 have now been implemented. It does not yet have a compact
`evidence/` layer that an external writer can open to see:

- exact source paths for every thesis-facing number and figure;
- case-role and split-role ledgers in one place;
- governing equations, definitions, units, sign conventions, and assumptions;
- allowed/forbidden claims per chapter;
- runtime-leakage audits for each evidence family;
- admission state for pressure, thermal, recirculation, source/property, and
  final-score claims;
- compact figure/table manifests identifying which small files should be copied
  to the LaTeX repo and which heavy/raw files must remain in `ethan_runs`.

This absence is the main workflow risk for external ChatGPT-style prose work.

## How To Start

1. Build the Chapter 4 evidence packet first.
   - It should support `csem-latex-ch4-reduction-split-sync`.
   - It must include reduction equations, evidence classes, split roles,
     runtime-legal inputs, source/property labels, and diagnostic/non-admission
     rules.

2. Build the governing-equations and definitions packet.
   - This prevents external prose from changing meanings of terms such as
     `Q_wall_W`, source-side heat flow, section-effective pressure residual,
     recirculation proxy, `Nu`, `f_D`, `K`, train/support/holdout/external, and
     admitted/diagnostic/blocked.

3. Build results evidence packets before asking the outside prose writer to
   expand Chapters 7 and 8.
   - Pressure negative result packet.
   - S13 recirculation/Qwall/UQ packet.
   - Thermal accounting and residual-owner packet.
   - Blocked scorecard and no-freeze packet.

4. Only after compact packets exist, propose selected small files for a LaTeX
   repo `evidence/` directory or exact figure destinations through a
   papers-board artifact-transfer row. Codex work in this repo should stop at
   evidence packets, manifests, caveats, captions, and writer instructions.

## What Can Move Into The LaTeX Repo Now

Move small, reviewable support files, not raw data:

- packet READMEs and selected CSV excerpts;
- claim/evidence crosswalks;
- governing-equation and glossary tables;
- figure/table ledgers and caption banks;
- selected upcomer SVG/PDF panels only after exact figure destinations are
  claimed;
- selected 3D paper tables or references to them.

Keep out of the LaTeX repo:

- native OpenFOAM case trees;
- broad generated figure folders;
- unfiltered work-product directories;
- raw sampled fields;
- scheduler logs unless a tiny excerpt is explicitly needed;
- any artifact without split role, admission state, allowed use, forbidden use,
  and runtime-leakage audit.

## Highest-value Studies

The scientific studies most likely to enrich the thesis are listed in
`scientific_study_dispatch_matrix.csv`. The top four are:

- recirculation fraction/onset evidence packet from the Salt upcomer visuals
  and S13 evidence;
- thermal accounting traceability packet;
- pressure-basis ladder and negative-result packet;
- source/property release atlas.

These studies enrich the thesis even when they fail closed, because they make
the blocked final scorecard scientifically interpretable.

## Board Rectification

Board tasks should now require an evidence packet whenever their output will
feed an external LaTeX writer. A good row names:

- exact packet output path;
- source files to open first;
- key numbers, equations, definitions, assumptions, caveats, and provenance to
  include;
- required figures/tables and target sections;
- allowed and forbidden claims;
- validation command;
- closeout status, journal, and import manifest.

Rows on the `ethan_runs` board should not be scoped as actual LaTeX prose
writing or full thesis chapter composition. They may prepare evidence packets,
copy/no-copy manifests, caption banks, assumptions/caveat ledgers, source-path
tables, and instructions that an outside writer can use. Historical completed
LaTeX sync rows remain provenance only; they are not future authorization for
Codex to continue manuscript writing from this board.

## Files In This Package

- `evidence_packet_schema.csv`: required fields for every external-writer
  evidence packet.
- `chapter_evidence_packet_queue.csv`: chapter-by-chapter packet queue.
- `scientific_study_dispatch_matrix.csv`: study queue and figure/table asks.
- `latex_repo_compact_evidence_manifest.csv`: what can be copied or summarized
  into the LaTeX repo without raw-data bloat.
- `recommended_papers_board_rows.md`: suggested external papers-board rows to
  add later under an explicit papers-board coordination task.
