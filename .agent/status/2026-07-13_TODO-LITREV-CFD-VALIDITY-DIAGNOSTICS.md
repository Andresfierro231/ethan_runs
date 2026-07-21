# TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS Status

Date: `2026-07-13`

Role: `Implementer / Tester / Writer`

## Observed Facts

- Built `work_products/2026-07/2026-07-13/2026-07-13_litrev_cfd_validity_diagnostics/`.
- Primary outputs:
  - `cfd_single_stream_validity.csv`: 18 pressure-section validity rows.
  - `coefficient_naming_limits.csv`: 54 coefficient naming rows.
- Existing artifact proxies were used for reverse/backflow/recirculation where
  available; secondary velocity remains a future vector-plane extraction need.

## Inferred Interpretation

Sections with material recirculation or reverse-flow proxies should be named
`section_effective` or diagnostic, not as transferable universal `f_D`, `K`, or
`Nu`.

## Blockers

Exact reverse-flow area fraction, reverse mass fraction, and secondary velocity
fraction are not available in all existing artifacts. Those require bounded
compute-node plane-vector extraction if needed later.

## Files Used

- `tools/analyze/build_litrev_cfd_validity_diagnostics.py`
- `tools/analyze/test_litrev_cfd_validity_diagnostics.py`
- `work_products/2026-07/2026-07-08/2026-07-08_pressure_term_ledger/pressure_term_ledger.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv`

## Validation

- `python3.11 tools/analyze/test_litrev_cfd_validity_diagnostics.py`
- `python3.11 tools/analyze/build_litrev_cfd_validity_diagnostics.py`

## Recommended Next Action

Consume `coefficient_naming_limits.csv` in named-loss and closure-export steps;
reject universal coefficient names where the validity gate is section-effective
or diagnostic only.

