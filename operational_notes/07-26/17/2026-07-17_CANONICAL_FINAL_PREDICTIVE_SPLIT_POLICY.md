---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-16/2026-07-16_salt1_durable_test_data_and_thesis_story/README.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_external_test_and_q_unlock_admission/split_admission_decisions.csv
  - work_products/2026-07/2026-07-16/2026-07-16_recirculation_cfd_anchor_study_design/README.md
tags: [forward-predictive-model, split-policy, salt-cfd, cfd-postprocessing]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/cfd-runs-and-admission.md
  - .agent/status/2026-07-17_AGENT-481.md
task: AGENT-481
date: 2026-07-17
role: Coordinator/Writer
type: operational_note
status: complete
---
# Canonical Final Predictive Split Policy

## Decision

The final predictive model should train across the admitted Salt1-4 nominal
operating envelope:

```text
final training = Salt1 nominal + Salt2 nominal + Salt3 nominal + Salt4 nominal
```

The final model should not treat Salt4 nominal as the untouched canonical
holdout. Testing and holdout evidence should instead come from perturbation
rows, external validation rows, and new CFD rows that are admitted under the
same postprocessing contract.

## Current Split

Use
`work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv`
as the dated source of truth.

Summary:

- `final_training`: `salt1_nominal`, `salt2_jin_nominal`,
  `salt3_jin_nominal`, `salt4_nominal`
- `training_support`: `salt1_lo10q`, `salt1_hi10q`, `salt4_lo5q`,
  `salt4_hi5q`
- `holdout_testing`: `salt2_lo5q`, `salt2_hi5q`
- `external_test`: `val_salt2`, after matching heat-loss/admission package
- `future_holdout_candidate`: Salt2/Salt4 +/-10Q, after `3293924` and `3295438`
  finish and terminal admission is complete
- `new_cfd_holdout_candidate`: Salt3 Q x insulation/onset matrix from AGENT-478,
  after non-duplicate staging, run completion, and admission

## Terminology

- `PM5`: plus/minus 5Q corrected-Q perturbation rows. In this split policy,
  current PM5 usage mainly means Salt2 +/-5Q holdout/testing rows after repaired
  matched-plane and wall-band extraction; PM5 rows are fit-forbidden unless a
  later policy row explicitly says otherwise.
- `PM10`: plus/minus 10Q corrected-Q perturbation rows. In this split policy,
  PM10 means `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q`;
  after terminal admission they are future/frozen-model holdout scoring rows,
  not fit, model-selection, or runtime-input rows.

## Work Queue Added

Four board TODOs were added:

- `TODO-PREDICT-SALT1-SCHEMA-PROMOTION`
- `TODO-PREDICT-SALT2-PM5-HOLDOUT-EXTRACTION-REPAIR`
- `TODO-PREDICT-VAL-SALT2-EXTERNAL-LEDGER`
- `TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION`

## Guardrails

- Do not consume Salt1 final-training rows until they are promoted into the
  same postprocessing schema as Salt2-4.
- Do not fit or tune on `salt2_lo5q` or `salt2_hi5q`.
- Do not score `val_salt2` as blind external validation until its matching
  section heat-loss ledger and admission package exist.
- Do not use Salt2/Salt4 +/-10Q until the live solver/harvester chain is
  terminal and admitted.
- Do not mutate native CFD outputs; use staged copies for any OpenFOAM
  postprocessing repair.
