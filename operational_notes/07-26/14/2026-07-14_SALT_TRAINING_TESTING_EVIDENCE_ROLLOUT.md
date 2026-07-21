---
provenance:
  task: AGENT-369
  generated_by: codex
tags: [salt, cfd-pp, training-data, testing-data, admission, start-here]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/README.md
---
# Salt Training Testing Evidence Rollout

## Open This First

Future cfd-pp, closure-fit, forward-model, and thesis agents should open this
note before deciding which Salt CFD rows can train or test model fits.

The compact machine-readable table is:

`work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/salt_training_testing_case_use_table.csv`

## What Changed Today

Salt1 is no longer only diagnostic context for thermal closure training. A
patch-complete terminal BC table was built from the actual terminal `0/T`
dictionaries and boundary meshes for:

- `salt1_jin_nominal_continuation_corrected`
- `salt1_jin_lo10q_corrected`
- `salt1_jin_hi10q_corrected`

The Salt1 hi10q conflict is resolved. The older failed/not-admissible inventory
row is superseded by terminal harvest evidence plus the patch-complete BC table.
Use it as `training_perturbation`, not as nominal Salt1.

Salt4 nominal moved from holdout to training by user policy. Salt4 +/-5Q
perturbed-Q rows are training rows. Salt2 +/-5Q perturbed-Q rows are holdout rows.

## Current Use Policy

Training rows now available for thermal closure fitting:

- Salt1 nominal
- Salt1 lo10q
- Salt1 hi10q
- Salt4 nominal
- Salt4 lo5q
- Salt4 hi5q

Holdout/testing rows now available:

- Salt2 lo5q
- Salt2 hi5q

These rows have different roles. Do not silently treat Q perturbations as
independent nominal baselines.

## Pending Pressure/Upcomer Gate

Matched pressure/upcomer extraction for Salt2/Salt4 +/-5Q was submitted as
Slurm job `3295901` (`upc_pm5q`), but later accounting shows it was
`CANCELLED by 890970` before running (`Elapsed=00:00:00`). Do not make
pressure/upcomer admission claims until a replacement job runs, parsed
`matched_plane_metrics_*.csv` files exist, and those rows are reviewed.

Monitor:

```bash
squeue -j 3295901
sacct -j 3295901 --format JobID,JobName,State,Elapsed,ExitCode -P
```

## Evidence Packages

- Salt1 terminal BC and hi10q resolution:
  `work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/`
- Salt training promotion and legacy perturbation audit:
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_promotion_and_legacy_perturbation_audit/`
- Salt2/Salt4 +/-5Q terminal harvest and heat-role reduction:
  `work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/`
- Matched-plane submission package:
  `work_products/2026-07/2026-07-14/2026-07-14_pm5_corrected_q_matched_plane_unlock/`

## Do Not Do

- Do not reopen the old stale blocker that Salt1 hi10q is failed. It is resolved
  for thermal training use.
- Do not use Salt2 +/-5Q for training or model selection; they are holdout rows.
- Do not use legacy Salt4 `balq`/`hiins` rows as blind independent training.
- Do not claim pm5 pressure/upcomer metrics from `3295901`; it was cancelled
  before running.
- Do not mutate native CFD outputs.

## Good Next Steps

1. Decide whether to relaunch pm5 matched-plane extraction, then harvest and
   classify parsed matched-plane rows after the replacement job reaches terminal
   state.
2. Refresh older generated Salt inventory CSVs so they consume the Salt1
   resolution and do not report stale failed/context-only labels.
3. Update training scripts/configs to consume the `salt_training_testing_case_use_table.csv`
   split discipline directly.
4. Run closure fits with the expanded thermal training rows and Salt2 +/-5Q held
   out.
