---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_coupled_admission
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m2_m3_comparators.csv
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/sensor_level_errors.csv
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
tags: [forward-model, wall-circuit, test-section, heat-placement, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: AGENT-498
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall/Test-Section Distribution Ladder

## Result

This package advances the AGENT-494 failure mode from passive-total heat loss to
local heat-placement. It defines two Salt2-trained local distribution candidates
and gates them against M3 on mdot, all-probe RMSE, and TW RMSE.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: No local wall/test-section distribution candidate has passed validation and holdout mdot, all-probe, and TW gates vs M3.

## Coupled Run

Coupled rows completed: `12`.
Status counts: `{"completed": 12}`.

## Performance Versus M3

Negative mdot delta is better. Negative all-probe and TW deltas would be better;
the completed candidates all improve mdot but regress temperature shape.

| Candidate | Validation delta vs M3 | Holdout delta vs M3 | Admission |
| --- | --- | --- | --- |
| `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_LUMPED_UA_NTU` | mdot `-15.64535145 pct`; all-probe `35.4599137 K`; TW `42.39586766 K` | mdot `-12.85262822 pct`; all-probe `43.11664296 K`; TW `48.71908999 K` | `not_admitted` |
| `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-15.65114081 pct`; all-probe `35.470608 K`; TW `42.41122425 K` | mdot `-12.85715657 pct`; all-probe `43.12306786 K`; TW `48.72979409 K` | `not_admitted` |
| `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_LUMPED_UA_NTU` | mdot `-11.30109382 pct`; all-probe `36.0150509 K`; TW `44.50322797 K` | mdot `-17.50605109 pct`; all-probe `41.25189604 K`; TW `48.6768088 K` | `not_admitted` |
| `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-11.29531994 pct`; all-probe `36.02976758 K`; TW `44.52254535 K` | mdot `-17.51055099 pct`; all-probe `41.26196237 K`; TW `48.69140384 K` | `not_admitted` |


## Probe Localization

Probe delta rows: `136` with gate counts `{"fail": 106, "not_compared": 16, "pass": 14}`.

Worst compared probe deltas:
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_LUMPED_UA_NTU` salt_4 TW5 (TW, heated_incline): `60.5946788 K` worse than M3
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW5 (TW, heated_incline): `60.58559098 K` worse than M3
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_LUMPED_UA_NTU` salt_4 TW6 (TW, heated_incline): `53.00942799 K` worse than M3
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW6 (TW, heated_incline): `53.00049652 K` worse than M3

Worst role/segment RMSE deltas:
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_LUMPED_UA_NTU` salt_4 TW heated_incline: `49.41457512 K`
- `PB2_salt2_local_shape_passive_hA_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW heated_incline: `49.40567017 K`
- `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_LUMPED_UA_NTU` salt_4 TW heated_incline: `39.64970968 K`
- `PB3_upcomer_test_section_attenuated_shape_p1_PLUS_HX_SEGMENTED_UA_NTU_N16` salt_4 TW heated_incline: `39.64009282 K`


Background command for replay:

```bash
mkdir -p logs/2026-07-17 && srun -N1 -n1 python3 tools/analyze/build_wall_test_section_distribution_ladder.py --run-fluid --timeout-seconds 273 > logs/2026-07-17/wall_test_section_distribution_ladder.out 2> logs/2026-07-17/wall_test_section_distribution_ladder.err &
```

## Files

- `segment_heat_placement_audit.csv`
- `probe_shape_regression_audit.csv`
- `local_candidate_definitions.csv`
- `candidate_definitions.csv`
- `static_candidate_gate.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`

## Legacy Extra Files

If present, `admission_review.csv` and `coupled_distribution_scorecard.csv` are
leftovers from a superseded earlier D0-D4 package state in this same directory.
They are not listed in `source_manifest.csv`, `summary.json`, or this canonical
file list and should not be used as AGENT-498 evidence.
