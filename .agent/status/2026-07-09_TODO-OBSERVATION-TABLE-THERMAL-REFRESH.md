# TODO-OBSERVATION-TABLE-THERMAL-REFRESH Status

Date: `2026-07-09`
Role: Coordinator / Implementer / Tester / Writer

## Task

Refresh the canonical closure observation table so it consumes the July 9
physical-interface OpenFOAM thermal sampling package and carries bracketing
status, residual status, recirculation flags, and explicit no-`qr` radiation
semantics.

## Scope

Edited:

- `.agent/BOARD.md` own row
- `.agent/status/2026-07-09_TODO-OBSERVATION-TABLE-THERMAL-REFRESH.md`
- `.agent/journal/2026-07-09/observation-table-thermal-refresh.md`
- `imports/2026-07-09_closure_observation_table_thermal_refresh.json`
- `operational_notes/07-26/09/2026-07-09_codex_jobs_handoff.md`
- `tools/analyze/build_closure_observation_table.py`
- `tools/analyze/test_closure_observation_table.py`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/**`

Read-only:

- July 8 canonical closure observation table package
- July 8 patchwise heat ledger with physical-interface enthalpy rows
- July 9 physical-interface OpenFOAM sampling package from job `3287311`
- July 7 pressure, heat, and time-window ledgers
- Native solver outputs, scheduler state, and external model repositories

## Outputs

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observation_schema.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/excluded_sources.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/summary.json`

## Result

- Observation rows: `1032`
- Fit-eligible rows: `45`
- Validation-eligible rows: `1032`
- Families: `pressure=342`, `thermal=690`
- Source cases: admitted Salt 2/3/4 Jin mainline continuations only
- OpenFOAM interface sampling rows consumed: `414` observation rows from `48`
  sampled planes
- Physical-interface residual rows consumed: `195` observation rows from the
  July 8 enthalpy ledger
- Recirculation-flagged rows: `291`, all `not_fit_recirculation`
- Radiation-present rows: `0`; all thermal sampling rows retain
  `radiation_output_term=absent_no_qr_output`
- Validation errors: `0`

## Contract Changes

New schema fields are first-class columns:

- `physical_interface_bracket_status`
- `thermal_residual_status`
- `thermal_residual_assignment`
- `thermal_residual_fraction`
- `thermal_residual_W`
- `interface_temperature_source`
- `interface_temperature_selection_rule`
- `max_interface_recirc_ratio`
- `recirculation_flag`
- `radiation_output_term`
- `radiation_present`
- `control_volume`, `control_volume_group`, `interface_role`
- `dominant_flow_direction`, `backflow_fraction`

Fit gating is conservative: no row with `recirculation_flag=yes` may validate
as fit-eligible, and all such rows are explicitly marked
`not_fit_recirculation`. Physical-interface enthalpy residual rows and sampled
thermal interface rows are validation evidence only until a reviewed
control-volume method promotes a specific target.

## Validation

- `python3 -m pytest tools/analyze/test_closure_observation_table.py -q`
- `python3 tools/analyze/build_closure_observation_table.py`
- `python3 tools/analyze/build_closure_observation_table.py --validate-only`

All passed. The generated package reports `validation_passed=true`.

## Mutations Avoided

No native solver outputs, source OpenFOAM case dictionaries, July 8 source
packages, scheduler jobs, registry rows, or external model repositories were
modified.
