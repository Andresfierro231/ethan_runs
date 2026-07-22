---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_fit_candidate_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/upcomer_onset_evidence_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_onset_blocker_resolution/next_evidence_requirements.csv
tags: [f6, friction, upcomer, onset, blocker]
related:
  - .agent/blockers.yml
task: AGENT-464
date: 2026-07-16
role: Hydraulics/Upcomer-onset/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 / Upcomer Blocker Status Scorecard

Generated: `2026-07-16T21:54:12+00:00`

## Decisions

- `f6-friction-re-correction`: `keep_open`.
- `upcomer-onset-data-sparsity`: `keep_open`.

## Results

- F6/PM5 rows reviewed: `12`.
- F6 fit-admissible rows: `0`.
- Upcomer onset evidence points reviewed: `3`.
- Upcomer single-stream fit rows admitted: `0`.
- Queue rows: `5`.

## Interpretation

Current PM5 rows are useful pressure/onset diagnostics, but all remain material
recirculation rows and cannot promote F6 as a single-stream friction correction.
Production should remain `F3_shah_apparent` until F6 shows validation/holdout
improvement without a hidden global multiplier.

Current upcomer evidence observes recirculation, but it does not bracket onset
or provide a non-recirculating anchor. Keep it in a hybrid/onset diagnostic
lane, not a conventional Nu/f_D/K fit lane.

## Outputs

- `f6_status_scorecard.csv`
- `upcomer_onset_classification.csv`
- `next_evidence_queue.csv`
- `blocker_decisions.csv`
- `source_manifest.csv`
- `summary.json`
