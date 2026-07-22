---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_wall_passive_test_section_admission_closeout
  - work_products/2026-07/2026-07-17/2026-07-17_wall_test_section_distribution_ladder
  - work_products/2026-07/2026-07-17/2026-07-17_cooler_removal_model
  - work_products/2026-07/2026-07-16/2026-07-16_coupled_m3ts_test_section_scorecard/m2_m3_comparators.csv
  - work_products/2026-07/2026-07-14/2026-07-14_external_bc_thermal_profile_parity_study/external_bc_segment_equivalents.csv
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
tags: [forward-model, wall-circuit, wall-temperature-drive, test-section, predictive-1d]
related:
  - predictive-wall-test-section-submodels
  - TODO-PREDICT-TEST-SECTION-HEAT-LOSS
  - TODO-PREDICT-SEGMENT-THERMAL-MODELS
task: AGENT-513
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Wall-Temperature-Drive Candidate

## Result

This package tests the next wall/test-section unblock step after AGENT-507:
keep the Salt2 PB2 local distribution shape, but change only the upcomer
`ambient_wall` and `test_section` role-row passive-loss drive from bulk-fluid
temperature to a Fluid-solved wall state.

Decision for `predictive-wall-test-section-submodels`: `keep_open`.

Reason: No wall-temperature-drive candidate has passed validation and holdout mdot, all-probe, and TW gates vs M3.

## Candidate Set

- `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU`
- `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16`
- `WTD2_upcomer_test_section_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16`

The wall proxy fields in `static_drive_audit.csv` are score-only diagnostics.
At runtime the Fluid solver computes `T_pipe_outer_wall_K` or
`T_outer_surface_K`; validation/holdout wall temperatures are not consumed.

## Coupled Run

Coupled rows completed: `9`.
Status counts: `{"completed": 9}`.

## Performance Versus M3

Negative mdot delta is better. Negative all-probe and TW deltas would be better.

| Candidate | Validation delta vs M3 | Holdout delta vs M3 | Admission |
| --- | --- | --- | --- |
| `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_LUMPED_UA_NTU` | mdot `-15.77357666 pct`; all-probe `35.4367048 K`; TW `42.46078965 K` | mdot `-13.134776 pct`; all-probe `42.96748325 K`; TW `48.66546388 K` | `not_admitted` |
| `WTD1_upcomer_test_section_pipe_outer_wall_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `-15.76778041 pct`; all-probe `35.44761178 K`; TW `42.47636066 K` | mdot `-13.13930885 pct`; all-probe `42.97408557 K`; TW `48.67636533 K` | `not_admitted` |
| `WTD2_upcomer_test_section_outer_surface_drive_PLUS_HX_SEGMENTED_UA_NTU_N16` | mdot `15.88167939 pct`; all-probe `79.44517564 K`; TW `92.6772842 K` | mdot `3.89428802 pct`; all-probe `78.20608023 K`; TW `92.2922694 K` | `not_admitted` |


Replay command:

```bash
mkdir -p logs/2026-07-17 && srun -N1 -n1 python3 tools/analyze/build_wall_temperature_drive_candidate.py --run-fluid --timeout-seconds 273 > logs/2026-07-17/wall_temperature_drive_candidate.out 2> logs/2026-07-17/wall_temperature_drive_candidate.err
```

## Files

- `wall_candidate_definitions.csv`
- `candidate_definitions.csv`
- `static_drive_audit.csv`
- `static_candidate_gate.csv`
- `scenario_contracts.csv`
- `runtime_input_audit.csv`
- `coupled_scorecard.csv`
- `coupled_delta_vs_m3.csv`
- `probe_error_localization.csv`
- `probe_delta_vs_m3.csv`
- `role_segment_error_summary.csv`
- `candidate_admission_review.csv`
- `next_steps.csv`
- `background_run_contract.csv`
- `blocker_decision.json`
- `source_manifest.csv`
- `summary.json`
