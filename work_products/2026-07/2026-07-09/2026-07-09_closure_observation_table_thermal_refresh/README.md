# Closure Observation Table Contract

Generated: `2026-07-09T17:26:16`

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
- Patchwise heat rows from the older heat ledger remain validation diagnostics;
  physical-interface enthalpy residual rows are carried as validation-only
  thermal evidence with bracketing status and residual assignment explicit.
- OpenFOAM physical-interface sample rows preserve signed mixing-cup
  temperatures, forward-flow temperatures, directional flux proxies, and
  backflow fractions separately. Rows flagged by recirculation/backflow are not
  fit targets.
- Radiation is not inferred from wall emissivity metadata. `radiation_present`
  is `yes` only if OpenFOAM outputs/samples a radiation term; current thermal
  rows carry `absent_no_qr_output`.
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

- Total observation rows: `1032`
- Fit-eligible rows: `45`
- Pressure/time-window/thermal families: `{'pressure': 342, 'thermal': 690}`
- Validation errors: `0`

## Source Artifacts

- `work_products/2026-07/2026-07-07/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-01/2026-07-01_claude_momentum_budget/momentum_budget.csv`
- `work_products/2026-06/2026-06-30/2026-06-30_claude_segment_friction/segment_friction.csv`
- `work_products/2026-06/2026-06-30/2026-06-30_claude_thermal_htc`
- `work_products/2026-07/2026-07-07/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/patchwise_heat_ledger_enthalpy_interfaces.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/segment_enthalpy_residuals.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/combined_openfoam_interface_samples.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_thermal_openfoam_interface_sampling/sampling_plane_plan.csv`
- `work_products/2026-07/2026-07-07/2026-07-07_time_window_quasi_steady_uq/quasi_steady_observations.csv`
- `work_products/2026-06/2026-06-29/2026-06-29_ethan_reduction_contract_audit/source_contract_map.csv`
- `work_products/2026-07/2026-07-08/2026-07-08_cfd_scenario_contract/scenario_contract.csv`

## Downstream Order

Pressure-ledger hardening, patchwise heat-ledger hardening, and model-form
bakeoff should consume this table or emit rows conforming to this schema rather
than creating bespoke target-data CSVs.
