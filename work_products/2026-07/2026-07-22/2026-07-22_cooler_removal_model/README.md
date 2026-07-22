---
provenance:
  - operational_notes/07-26/17/2026-07-17_COOLER_MODEL_COMPREHENSIVE_TEST_PLAN.md
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/setup_only_cooler_closure_bakeoff/cooler_model_scores.csv
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m3ts_coupled_scorecard.csv
  - tools/analyze/build_cooler_removal_model.py
tags: [forward-model, cooler, hx, predictive-1d, candidate-screen]
related:
  - TODO-PREDICT-COOLER-REMOVAL
  - predictive-wall-test-section-submodels
task: TODO-PREDICT-COOLER-REMOVAL
date: 2026-07-22
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Cooler Removal Model Candidate Screen

This package implements the current cooler comparison plan for the two next
model families: constant-UA effectiveness/NTU and segmented distributed-UA
effectiveness/NTU.

## Result

- `HX_LUMPED_UA_NTU` reproduces the existing split-legal fixed-mdot cooler duty
  evidence from AGENT-438. It fits one Salt2 scalar and scores Salt3/Salt4
  without refit.
- `HX_SEGMENTED_UA_NTU_N4/N8/N16` are implemented as predeclared coupled-run
  candidates with one global `alpha_UA`. Because the sibling Fluid source tree
  was read-only in this Ethan session, segmented behavior is injected only by
  `tools/analyze/build_cooler_removal_model.py --run-fluid` at runtime.
- Fixed-mdot segmented duty rows are intentionally marked pending. They should
  not be fabricated from coupled totals because coupled `Q_hx` changes with the
  solved mdot and loop state.
- A bounded coupled Fluid attempt does not admit a cooler candidate unless
  completed score rows exist and pass coupled review.

## Coupled Run State

`--run-fluid` executed: `False`.

Per-row timeout seconds: `90`.

Completed coupled rows: `0`.

Coupled row status counts: `{"not_run_use_--run-fluid_on_compute_node": 12}`.

If coupled rows are still pending or timed out, rerun on a compute node with a
larger timeout after confirming the solve path is not stuck:

```bash
python3 tools/analyze/build_cooler_removal_model.py --run-fluid --timeout-seconds 273
```

## Files

- `candidate_definitions.csv`
- `fit_parameters.csv`
- `duty_scorecard.csv`
- `coupled_scorecard.csv`
- `segmented_profile_diagnostics.csv`
- `runtime_input_audit.csv`
- `model_comparison_decision.json`
- `source_manifest.csv`
- `summary.json`
