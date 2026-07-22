---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_fluid_timeout_and_wall_circuit_study
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
tags: [forward-model, wall-circuit, test-section, coupled-score, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: AGENT-494
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Test-Section Coupled Admission

## Result

This package promotes `PB1_total_hA_heater_power_drive_p1` from AGENT-492 into
explicit PB1+cooler coupled scenario contracts and keeps local test-section
evidence separate from passive-total heat-loss cancellation.

Decision for `predictive-wall-test-section-submodels`:
`keep_open`.

Reason: PB1 passive-total static evidence is promising, but no PB1+cooler candidate has passed all coupled admission gates.

## Coupled Run Status

Coupled Fluid scoring has been run in this package. Completed rows: `12`; status counts: `{"completed": 12}`. The background command remains documented in `background_run_contract.csv` for reproducibility, but no rerun is required for this package.

## Files

- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `static_component_scorecard.csv`
- `static_component_summary.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `coupled_admission_review.csv`
- `runtime_input_audit.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
