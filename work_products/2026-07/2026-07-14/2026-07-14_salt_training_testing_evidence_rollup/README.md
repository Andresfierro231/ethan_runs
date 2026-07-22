---
provenance:
  task: AGENT-369
  generated_by: codex
tags: [salt, cfd-pp, training-data, testing-data, admission, handoff]
related:
  - operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/README.md
---
# Salt Training Testing Evidence Rollup

This is the compact handoff for future agents. Use
`salt_training_testing_case_use_table.csv` before fitting or scoring closure
models. It records the cases that became usable on 2026-07-14, their split role,
and the exact evidence packages that justify use.

## Use Now

Training thermal closure rows:

- `salt1_jin_nominal_continuation_corrected`
- `salt1_jin_lo10q_corrected`
- `salt1_jin_hi10q_corrected`
- `salt4_jin`
- `salt4_jin_lo5q_corrected`
- `salt4_jin_hi5q_corrected`

Holdout/testing thermal closure rows:

- `salt2_jin_lo5q_corrected`
- `salt2_jin_hi5q_corrected`

## Still Pending

Pressure/upcomer metrics for Salt2/Salt4 +/-5Q are not admitted yet. Job
`3295901` (`upc_pm5q`) was submitted but later accounting shows it was
`CANCELLED by 890970` before running (`Elapsed=00:00:00`). Relaunch or document a
replacement path before making pressure/upcomer claims.

## Guardrails

- Keep every Q-perturbed row labeled as perturbed-Q.
- Do not use Salt2 +/-5Q for model selection; they are holdout rows.
- Do not call legacy `hiins` high-insulation unless a restored source proves an
  insulation mutation. Current trusted label is high-Q / balanced-cooling /
  baseline-insulation for those legacy rows.
- Do not use legacy Salt4 `balq`/`hiins` as blind independent training rows.

## Files

- `salt_training_testing_case_use_table.csv`: case-level use policy.
- `next_agent_action_contract.csv`: concrete follow-up actions and prohibitions.
- `source_manifest.csv`: exact source package references.
