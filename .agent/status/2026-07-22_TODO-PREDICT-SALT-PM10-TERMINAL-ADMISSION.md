---
provenance:
  - tools/analyze/build_salt_pm10_terminal_admission.py
  - tools/analyze/test_salt_pm10_terminal_admission.py
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission/summary.json
task: TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION
date: 2026-07-22
role: cfd-pp / Scheduler / Thermal-modeling / Hydraulics / Upcomer-onset / Implementer / Tester / Writer
type: status
status: complete
tags: [status, pm10, terminal-admission, holdout, recirculation, guardrails]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_predict_salt_pm10_terminal_admission
---

# TODO-PREDICT-SALT-PM10-TERMINAL-ADMISSION

## Objective

Build a read-only terminal/admission disposition packet for `salt2_lo10q`,
`salt2_hi10q`, `salt4_lo10q`, and `salt4_hi10q` after the `3293924` solver
chain and `3295438` dependent harvester reached terminal states.

## Outcome

Decision: `terminal_admitted_for_future_blind_holdout_evidence_only`.

Current scheduler evidence is terminal: `3293924` is `TIMEOUT` after
`5-00:00:06`, with cancelled `foamRun` steps, and `3295438` is `COMPLETED`.
`squeue -j 3293924,3295438` returned no live rows on 2026-07-22.

All four PM10 cases pass the existing strict terminal drift/log gate and have
finite mdot, TP/T, TW, and recirculation diagnostic evidence. They remain
future blind-holdout rows: no fit, no model selection, no runtime input release,
no source/property release, and no protected score until a candidate has been
frozen independently.

Representative mdot windows are steady. Late-window mdot drift from the terminal
classification ranges from `-0.486409%` to `0.101132%` for the four rows.
Representative `total_Q` remains `not steady (drifting)` for all four rows, with
relative drift from `0.085013` to `0.095690`; therefore heat/source release
remains forbidden.

Upcomer evidence classifies all four rows as `strong_recirculation`
diagnostics. Ordinary upcomer `Nu`, `f_D`, or component-`K` fitting remains
forbidden.

## Changes Made

- Added `tools/analyze/build_salt_pm10_terminal_admission.py`.
- Added `tools/analyze/test_salt_pm10_terminal_admission.py`.
- Wrote `scheduler_terminal_evidence.csv`.
- Wrote `pm10_case_terminal_gate.csv`.
- Wrote `pm10_steadiness_metric_context.csv`.
- Wrote `pm10_split_use_decision.csv`.
- Wrote `pm10_recirc_onset_summary.csv`.
- Wrote `pm10_heat_pressure_evidence_inventory.csv`.
- Wrote `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`,
  and package README.

## Validation

- `python3.11 tools/analyze/build_salt_pm10_terminal_admission.py`: passed;
  emitted `4` terminal-evidence admitted rows, `0` fit/model-selection/current
  protected-score rows, and `4` total-Q-drifting rows.
- `python3.11 -m pytest tools/analyze/test_salt_pm10_terminal_admission.py`:
  passed, `3` tests.
- `squeue -j 3293924,3295438 -o %i,%j,%T,%M,%D,%R`: no live rows.
- `sacct -j 3293924,3295438 --format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList -P`:
  `3293924 TIMEOUT`, `3295438 COMPLETED`.

## Guardrails

- Native CFD/OpenFOAM output mutation: none.
- Registry/admission mutation: none.
- Scheduler action: none; read-only `squeue`/`sacct` only.
- Staging, solver, harvester, sampler, and Fluid launch: none.
- Fitting, model selection, protected scoring, source/property/Qwall release,
  and runtime input release: none.
- Residual absorption into internal `Nu`: none.

## Next Useful Work

Use this packet as source evidence for the recirculation/onset thesis packet and
as a terminal-use gate for future pressure-ladder/streamwise-pressure maps. Do
not use the PM10 rows in final scorecard scoring until an independent freeze
exists.
