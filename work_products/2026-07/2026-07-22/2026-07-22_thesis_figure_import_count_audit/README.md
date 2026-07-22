---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_final_figure_import_ledger/figure_candidate_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_final_figure_import_ledger/selected_figure_import_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_final_figure_import_ledger/caption_source_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_final_figure_import_ledger/final_import_manifest.csv
tags: [thesis, figures, evidence-packet, no-copy, provenance]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGURE-IMPORT-COUNT-AUDIT-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-figure-import-count-audit.md
task: TODO-THESIS-FIGURE-IMPORT-COUNT-AUDIT-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Figure Import Count Audit

Decision: `authoritative_figure_count_12_legacy_selected_count_9_resolved_no_copy_with_verified_path_corrections`.

The 12-row `figure_candidate_ledger.csv` in the final figure import ledger is the authoritative current manifest for thesis-ready figure candidates. The 9-row `selected_figure_import_ledger.csv` is a visible selected subset with legacy figure IDs and two upcomer composites that are not in the authoritative final manifest. The mismatch is therefore a ledger-generation/history issue, not evidence that current figure files are missing.

Filesystem verification found all 12 current assets. Five ledger source strings were stale: the files exist under package subdirectories such as `figures/progress/svg` and `figures/tp_tw_vs_elevation/svg`. Use `verified_source_path`, not `ledger_source_path`, for any later thesis transfer row.

Outputs:
- `audited_selected_asset_table.csv`: 12 authoritative current figure rows with verified path, caption-safe claim, and forbidden claim.
- `legacy_selected_count_reconciliation.csv`: maps seven legacy selected IDs to current IDs, flags two legacy-only upcomer composites, and flags five current-only rows absent from the older selected ledger.
- `caption_boundary_table.csv`: safe claim, forbidden claim, caveat, and range/basis note for each current figure.
- `source_path_existence_table.csv`: ledger path, verified path, path-resolution status, and byte-size check for each current figure.
- `thesis_repo_transfer_todo.csv`: transfer queue requiring a separate exact thesis-repo row before copy.
- `copy_no_copy_manifest.csv`: row-level no-copy decision.
- `summary.json`: compact counts and guardrail flags.

Guardrails preserved: no thesis body edit, no binary asset copy, no broad figure tree copy, no solver output mutation, no registry mutation, no scheduler action, and no science/admission change.
