---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output/coupled_scorecard.csv
tags: [status, hx, cooler, coupled-fluid, scheduler, source-property]
related:
  - .agent/journal/2026-07-22/hx-coupled-fluid-evaluation-scheduler.md
  - imports/2026-07-22_hx_coupled_fluid_evaluation_scheduler.json
task: TODO-HX-COUPLED-FLUID-EVALUATION-SCHEDULER-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Implementer / Tester / Writer / Monitor
type: status
status: complete
---
# TODO-HX-COUPLED-FLUID-EVALUATION-SCHEDULER-2026-07-22

## Objective

Make maximum source/property gate progress for the HX/cooler candidate, then
run the actual coupled Fluid evaluation on a scheduler-accounted compute path.

## Outcome

Completed. Source/property preflight remains fail-closed, but the diagnostic
coupled Fluid run executed successfully under Slurm allocation `3307325` on
`c318-008` using `srun`. The coupled output has `12/12` completed rows and
`12/12` accepted roots across `HX_LUMPED_UA_NTU` and the `N4/N8/N16`
segmented cooler variants.

The coupled QOI review does not admit or freeze any candidate:
`HX_LUMPED_UA_NTU` has max absolute mdot error `37.48196928%`, mean all-probe
RMSE `114.1543299 K`, and mean all-probe RMSE delta versus `M3TS_R0` of
`97.57853845 K`. The review gate is
`fail_diagnostic_large_coupled_errors_source_property_closed`.

## Changes Made

- Added a run-specific `--output-dir` option to `tools/analyze/build_cooler_removal_model.py`.
- Added the HX source/property preflight and post-run review builder plus tests.
- Published the scheduler package under `work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/**`.
- Recorded the launch contract, source/property gate state, coupled scorecard,
  QOI review, guardrails, status, journal, and import manifest.

## Validation

- `python3.11 tools/analyze/build_hx_coupled_fluid_evaluation_preflight.py` passed.
- `python3.11 -m unittest tools.analyze.test_hx_coupled_fluid_evaluation_preflight tools.analyze.test_cooler_removal_model` passed: `9` tests.
- `python3.11 -m py_compile tools/analyze/build_cooler_removal_model.py tools/analyze/build_hx_coupled_fluid_evaluation_preflight.py tools/analyze/test_cooler_removal_model.py tools/analyze/test_hx_coupled_fluid_evaluation_preflight.py` passed.
- Scheduler run: `srun -N1 --overlap -n1 python3.11 tools/analyze/build_cooler_removal_model.py --run-fluid --timeout-seconds 273 --output-dir work_products/2026-07/2026-07-22/2026-07-22_hx_coupled_fluid_evaluation_scheduler/coupled_fluid_output` completed with `12/12` coupled rows.

## Unresolved Blockers

- Source/property release-ready rows remain `0`; strict source-envelope pass
  rows remain `0`.
- The HX/cooler coupled scores are much worse than the M3+TS comparator and
  should not be used for admission prose.
- Fixed-mdot segmented duty scoring is still pending a native/replay runner and
  was not fabricated from coupled totals.

## Guardrails

No native-output mutation, registry/admission mutation, Fluid/external source
edit, thesis edit, source/property release, Qwall/numeric q-loss release,
coefficient admission, candidate freeze, final-score claim, refit,
model-selection promotion, protected scoring, hidden multiplier, residual
absorption into internal Nu, or runtime-leakage relaxation occurred.
