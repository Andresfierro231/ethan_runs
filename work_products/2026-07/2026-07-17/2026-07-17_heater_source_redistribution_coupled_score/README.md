---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m2_m3_comparators.csv
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
tags: [forward-model, heater-source, test-section, heat-placement, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-WALL-THERMAL-CIRCUIT
task: AGENT-511
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Heater Source Redistribution Coupled Score

## Result

This package tests whether moving the setup heater power axially between TW4,
TW5, TW6, and TP3 can repair the temperature-shape failure left by the PB2
wall/passive distribution model.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: No Salt2-fit heater-source redistribution candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3.

Selected Salt2 lambda: `0`.
Selection status: `selected_from_salt2_only`.

## Coupled Run

Coupled rows completed: `27`.
Status counts: `{"completed": 27}`.

Background command for replay:

```bash
mkdir -p logs/2026-07-17 && srun -N1 -n1 python3 tools/analyze/build_heater_source_redistribution_coupled_score.py --run-fluid --timeout-seconds 273 > logs/2026-07-17/heater_source_redistribution_coupled_score.out 2> logs/2026-07-17/heater_source_redistribution_coupled_score.err &
```

## Files

- `heater_source_lambda_grid.csv`
- `selected_heater_source_weights.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
