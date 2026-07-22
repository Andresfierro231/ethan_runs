# Repeatability and 1D Refinement Guide

## Exact Rerun

From repo root:

```bash
python3.11 tools/analyze/build_best_predictive_heat_loss_discrepancy.py
python3.11 -m unittest tools.analyze.test_best_predictive_heat_loss_discrepancy
```

Expected row counts:

- `best_predictive_leg_heat_loss_discrepancy.csv`: 15 rows.
- `best_predictive_case_heat_loss_summary.csv`: 3 rows.
- `model_change_recommendations.csv`: 5 rows.

## Dependencies

The package uses only existing CSV/markdown work products:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_results.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_segment_states.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_vs_fast_scan_comparison.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_3d_1d_heat_loss_alignment/heat_loss_alignment_by_segment.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv`

No native CFD solver outputs, Slurm jobs, or external Fluid source edits are
required to reproduce this package.

## How to Reuse After Refining the 1D Model

1. Land the new 1D model outputs as a new forward package with per-segment
   `Q_source_W`, `Q_hx_sink_W`, and `Q_ambient_W` or equivalent columns.
2. Update or parameterize `BEST_VARIANT` and the forward-results/segment-state
   paths in the builder.
3. Confirm every Fluid `parent_segment` maps to one of the five comparison legs.
4. Rerun the builder and tests.
5. Compare the new leg discrepancies to this baseline:
   - junction under-loss should shrink;
   - pipe-leg over-loss should not grow;
   - aggregate heat balance should not be the only success metric;
   - Salt3 and Salt4 should be scored without refit if Salt2 trains a scalar.

## What Not To Do

- Do not use realized CFD `wallHeatFlux` as a runtime predictive input.
- Do not use CFD mdot as a runtime predictive input.
- Do not call imposed cooler duty final predictive HX.
- Do not hide junction or heater errors inside one global ambient multiplier.
