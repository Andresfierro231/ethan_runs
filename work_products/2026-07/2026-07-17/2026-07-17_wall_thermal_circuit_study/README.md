---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder
  - work_products/2026-07/2026-07-17/2026-07-17_wall_temperature_drive_candidate
  - work_products/2026-07/2026-07-17/2026-07-17_heater_source_redistribution_coupled_score
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m2_m3_comparators.csv
tags: [forward-model, wall-circuit, test-section, parallel-fluid, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-WALL-THERMAL-CIRCUIT
task: AGENT-522
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Parallel Wall Thermal-Circuit Study

## Result

This package scores non-duplicative wall/passive/test-section thermal-circuit
lanes after AGENT-498 and AGENT-513. AGENT-511 heater-source redistribution is
imported read-only and is not duplicated by this package.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: No wall thermal-circuit candidate has passed validation and holdout mdot, TP, TW, and all-probe gates vs M3.

Coupled rows completed: `24`.
Status counts: `{"completed": 24}`.
Parallel workers requested: `8`.

## Performance Versus M3

Negative deltas are better. Admission requires validation and holdout mdot, TP,
TW, and all-probe deltas all to be non-positive.

| Candidate | Validation delta vs M3 | Holdout delta vs M3 |
| --- | --- | --- |
| `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` | mdot `5.60155454 pct`; TP `31.59316441 K`; TW `44.38313802 K`; all-probe `40.92215137 K` | mdot `4.7734292 pct`; TP `44.51143302 K`; TW `53.76425145 K`; all-probe `51.13236933 K` |
| `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `5.59716302 pct`; TP `31.58356844 K`; TW `44.39118812 K`; all-probe `40.92582874 K` | mdot `4.7698158 pct`; TP `44.50312607 K`; TW `53.76941638 K`; all-probe `51.13394954 K` |
| `HIW2_heated_incline_outer_surface_drive_PLUS_HX_LUMPED_UA_NTU` | mdot `-9.453601609 pct`; TP `6.14801145 K`; TW `43.43922072 K`; all-probe `35.50998181 K` | mdot `-19.34035362 pct`; TP `19.71497653 K`; TW `48.39267616 K`; all-probe `41.53743629 K` |
| `HIW2_heated_incline_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-9.44715866 pct`; TP `6.13756332 K`; TW `43.45655588 K`; all-probe `35.52279018 K` | mdot `-19.33526371 pct`; TP `19.7057306 K`; TW `48.4055279 K`; all-probe `41.54593881 K` |
| `TSC1_test_section_only_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` | mdot `-15.7100372 pct`; TP `11.85218417 K`; TW `42.40961549 K`; all-probe `35.45432717 K` | mdot `-12.91399165 pct`; TP `26.538614 K`; TW `48.70697444 K`; all-probe `43.0837913 K` |
| `TSC1_test_section_only_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-15.71582829 pct`; TP `11.84200409 K`; TW `42.42501909 K`; all-probe `35.46506801 K` | mdot `-12.9185215 pct`; TP `26.52977677 K`; TW `48.71772137 K`; all-probe `43.09025462 K` |
| `TSC2_test_section_only_outer_surface_drive_PLUS_HX_LUMPED_UA_NTU` | mdot `-9.181403381 pct`; TP `0.13911638 K`; TW `45.45492865 K`; all-probe `36.5527506 K` | mdot `-19.50466329 pct`; TP `13.75889144 K`; TW `49.00610831 K`; all-probe `41.07308412 K` |
| `TSC2_test_section_only_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-9.175534898 pct`; TP `0.12844226 K`; TW `45.47524243 K`; all-probe `36.56854139 K` | mdot `-19.50923507 pct`; TP `13.74911297 K`; TW `49.02172213 K`; all-probe `41.08418019 K` |


## Probe Localization

Probe delta rows: `272` with gate counts `{"fail": 206, "not_compared": 32, "pass": 34}`.

Worst compared probe deltas:
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` salt_4 TW5 (TW, heated_incline): `78.64861796 K` worse than M3
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW5 (TW, heated_incline): `78.64004194 K` worse than M3
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` salt_4 TW6 (TW, heated_incline): `71.05938137 K` worse than M3
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW6 (TW, heated_incline): `71.05100668 K` worse than M3

Worst role/segment RMSE deltas:
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` salt_4 TW heated_incline: `67.22153272 K`
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW heated_incline: `67.21305903 K`
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` salt_4 TW cooled_incline_pre_hx: `57.66080936 K`
- `HIW1_heated_incline_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW cooled_incline_pre_hx: `57.65290073 K`


## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `agent511_import_status.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `ag522_wall_circuit.sbatch`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
