---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model/README.md
tags: [journal, AGENT-482, cooler, hx, predictive-1d]
related:
  - .agent/status/2026-07-17_AGENT-482.md
  - imports/2026-07-17_cooler_removal_model_implementation.json
  - operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md
task: AGENT-482
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Cooler Removal Model Implementation

## Files Inspected

- `operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md`
- `work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/setup_only_cooler_closure_bakeoff/cooler_model_scores.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv`
- `.agent/BLOCKERS.md`
- `.agent/BOARD.md`

## Files Changed

- `tools/analyze/build_cooler_removal_model.py`
- `tools/analyze/test_cooler_removal_model.py`
- `work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model/*`
- `.agent/status/2026-07-17_AGENT-482.md`
- `.agent/journal/2026-07-17/cooler-removal-model-implementation.md`
- `imports/2026-07-17_cooler_removal_model_implementation.json`
- `operational_notes/maps/forward-predictive-model.md`

## Observed Output

The constant-UA effectiveness/NTU cooler candidate reproduces the prior
split-legal AGENT-438 duty screen: Salt3 validation error is `2.869104004 W`
and Salt4 holdout error is `7.502618613 W`. Runtime-input audit passes.

The coupled score is not admitted. A compute-node bounded run with
`--run-fluid --timeout-seconds 45` attempted `12` candidate/case rows and all
`12` timed out. No coupled mdot/TP/TW score row completed in AGENT-482.

## Interpretation

Cooler-duty magnitude is promising in the duty-only screen, but AGENT-482 does
not close or narrow `predictive-wall-test-section-submodels` enough for
admission because the coupled scorecard has no completed Fluid rows. The
segmented distributed-UA candidates are defined and runtime-audited, but their
fixed-mdot duty rows remain pending because coupled totals must not be used as
stand-ins for fixed-mdot replay totals.

## Commands Run

- `python3 -m unittest tools.analyze.test_cooler_removal_model`
- `python3 -m py_compile tools/analyze/build_cooler_removal_model.py tools/analyze/test_cooler_removal_model.py`
- `python3 tools/analyze/build_cooler_removal_model.py`
- `python3 tools/analyze/build_cooler_removal_model.py --run-fluid`
- Final bounded: `python3 tools/analyze/build_cooler_removal_model.py --run-fluid --timeout-seconds 45`

The first Fluid-backed generation exposed a diagnostics bug: the runtime-only
segmented adapter captured every nonlinear solver iteration and produced an
oversized `segmented_profile_diagnostics.csv`. The builder was corrected to
keep only the latest profile per candidate/case/segment/cell, the package was
regenerated, and the final durable package is the bounded `45 s` run state.

## Next Action

Do not promote a cooler model from this package alone. Next work should either
diagnose the Fluid runtime path and rerun with a justified larger timeout, or
advance `TODO-PREDICT-WALL-THERMAL-CIRCUIT` / `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`
so the coupled model has better wall/test-section physics before another
admission attempt.
