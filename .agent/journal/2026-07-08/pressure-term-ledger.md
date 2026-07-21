# Pressure Term Ledger

Date: `2026-07-08`
Task: `TODO-PRESSURE-TERM-LEDGER`
Role: Implementer / Tester / Writer
Owner: codex

## Context Read

Followed the repo startup protocol and claimed the row only after completing
`TODO-OBSERVATION-TABLE-CONTRACT`. Task-specific sources read:

- `operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`
- `.agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md`
- `.agent/journal/2026-07-01/T1-mesh-centerlines-geometry-refix.md`
- `.agent/journal/2026-07-01/3d-closure-into-1d-predictivity-trial.md`
- `reports/2026-07/2026-07-01/2026-07-01_postprocessing_rom_honesty_audit/README.md`
- `.agent/status/2026-07-07_AGENT-193.md`
- `.agent/status/2026-07-07_AGENT-197.md`

## Work Completed

Reconciled the existing AGENT-193/197 pressure ledger with the stricter
observation-contract requirements. The July 7 package remains historical; the
new fit-ready package is:

`work_products/2026-07-08_pressure_term_ledger/`

Generated files:

- `pressure_term_ledger.csv`
- `pressure_term_ledger.json`
- `summary.json`
- `README.md`

Code/tests updated:

- `tools/analyze/build_pressure_term_ledger.py`
- `tools/analyze/test_pressure_term_ledger.py`

## Ledger Additions

New columns include:

- source root, source window, mesh level, and observation schema path
- station start/end labels and non-fitting station count
- endpoint `p_rgh`, density, bulk velocity, dynamic head, and total-pressure
  proxy
- flow-direction-projected `dp_rgh`, density-gradient buoyancy, and inertial
  terms
- distributed mechanical-loss gradient
- development/reset flag, minor-loss upper-bound flag, recirculation flag,
  residual assignment, and no-buoyancy-double-counting policy
- fit/validation eligibility and fit-use status

## Observed Results

- `18` rows: Salt 2/3/4 Jin × six spans.
- `12` rows fit-eligible.
- `6` recirculation rows excluded from fitting.
- `max_abs_residual_fraction_main_legs = 0.0` in the regenerated summary.
- `max_f_debuoyed_round_trip_error = 0.0` versus July 1 `f_corrected`.

## Interpretation

The pressure ledger is now a fit-ready span table, but the residual definition
is intentionally the AGENT-193 momentum-budget identity:

```text
residual = -sigma * distributed - gross - buoyancy
```

Development and minor-loss columns are diagnostic decomposition terms for why
the CFD distributed mechanical loss differs from simpler 1D assumptions. They
are not subtracted a second time from the budget residual, because that would
double count losses already embedded in `distributed_friction_pa`.

The no-double-counting guard is explicit: density-gradient buoyancy is reported
in `gh_drho_dxi_pa_m` and `buoyancy_contribution_pa`, while fit friction uses
`distributed_mechanical_loss_pa_m` / `f_debuoyed`.

## Validation

- `python tools/analyze/build_pressure_term_ledger.py`: passed.
- `python -m pytest tools/analyze/test_pressure_term_ledger.py -q`: passed,
  `14 passed`.
- `python3.11 -m py_compile tools/analyze/build_pressure_term_ledger.py tools/analyze/test_pressure_term_ledger.py`:
  passed.
- `python3.11 tools/analyze/build_pressure_term_ledger.py` failed in this shell
  because importing the external Fluid package requires `yaml`, which is not
  installed for `/usr/bin/python3.11`. The default `python` has the needed
  dependencies and was used for runtime validation.

## Handoff

`TODO-PATCHWISE-HEAT-LEDGER` should follow next. It should mirror this pressure
ledger pattern: patch/source provenance, sign convention, source windows,
enthalpy-change terms, wallHeatFlux integral, residual assignment, and
fit-vs-validation eligibility in one table.
