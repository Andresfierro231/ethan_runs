# TODO-LITREV-RESET-NAMED-LOSSES Status

Date: `2026-07-13`

Role: `Implementer / Tester / Writer`

## Observed Facts

- Built `work_products/2026-07/2026-07-13/2026-07-13_litrev_reset_named_losses/`.
- Primary outputs:
  - `reset_distance_map.csv`: 33 reset rows.
  - `named_pressure_loss_table.csv`: 33 named pressure-loss rows.
- The package consumed CFD validity naming limits when available.

## Inferred Interpretation

Pressure-loss residuals should remain localized as straight-section,
component-K, cluster-K, or branch-apparent terms. A global friction multiplier
is not recommended.

## Blockers

Some two-tap feature lengths remain proxy lengths inherited from preserved
reductions. Thermal reset status is conservative until wall-material and heat
path reset locations are mapped explicitly.

## Files Used

- `tools/analyze/build_litrev_reset_named_losses.py`
- `tools/analyze/test_litrev_reset_named_losses.py`
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_minor_loss_two_tap/minor_loss_two_tap.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/coefficient_naming_limits.csv`

## Validation

- `python3.11 tools/analyze/test_litrev_reset_named_losses.py`
- `python3.11 tools/analyze/build_litrev_reset_named_losses.py`

## Recommended Next Action

Use `named_pressure_loss_table.csv` as the pressure-loss export ledger and keep
component/cluster/branch-apparent names through any 1D closure handoff.

