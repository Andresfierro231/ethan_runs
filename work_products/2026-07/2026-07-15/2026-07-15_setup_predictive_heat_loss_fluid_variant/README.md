# Setup-Predictive Heat-Loss Fluid Variant

Task: AGENT-418  
Generated: 2026-07-15

## Result

Implemented the first active Fluid 1D variant for setup-predictive segment heat
losses. `outer_closure_mode: external_boundary_table` now changes actual
passive heat-loss calculation, not just diagnostics.

## Implemented Capabilities

- External h/Ta/Tsur/emissivity setup dictionaries.
- Junction/stub/connector coverage multiplier through
  `external_boundary_coverage_multiplier_by_parent_segment`.
- Bulk, pipe-outer-wall, and outer-surface drive selectors through
  `external_boundary_drive_selector_by_parent_segment`.
- Compatibility with the setup-only `hx_ua_multiplier` hook.
- No runtime use of realized CFD `wallHeatFlux`, CFD mdot, imposed CFD cooler
  duty, or validation temperatures.

## Dry-Run Evidence

Rows: 6

The demonstration table shows:

- warmer external Ta reduces computed passive loss;
- junction coverage multiplier scales computed loss;
- wall/shell drive selectors reduce computed loss relative to bulk drive.

## Files

- `fluid_variant_contract.csv`
- `dry_run_segment_loss_demonstration.csv`
- `source_manifest.csv`
- `summary.json`

## Validation

- Focused Fluid contract tests: passed.
- Python compilation of modified Fluid source/tests: passed.
- Full `tests.test_solver_contracts` was started but stopped because unrelated
  solver-heavy tests exceeded the interactive turn budget.
