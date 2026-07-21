# Observation Table Thermal Refresh

Date: `2026-07-09`
Task: `TODO-OBSERVATION-TABLE-THERMAL-REFRESH`
Role: Coordinator / Implementer / Tester / Writer

## Prompt

The user asked for a thorough refresh of the canonical observation table so it
consumes the physical-interface thermal sampling package and carries bracketing
status, residual status, recirculation flags, and no-`qr` semantics. The user
also asked for clear documentation of the jobs completed so far.

## Work Performed

Updated `tools/analyze/build_closure_observation_table.py` to write the new
dated output package:

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/`

The builder now consumes:

- July 7 pressure term ledger
- July 7 heat source/sink ledger
- July 7 quasi-steady time-window observations
- July 8 scenario and source contracts
- July 8 patchwise heat ledger with physical-interface enthalpy residuals
- July 9 OpenFOAM physical-interface thermal samples from Slurm job `3287311`

Added schema columns for physical-interface bracket status, residual status,
residual assignment, residual magnitude/fraction, interface-temperature source
and selection rule, maximum recirculation/backflow metric, binary
recirculation flag, radiation output term, binary radiation-present flag,
control-volume labels, interface role, dominant flow direction, and backflow
fraction.

Updated `tools/analyze/test_closure_observation_table.py` so the test suite
proves:

- the generated table consumes the July 9 OpenFOAM sample CSV;
- heater, cooler/reducer, and junction sampled control-volume groups are
  present;
- signed mixing-cup and dominant-forward temperatures remain separate;
- residual rows remain validation-only;
- all recirculation-flagged rows are excluded from fit targets;
- all sampled thermal rows carry `absent_no_qr_output` and
  `radiation_present=no`.

## Result

Generated package:

- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/README.md`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observations.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/closure_observation_schema.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/excluded_sources.csv`
- `work_products/2026-07/2026-07-09/2026-07-09_closure_observation_table_thermal_refresh/summary.json`

Counts:

- `1032` total observation rows
- `342` pressure rows
- `690` thermal rows
- `45` fit-eligible rows, unchanged from the prior seed contract
- `1032` validation-eligible rows
- `414` rows from the July 9 OpenFOAM physical-interface sample CSV
- `195` rows from the July 8 physical-interface enthalpy ledger
- `291` rows with `recirculation_flag=yes`, all `not_fit_recirculation`
- `0` rows with `radiation_present=yes`

The OpenFOAM sample rows add row-level evidence for `48` physical planes:
heater interior brackets, cooler/reducer interior brackets, and junction
brackets for Salt 2/3/4. Those rows remain validation diagnostics, not fit
targets.

The enthalpy residual rows carry physical bracketing statuses including full
span, partial cooler bracket, high-recirculation composite diagnostic, and
not-bracketed junction rows. Those rows are also validation-only.

## Validation

Commands run:

- `python3 -m pytest tools/analyze/test_closure_observation_table.py -q`
- `python3 tools/analyze/build_closure_observation_table.py`
- `python3 tools/analyze/build_closure_observation_table.py --validate-only`

Results:

- Pytest: `9 passed`
- Direct generation: `closure_observation_rows=1032`,
  `validation_errors=0`
- Validate-only: `closure_observation_rows=1032`, `validation_errors=0`

## Interpretation Boundary

This refresh makes the canonical observation table able to score pressure,
mass-flow, thermal residual, exclusion, recirculation, bracketing, and
uncertainty-placeholder fields from one contract. It does not promote any new
thermal row into fit evidence. Any future thermal fit promotion still needs a
defensible control-volume method and mesh/uncertainty support.

No solver outputs or source case dictionaries were edited.
