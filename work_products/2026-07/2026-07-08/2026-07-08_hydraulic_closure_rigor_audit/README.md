# Hydraulic Closure Rigor Audit

Generated: `2026-07-08T18:16:04`
Task: `AGENT-223`

## Scope

This package integrates existing Salt 2/3/4 Jin hydraulic evidence into one
audit. It does not modify the July 8 pressure ledger, minor-loss ledger,
observation table, native solver outputs, or external Fluid code.

## Outputs

- `independent_total_pressure_ledger.csv`
- `minor_loss_two_tap_refined.csv`
- `station_development_analysis.csv`
- `recirculation_invalidity.csv`
- `hydraulic_uncertainty_budget.csv`
- `loop_closure_audit.csv`
- `closure_decision_matrix.csv`
- `source_inventory.csv`
- `summary.json`

## Key Findings

- Rows audited: `18` pressure-span rows and
  `15` minor-loss feature rows.
- The total-pressure ledger uses `p_rgh + 0.5*rho*U_bulk^2` as a proxy, not a
  full local total pressure.
- Minor-loss values remain upper-bound / sensitivity inputs until full raw
  centerline tap-to-tap extraction is available.
- Upcomer recirculation spans remain diagnostic-only for single-stream closure
  fitting.
- Mesh/GCI uncertainty is not quantified in the available admitted evidence and
  is carried as an explicit blocker.

## Reproduce

```bash
python tools/analyze/build_hydraulic_closure_rigor_audit.py
python -m pytest tools/analyze/test_hydraulic_closure_rigor_audit.py -q
```
