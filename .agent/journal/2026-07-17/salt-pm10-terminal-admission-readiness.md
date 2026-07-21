---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_canonical_final_predictive_split_policy/canonical_final_predictive_split_policy.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_salt_pm10_terminal_admission_readiness/
tags: [salt, pm10, terminal-admission, holdout, recirculation]
related:
  - .agent/status/2026-07-17_AGENT-493.md
  - imports/2026-07-17_salt_pm10_terminal_admission_readiness.json
task: AGENT-493
date: 2026-07-17
role: Coordinator/cfd-pp/Hydraulics/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# Salt PM10 Terminal Admission Readiness

## What The TODO Means

`TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION` is the gate for Salt2/Salt4
`+/-10Q` corrected-Q cases to become legal future holdout score rows. The
canonical split policy lists `salt2_lo10q`, `salt2_hi10q`, `salt4_lo10q`, and
`salt4_hi10q` as future holdout candidates with no fitting or model selection
allowed before terminal admission.

## Current State

Read-only `sacct` shows `3293924` still `RUNNING` and `3295438` still
`PENDING`. Therefore PM10 terminal admission cannot be completed honestly today.
The readiness package records `4/4` cases as `blocked_live_job` and `0` as ready
for terminal admission.

All four cases have prior July 9 steady-window stats available, but those are
not enough to supersede the live continuation/harvest gate. The terminal package
must wait for the current jobs to finish and then use the terminal artifacts.

## What PM5 Postprocessing Was

The PM5 work was not a blind rerun of the broken July 14 script. AGENT-406 used
scratch copies, repaired the stale `controlDict` include problem only in those
copies, reconstructed representative-time fields, sampled upcomer
inlet/mid/outlet planes and wall-band surfaces, validated required fields, and
parsed recirculation and wall-core metrics. AGENT-486 then reused the repaired
Salt2 +/-5Q rows for holdout diagnostics with `0` fit-admitted rows.

## PM10 Next Sequence

1. Refresh scheduler state for `3293924` and `3295438`.
2. If either job is still live, monitor only.
3. If both jobs complete successfully, claim a new PM10 extraction/admission
   task.
4. Repeat the PM5 scratch-copy matched-plane/wall-band workflow for four PM10
   cases and three planes each.
5. Publish field validation, metric rows, terminal admission rows, runtime
   leakage audit, and mesh/time uncertainty state.
6. Keep all PM10 rows out of fitting/model selection unless a later policy
   explicitly admits them.

## Guardrails

No native solver outputs, registry/admission state, scheduler state, external
Fluid files, or generated index files were mutated. No OpenFOAM or Fluid
postprocessing was launched.
