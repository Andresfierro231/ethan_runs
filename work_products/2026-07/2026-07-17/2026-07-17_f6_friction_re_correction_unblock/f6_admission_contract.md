---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_f6_internal_nu_admission_review_and_forward_unblock/f6_onset_scorecard.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/hybrid_1d_model_contract.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/required_output_contract.csv
tags: [f6, friction, recirculation, admission, blocker]
related:
  - work_products/2026-07/2026-07-16/2026-07-16_recirc_feature_admission_and_hybrid_contract/recirculation_feature_admission_table.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/proposed_cfd_run_matrix.csv
task: AGENT-487
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: decision_contract
status: complete
---
# F6 Admission Contract

## Ordinary F6 Lane

Admit only rows with low reverse flow (`RAF < 0.01` and `RMF < 0.01`), valid
same-window pressure loss, documented Re/Ri/property extraction, and split-safe
validation/holdout improvement over `F3_shah_apparent`.

## Recirculation-Modeled Lane

Rows with material reverse flow may support a named `section_effective_loss`,
`mixing_penalty`, or `onset/transition_diagnostic` lane. They may not be
reported as ordinary `Nu`, `f_D`, or component `K`.

Admission requires same-window RAF/RMF/SVF, wall-core or wall-bulk Delta T, Gz,
pressure residual movement, mesh/time uncertainty, and validation/holdout
improvement over `F3_shah_apparent` without a hidden global multiplier.

## Current Decision

Current PM5 evidence does not clear either lane. Keep `F3_shah_apparent` as the
production closure and keep `f6-friction-re-correction` open with the narrowed
queue in `next_extraction_queue.csv`.
