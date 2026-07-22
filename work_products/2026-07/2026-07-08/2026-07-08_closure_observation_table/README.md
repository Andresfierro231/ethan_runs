# Closure Observation Table Contract

Generated: `2026-07-08T15:14:05`

## Scope

This package defines the canonical `closure_observations.csv` contract for the
current closure work. The seed rows are limited to admitted Salt 2/3/4 Jin
mainline continuations. Salt 1, Water, and corrected Salt Q perturbations are
excluded until their separate gates explicitly admit them.

## Contract

- One row is one observable, not a case summary.
- Units, mesh level, source path, source case root, time window, admission
  status, and fit/validation eligibility are mandatory.
- `fit_eligible` and `validation_eligible` are independent fields.
- Debuoyed momentum/pressure-ledger friction rows are fit targets only outside
  recirculation-invalid spans.
- Patchwise heat rows are validation diagnostics only until the heat ledger adds
  enthalpy-change terms and a patchwise residual assignment.
- Time-window rows are validation targets, not extra independent training
  samples, because samples from the same relaxation path are correlated.

## Outputs

- `closure_observations.csv`: canonical seed observation table.
- `closure_observation_schema.csv`: required columns, units, allowed values,
  and descriptions.
- `excluded_sources.csv`: explicit list of scenario/gate sources not admitted
  to the seed table.
- `summary.json`: counts, validation result, and source artifact list.

## Counts

- Total observation rows: `423`
- Fit-eligible rows: `45`
- Pressure/time-window/thermal families: `{'pressure': 342, 'thermal': 81}`
- Validation errors: `0`

## Source Artifacts

- `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv`
- `work_products/2026-06-30_claude_segment_friction/segment_friction.csv`
- `work_products/2026-06-30_claude_thermal_htc`
- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
- `work_products/2026-07-07_time_window_quasi_steady_uq/quasi_steady_observations.csv`
- `work_products/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv`
- `work_products/2026-07-08_cfd_scenario_contract/scenario_contract.csv`

## Downstream Order

Pressure-ledger hardening, patchwise heat-ledger hardening, and model-form
bakeoff should consume this table or emit rows conforming to this schema rather
than creating bespoke target-data CSVs.
