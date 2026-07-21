# TODO-OBSERVATION-TABLE-CONTRACT Status

Date: `2026-07-08`
Role: Coordinator / Implementer / Writer
Owner: codex

## Scope

Claimed the canonical closure observation table contract as the prerequisite for
pressure-ledger hardening, patchwise heat-ledger follow-up, and model-form
bakeoff. Work is limited to the paths assigned on `.agent/BOARD.md`.

## Startup Context Read

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `tools/AGENTS.override.md`
- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/status/2026-07-08_AGENT-202.md`
- `work_products/2026-07-08_cfd_scenario_contract/README.md`
- `.agent/status/2026-07-07_AGENT-193.md`
- `.agent/status/2026-07-07_AGENT-194.md`

## Completed

- Added `tools/analyze/build_closure_observation_table.py`.
- Added `tools/analyze/test_closure_observation_table.py`.
- Generated `work_products/2026-07-08_closure_observation_table/` with:
  - `closure_observations.csv`
  - `closure_observation_schema.csv`
  - `excluded_sources.csv`
  - `README.md`
  - `summary.json`
- Seed table contains `423` validated Salt 2/3/4 Jin rows:
  - `342` pressure-family rows
  - `81` thermal-family rows
  - `45` fit-eligible rows
  - `423` validation-eligible rows
- Salt 1 and corrected Salt Q rows are explicitly excluded in
  `excluded_sources.csv`.
- Patchwise heat-ledger rows are validation diagnostics only because
  enthalpy-change terms are still missing.
- Time-window rows are validation targets, not independent fit rows.

## Validation

- `python3.11 tools/analyze/build_closure_observation_table.py`: passed;
  `validation_errors=0`.
- `python3.11 tools/analyze/build_closure_observation_table.py --validate-only`:
  passed; `validation_errors=0`.
- `python3.11 -m py_compile tools/analyze/build_closure_observation_table.py tools/analyze/test_closure_observation_table.py`:
  passed.
- `python -m pytest tools/analyze/test_closure_observation_table.py -q`:
  passed, `6 passed`.
- `python3.11 -m pytest tools/analyze/test_closure_observation_table.py -q`:
  not available in this shell because `pytest` is not installed for
  `/usr/bin/python3.11`; the same tests passed with the default `python`.

## Status

COMPLETE.
