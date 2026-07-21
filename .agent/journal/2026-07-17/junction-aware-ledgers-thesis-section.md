---
provenance:
  - .agent/BOARD.md
  - reports/thesis_dossier/Chapters_and_sections/current/05_junction_aware_ledgers.md
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_external_score_junction_corner_progress/README.md
tags: [journal, thesis-dossier, junction-aware-ledger, structured-losses]
related:
  - .agent/status/2026-07-17_AGENT-504.md
  - imports/2026-07-17_junction_aware_ledgers_thesis_section.json
task: AGENT-504
date: 2026-07-17
role: Coordinator/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Junction-Aware Ledgers Thesis Section

Added a current thesis/paper section titled “Why Segment-Only 1D Models Miss
Structured Losses.” The section compares:

- segment-only loop ledgers;
- junction-aware ledgers with explicit junction/stub/connector ownership;
- hybrid upcomer ledgers with throughflow and recirculation-cell lanes.

The section uses existing evidence only. It states that Salt2-4 mainline rows
show about `39-48 W` of junction/stub loss, while `val_salt2` has about
`40.926087 W` across four junction/stub buckets. It keeps pressure corner-K
diagnostic because current rows have `0` fit-admitted entries and negative
local K after straight-loss subtraction.

No new model admission was made. The thesis claim is that the final 1D model
needs local role ledgers rather than one global correction factor.
