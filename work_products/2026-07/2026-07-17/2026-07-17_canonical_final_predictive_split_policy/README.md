---
provenance:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-16/2026-07-16_salt1_durable_test_data_and_thesis_story/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/split_admission_decisions.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/README.md
tags: [forward-predictive-model, split-policy, salt-cfd, holdout]
related:
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
  - .agent/status/2026-07-17_AGENT-481.md
task: AGENT-481
date: 2026-07-17
role: Coordinator/Writer
type: work_product
status: complete
---
# Canonical Final Predictive Split Policy

## Decision

The canonical final predictive split is updated: final training/calibration must
span Salt1 through Salt4 nominal rows. Testing and holdout evidence should come
from perturbation rows, external validation rows, and new CFD rows, not by
withholding Salt4 nominal from the final training envelope.

This supersedes older scorecard language that treated `salt_2=train`,
`salt_3=validation`, and `salt_4=holdout` as the canonical final split. That old
split can still be cited as historical method-development evidence, but it is
not the target split for final thesis prediction.

## Files

- `canonical_final_predictive_split_policy.csv`: row-level split policy.
- `summary.json`: counts and guardrail flags.

## Guardrails

- Salt1 rows must be promoted into the same postprocessing schema as Salt2-4
  before final model training consumes them.
- Salt2 +/-5Q rows are holdout/testing only; do not fit or tune on them.
- `val_salt2` is external-test only and needs a matching heat-loss/admission
  package before blind scoring.
- Salt2/Salt4 +/-10Q rows remain blocked until live job `3293924` and harvester
  `3295438` finish and a terminal admission package lands.
- New Salt3 Q x insulation CFD should be staged only after current high-heat
  jobs are inspected, and should be admitted before use.

