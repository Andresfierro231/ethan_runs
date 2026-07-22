---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_latex_evidence_packet_figure_asset_selection/figure_candidate_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_final_figure_import_ledger/final_import_manifest.csv
tags: [thesis, figures, import-ledger, papers-transfer]
related:
  - .agent/status/2026-07-22_TODO-THESIS-EVIDENCE-PACKET-FINAL-FIGURE-IMPORT-LEDGER-2026-07-22.md
task: TODO-THESIS-EVIDENCE-PACKET-FINAL-FIGURE-IMPORT-LEDGER-2026-07-22
date: 2026-07-22
role: Writer/Reviewer
type: handoff
status: complete
---
# Papers Transfer Instructions

This row intentionally does not copy assets into an external papers or thesis
repository. It prepares a path-only ledger for a later exact board row that
owns the destination repo and final manuscript paths.

Next transfer row should:

1. Read `final_import_manifest.csv`.
2. Confirm the exact destination directory in the papers/thesis repo.
3. Copy only rows where `copy_after_papers_transfer_row` is `true`.
4. Preserve source paths in the destination-side manifest.
5. Keep captions inside the safe claim boundaries listed in
   `caption_source_ledger.csv` and `figure_candidate_ledger.csv`.

Do not copy broad figure trees. Do not rewrite generated SVGs unless a separate
figure-polish row claims that exact source and output path. Do not add protected
score or candidate-freeze language to any caption.
