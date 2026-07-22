---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score
  - work_products/2026-07/2026-07-17/2026-07-17_wall_thermal_circuit_study
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m2_m3_comparators.csv
tags: [forward-model, wall-fluid-coupling, test-section, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
task: AGENT-526
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Test-Section Wall/Fluid Coupling Candidate

## Result

This package implements the fallback after AGENT-511 heater-source redistribution
and AGENT-522 non-series wall thermal-circuit candidates failed admission. It
uses AGENT-511's Salt2-selected heater lambda and scores a test-section-only
bulk-to-ambient series resistance through internal convection/wall resistance
and setup external hA.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: No test-section wall/fluid series-coupling candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3.

Coupled rows completed: `6`.
Status counts: `{"completed": 6}`.

## Method

- Start from AGENT-511 only after its Salt2-only source selection was complete;
  the selected heater-source lambda is not re-fit on Salt3 or Salt4.
- Use the PB2 passive wall/test-section distribution and the Salt2 cooler
  alpha-UA candidates already admitted for coupled scoring.
- Apply the new thermal-circuit behavior only to the `left_upper_vertical`
  role row named `test_section`.
- Compute that role loss as bulk fluid temperature to ambient through
  `R_i_prime + R_wall_prime` in series with setup external `hA`. Other role
  rows keep Fluid's direct external hA behavior.
- Use an in-process adapter around Fluid's role-loss function for this run
  only. No persistent Fluid source, native CFD output, registry, or blocker
  register file is edited.

## Admission Gate

Admission requires the runtime audit to pass and both selected candidates to
beat M3 on validation and holdout absolute mdot error, TP RMSE, TW RMSE, and
all-probe RMSE. The coupled run completed, but both candidates failed validation
and holdout temperature gates while improving mdot.

## Local Test-Section Behavior

`local_test_section_behavior.csv` isolates TP5 plus adjacent upper-upcomer /
test-section bracket probes TP6 and TW8. These rows are diagnostic only: they
show whether the explicit series coupling helped local test-section behavior,
but they are not used for tuning or admission without the global gates.

## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `local_test_section_behavior.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
