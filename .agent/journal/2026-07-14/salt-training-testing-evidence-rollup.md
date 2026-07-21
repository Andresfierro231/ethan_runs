---
provenance:
  task: AGENT-369
  generated_by: codex
tags: [salt, cfd-pp, training-data, testing-data, admission, journal]
related:
  - .agent/status/2026-07-14_AGENT-369.md
  - operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/README.md
---
# Salt Training Testing Evidence Rollup Journal

## Why This Exists

The July 14 cfd-pp work promoted newly available Salt CFD rows for thermal
closure training/testing, resolved the Salt1 hi10q conflict, and separated
thermal use from still-pending pressure/upcomer metric extraction. Future agents
needed one authoritative start-here note and compact table so the newly usable
cases are not missed or mislabeled.

## Observed Facts

- Salt1 nominal, lo10q, and hi10q have terminal-harvest and patch-complete BC
  evidence in
  `work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/`.
- The older Salt1 hi10q failed/not-admissible row is superseded for thermal
  training use by the AGENT-363 terminal harvest and BC evidence.
- Salt4 nominal is training by user policy.
- Salt4 +/-5Q perturbed-Q rows are training rows.
- Salt2 +/-5Q perturbed-Q rows are holdout/testing rows.
- Scheduler accounting for job `3295901` (`upc_pm5q`) reports
  `CANCELLED by 890970`, `Elapsed=00:00:00`, so the pm5 pressure/upcomer
  extraction did not produce admitted metrics.

## Inferred Interpretation

The thermal closure training set can be expanded immediately with six Salt rows:
Salt1 nominal/lo10q/hi10q and Salt4 nominal/lo5q/hi5q. Salt2 lo5q/hi5q should
be preserved as holdout/testing evidence. Pressure/upcomer use remains blocked
until the cancelled matched-plane extraction is replaced and reviewed.

## Documentation Written

- Main future-agent note:
  `operational_notes/07-26/14/2026-07-14_SALT_TRAINING_TESTING_EVIDENCE_ROLLOUT.md`
- Work-product package:
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/`
- Compact use table:
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/salt_training_testing_case_use_table.csv`
- Follow-on action contract:
  `work_products/2026-07/2026-07-14/2026-07-14_salt_training_testing_evidence_rollup/next_agent_action_contract.csv`

## Next Required Work

1. Investigate and relaunch the pm5 matched-plane extraction if pressure/upcomer
   metrics are still needed.
2. Refresh older generated inventory/admission CSVs so Salt1 no longer appears
   context-only and Salt1 hi10q no longer appears failed for thermal training.
3. Update closure-fit scripts/configs to consume
   `salt_training_testing_case_use_table.csv` and preserve the Salt2 holdout
   role.
4. Keep legacy `balq`/`hiins` rows out of blind training unless source
   restoration and operating-point gates are completed.

## Verification

The rollup package was validated with a CSV/JSON count check:

- case rows: 10
- thermal training rows: 6
- holdout rows: 2
- pressure/upcomer rows blocked by cancelled job: 4
- next-action rows: 5

Native CFD solver outputs were not mutated.
