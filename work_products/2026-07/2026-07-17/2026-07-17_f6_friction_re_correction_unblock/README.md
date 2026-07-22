---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_f6_upcomer_blocker_status_scorecard/f6_status_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/proposed_cfd_run_matrix.csv
tags: [f6, friction, recirculation, blocker]
related:
  - .agent/status/2026-07-17_AGENT-487.md
  - .agent/journal/2026-07-17/f6-friction-re-correction-unblock.md
task: AGENT-487
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# F6 Friction/Re-Correction Unblock

Generated: `2026-07-17T13:05:48+00:00`

## Decision

- `f6-friction-re-correction`: `keep_open_narrowed`.
- Production closure remains `F3_shah_apparent`.
- No current row admits ordinary single-stream F6.
- No current row admits a predictive recirculation-modeled F6/onset closure.

## Results

- Candidate rows reviewed: `12`.
- Ordinary F6 candidate rows: `0`.
- Ordinary F6 scoreable rows: `0`.
- Recirculation/hybrid diagnostic rows: `12`.
- Recirculation/hybrid scoreable rows: `0`.
- Next extraction rows: `5`.

## Outputs

- `f6_candidate_inventory.csv`
- `f6_admission_contract.md`
- `f6_vs_f3_scorecard.csv`
- `f6_blocker_decision.md`
- `next_extraction_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external
Fluid files, or generated index files were mutated. Generated indexes remain
pending because `AGENT-482` owns the generated index paths.
