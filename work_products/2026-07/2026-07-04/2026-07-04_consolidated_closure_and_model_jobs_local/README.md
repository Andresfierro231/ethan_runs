# Consolidated Closure And Model Jobs

Generated: `2026-07-04T09:54:09-05:00`

This package joins existing CFD-to-1D closure work products into one provenance-heavy table.
It does not run OpenFOAM and does not mutate case directories.

## Files

- `consolidated_closure_table.csv`: joined friction, HTC/UA', recirculation, model-comparison, and run-status rows.
- `consolidated_closure_summary_by_case.csv`: per-case row counts and admissibility counts.
- `consolidated_closure_summary.json`: source inventory and package counts.
- `next_1d_model_forms/`: lightweight 1D model-form screen generated from this table.

## Current Counts

- Rows: `78`
- Cases / run labels: `14`

## Admission Rules

- Nominal Salt Jin closure rows are kept as existing closure evidence with span-level quality flags.
- Salt perturbation runs are represented as `case_status` rows only; their false-steady status is not joined onto nominal closure rows.
- Rows with negative apparent friction remain in the table for auditability but are marked non-admissible.
- Water rows will become useful after job `3265970` exits and the dependent Water postprocess job reruns the inventory.
