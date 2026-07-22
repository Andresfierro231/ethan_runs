# Repeatability and Refinement Guide

## Exact Rerun

From repo root:

```bash
python3.11 tools/analyze/build_external_bc_thermal_profile_parity_study.py
python3.11 -m unittest tools.analyze.test_external_bc_thermal_profile_parity_study
```

## Expected Row Counts

- `external_bc_patch_contract.csv`: 207 rows.
- `external_bc_segment_equivalents.csv`: 24 rows.
- `source_sink_parity_contract.csv`: 12 rows.
- `section_heat_loss_comparison.csv`: 15 rows.
- `thermal_profile_drive_comparison.csv`: 15 rows.
- `case_summary.csv`: 3 rows.
- `admission_decision_table.csv`: 5 rows.

## Reuse With a Refined 1D Model

1. Land the new 1D run with per-segment heat source, HX loss, and ambient loss
   columns.
2. Rebuild the leg-level discrepancy table against the same CFD contract.
3. Do not judge success by aggregate heat balance alone.
4. Check whether junction under-loss shrinks and pipe-leg over-loss does not
   grow.
5. If fitting a wall-adjacent or mixing-factor drive, train only on Salt2,
   validate on Salt3, and hold out Salt4.

## Guardrails

- Do not use realized CFD wallHeatFlux, CFD mdot, or validation temperatures as
  runtime predictive inputs.
- Do not add a separate radiation term to realized CFD wallHeatFlux.
- Do not call imposed cooler duty final predictive HX.
- Do not hide heater, cooler, junction, or wall-drive errors in one global
  ambient multiplier.
