# Observation Table Contract

Date: `2026-07-08`
Task: `TODO-OBSERVATION-TABLE-CONTRACT`
Role: Coordinator / Implementer / Writer
Owner: codex

## Context Read

Followed the repo startup protocol and read the root instructions, board,
ownership map, roles, and `tools/AGENTS.override.md`. Task-specific sources
read before coding:

- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/journal/2026-06-30/3d-to-1d-field-reduction-methods.md`
- `.agent/journal/2026-06-19/coordinator-writer-litrev-to-1d-modeling-handoff.md`
- `reports/2026-06/2026-06-18/2026-06-18_ethan_salt_closure_correlation_package/README.md`
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`
- `work_products/2026-07-08_cfd_scenario_contract/README.md`
- `.agent/status/2026-07-07_AGENT-193.md`
- `.agent/status/2026-07-07_AGENT-194.md`

## Work Completed

Built `tools/analyze/build_closure_observation_table.py` as the formal
contract builder and validator for the closure observation table. The builder is
read-only with respect to solver case trees and adapts existing artifacts into
one row per observable.

Generated `work_products/2026-07-08_closure_observation_table/`:

- `closure_observations.csv`
- `closure_observation_schema.csv`
- `excluded_sources.csv`
- `README.md`
- `summary.json`

Added `tools/analyze/test_closure_observation_table.py` with focused tests for
schema rejection, Salt 2/3/4-only admission, required metadata, separate
fit-vs-validation flags, recirculation fit exclusion, and heat-ledger
validation-only status.

## Observed Outputs

- `423` total observation rows.
- Source ids are exactly Salt 2/3/4 Jin:
  - `viscosity_screening_salt_test_2_jin_coarse_mesh`
  - `viscosity_screening_salt_test_3_jin_coarse_mesh`
  - `viscosity_screening_salt_test_4_jin_coarse_mesh`
- `45` rows are fit-eligible.
- `423` rows are validation-eligible.
- Families:
  - `342` pressure-family rows
  - `81` thermal-family rows

## Interpretation

The central contract now exists. Downstream pressure-ledger hardening,
patchwise heat-ledger hardening, and model-form bakeoff should consume
`closure_observations.csv` or emit rows conforming to
`closure_observation_schema.csv`.

Fit eligibility is intentionally narrower than validation eligibility.
Debuoyed pressure/momentum friction rows are fit targets only outside
recirculation-invalid spans. Apparent segment-friction rows remain diagnostics.
Patchwise heat-ledger rows remain validation diagnostics because the July 7 heat
ledger still lacks enthalpy-change terms. Time-window rows are validation
targets, not independent training rows, because samples from one relaxation path
are correlated.

## Exclusions And Caveats

Salt 1 is excluded pending its qualification decision. Corrected Salt Q rows are
excluded until a formal gate emits explicit requalification; the exclusions are
listed in `excluded_sources.csv`.

Several seeded rows carry
`frozen_extraction_window_older_than_available_case_latest`. This is preserved
as a quality flag rather than hidden, because the July 8 scenario-contract audit
showed later retained solver times exist than some older source-contract
windows.

## Validation

- `python3.11 tools/analyze/build_closure_observation_table.py`: passed with
  `validation_errors=0`.
- `python3.11 tools/analyze/build_closure_observation_table.py --validate-only`:
  passed with `validation_errors=0`.
- `python3.11 -m py_compile tools/analyze/build_closure_observation_table.py tools/analyze/test_closure_observation_table.py`:
  passed.
- `python -m pytest tools/analyze/test_closure_observation_table.py -q`:
  passed, `6 passed`.
- `python3.11 -m pytest tools/analyze/test_closure_observation_table.py -q`
  could not run because `pytest` is not installed for `/usr/bin/python3.11`.

## Handoff

Next recommended row is `TODO-PRESSURE-TERM-LEDGER`, reconciled against
AGENT-193/197 output but upgraded to emit station endpoints, total-pressure
proxy, dynamic head, density-gradient buoyancy, development/reset, minor-loss,
recirculation flags, and residual assignment in a fit-ready table conforming to
this observation contract.
