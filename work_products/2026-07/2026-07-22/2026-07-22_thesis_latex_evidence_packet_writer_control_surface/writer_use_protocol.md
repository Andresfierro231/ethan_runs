---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_outline_evidence_completeness_matrix/chapter_evidence_completeness_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_compact_numerical_claims_ledger/compact_numerical_claims_ledger.csv
tags: [thesis, writer-protocol, evidence-ledger]
related:
  - new_board_study_queue.csv
  - past_studies_reusable_for_thesis.csv
  - latex_repo_transfer_queue.csv
task: TODO-THESIS-MATRIX-LEDGER-STUDY-DISPATCH-2026-07-22
date: 2026-07-22
role: Coordinator/Writer/Reviewer/Tester
type: handoff
status: complete
---
# Writer Use Protocol

Use the matrix first, then the numerical ledger.

For each thesis section:

1. Open `chapter_evidence_completeness_matrix.csv`.
2. Check `readiness_status`, `ready_evidence_packets`,
   `missing_evidence_or_studies`, `next_board_tasks`, and `writer_action`.
3. If the section is `ready_now`, write from the cited packets. If it is
   `partly_ready`, write only the supported part and preserve the blocker. If
   it is blocked, write the methodology or limitation but not the missing
   result.
4. For every numerical sentence, find the relevant row in
   `compact_numerical_claims_ledger.csv`.
5. Copy the exact value, unit, source path, split role, admission label, allowed
   claim, and forbidden overclaim into the writer's notes.
6. If a number is not in the compact ledger, do not use it in thesis prose until
   a small evidence packet or ledger update adds it.

The crosswalk files are not optional:

- `chapter_number_targets.csv`: quickly identifies which claim IDs are relevant
  to each chapter.
- `forbidden_overclaim_matrix.csv`: prevents diagnostic evidence from becoming
  validation, admission, source/property release, Qwall release, final-score,
  or runtime-input claims.
- `uncertainty_admission_labels.csv`: defines the exact label language the
  writer should use.
- `source_number_index.csv`: lets the writer trace every number back to a
  source packet without opening heavy output trees.

The thesis repo should receive compact evidence packets, CSV excerpts,
caption/source ledgers, and selected figures only. Do not move huge native CFD
outputs, raw generated trees, solver directories, or broad figure directories
into the LaTeX repo.
