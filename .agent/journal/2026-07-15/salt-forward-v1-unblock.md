---
provenance:
  task: AGENT-402
  generated_by: codex
tags: [salt, cfd-pp, forward-v1, unblock, journal]
related:
  - .agent/status/2026-07-15_AGENT-402.md
  - work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock/README.md
---
# Salt Forward-v1 Unblock Journal

## Observed Facts

- `3293924` corrected Salt-Q selected continuation is still running.
- `3295438` Salt2/Salt4 selected harvester is still pending on dependency.
- `3295901` and `3295968` PM5 batch jobs were cancelled before running.
- PM5 interactive run `interactive_3295120_retry2` completed and wrote 4 parsed
  CSVs with 12 rows, but all rows are `incomplete` with missing sampled fields.
- Salt thermal closure training now has 6 usable rows and 2 holdout rows from
  the July 14 Salt training/testing rollout.
- AGENT-391 setup-only cooler bakeoff completed and identified
  `salt2_fit_constant_UA_bulk_drive` as a setup-legal candidate with
  all non-Salt1 RMSE `4.63756559107 W`.
- AGENT-392 thermal rescue completed all 8 stages with failed stage count `0`,
  including setup-only HX fit and tests.
- Sensor targets remain runtime-disallowed; `TP2` and `TW10` are blocked.

## Interpretation

The next PM5 action is not simply to wait or resubmit the same job. The
extraction must be repaired so plane outputs include `U/rho/T` and wall-band
outputs include wall `T` plus `wallHeatFlux`. The Salt thermal training rows can
be consumed immediately by closure-fit work, provided Salt2 +/-5Q remain
holdout/testing and Q perturbations remain labeled.

## Work Product

Created:

`work_products/2026-07/2026-07-15/2026-07-15_salt_forward_v1_unblock/`

The package contains scheduler state, PM5 recovery audit, Salt training input,
stale refresh actions, setup-only HX actions, sensor policy actions, source
manifest, and summary JSON.

## Next Actions

1. Claim a separate PM5 extraction-repair row if changing/rerunning matched-plane
   extraction. Fix field emission before rerun.
2. Feed `salt_training_fit_input_table.csv` into the next closure-fit package.
3. Refresh stale blocker/inventory docs that still describe PM5 as pending or
   Salt1 as context-only.
4. Carry `salt2_fit_constant_UA_bulk_drive` into the next forward-v1 scorecard
   candidate, with runtime-input audit.
5. Keep `TP2` and `TW10` excluded from complete sensor scoring until coordinate
   or HX-shell policy is resolved.

No native CFD outputs, registry state, generated index files, or external Fluid
files were mutated.
