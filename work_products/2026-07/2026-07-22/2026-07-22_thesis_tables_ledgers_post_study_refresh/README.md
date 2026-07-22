---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_paper_outline_evidence_transfer_gap_request/completed_studies_to_import.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_compact_numerical_claims_ledger/compact_numerical_claims_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_s13_mesh_gci_upcomer_exchange_evidence_packet/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_source_property_release_unblock_study/summary.json
tags: [thesis, tables, ledgers, post-study-refresh, no-latex]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_paper_outline_evidence_transfer_gap_request/README.md
  - .agent/status/2026-07-22_TODO-THESIS-TABLES-LEDGERS-POST-STUDY-REFRESH-2026-07-22.md
task: TODO-THESIS-TABLES-LEDGERS-POST-STUDY-REFRESH-2026-07-22
date: 2026-07-22
role: Writer / Reviewer / Tester / Coordinator
type: work_product
status: complete
---
# Thesis Tables/Ledgers Post-Study Refresh

This packet updates the thesis-facing table and ledger routing after recent
study closeouts. It does not edit LaTeX, compact ledgers, source indexes, native
CFD outputs, registry/admission state, or external repositories.

## Start Here

1. `updated_transfer_manifest.csv` is the current compact-evidence transfer
   order.
2. `updated_completed_studies_to_import_ledger.csv` lists the completed packets
   that should update thesis evidence tables.
3. `stale_status_corrections.csv` names the older queue statuses that are now
   stale.
4. `proposed_compact_ledger_delta.csv` and `source_index_update_plan.csv` are
   proposals for a later exact-ledger edit row; this task did not mutate the
   compact numerical claims ledger.

## Main Findings

- Three newly completed packets need to be reflected in thesis-facing tables:
  S13 mesh/GCI upcomer evidence, pressure F6 ordinary-basis failure evidence,
  and source/property release unblock evidence.
- The compact numerical claims ledger already covers related older pressure,
  S13, and source/property evidence, but it does not directly cite these three
  newer packet summaries as the controlling sources.
- The next ledger edit should add a small delta rather than rewrite existing
  claims: keep old claim IDs as provenance, add new rows/source-index entries
  for the new packet-level counts, and keep admission/freeze/final-score values
  at zero.
- Figure/sensor/thermal import rows remain dependent on their separate active
  or open packets. They should not be force-updated here.

## Guardrails

Do not use this packet to claim closure admission, final score, source/property
release, Qwall release, pressure component-K/F6 admission, ordinary upcomer
closure, or thermal repair. It is a routing and ledger-refresh packet only.
