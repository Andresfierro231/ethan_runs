# Ethan Runtime And Hypothesis Matrix

This report separates three questions:

- which rows should continue now,
- which rows are usable for diagnostic analysis as they stand,
- which rows point more strongly toward alternate assumptions than toward more runtime.

## Default runtime recommendation

- Do not submit a blanket continuation campaign for every non-converged Ethan row.
- Treat `val_salt_test_2_coarse_mesh_laminar` as the only already-justified active continuation target.
- If continuation jobs are submitted, default to 64 MPI ranks per run and pack 3 runs per 256-core node before attempting 4-up packing. That is a conservative memory headroom choice and is sufficient for the current physics-audit stage.

## Decision labels

- `continue_now`: runtime evidence still supports extending the case.
- `analyze_as_diagnostic_only`: useful for time-history and trend interpretation, but not currently worth a dedicated continuation submission.
- `alternate_case_first`: current mismatch is better explained by setup assumptions than by more runtime.
- `analyze_as_steady_state`: converged and ready for downstream steady-state reduction work.

## Alternate-case rules

- When CFD underpredicts external loss badly, thicker insulation is not the first next case.
- Radiation-on sensitivity and wall-loss boundary recalibration come before insulation-thickening in that regime.

