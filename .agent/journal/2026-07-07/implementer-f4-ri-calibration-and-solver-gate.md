# AGENT-191 F4 Ri Calibration And Solver Gate

Date: `2026-07-07`  
Role: Coordinator / Implementer / Reviewer / Writer

## Objective

Freeze mainline Salt 2/3/4 Jin evidence, build the read-only F4/Ri calibration
and audit package, keep corrected Salt/Salt 1 flagged rows out of closure
fitting, and harden Fluid F4 solver routing after the read-only gate.

## Raw Observations

- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`
  contains 18 admitted rows: Salt 2/3/4 Jin × six spans.
- The corrected Salt gate snapshot records job `3279646` as pending on
  `afterany:3275448(unfulfilled),afterany:3275449(unfulfilled),afterany:3275560(unfulfilled)`.
- `salt1_jin_hi10q_corrected` is held with the explicit early-ended note:
  254 s past restart, 4.24% of target extension.
- `salt3_jin_hi5q_corrected` and `salt3_jin_hi10q_corrected` are held as
  canceled/investigate rows from job `3275450`, with fatal/error markers.
- `salt1_jin_lo10q_corrected` is held because Salt 1 lacks the nominal mdot
  reference needed for the same corrected-Q gate logic as Salt 2/3/4.
- The bounded residual F4 candidate uses median section Ri and streamwise Ri
  from the July 1 all-span convection artifacts. Several physical groups have
  negative R2 under the one-parameter screen.

## Interpretation

- The admitted evidence set is now frozen correctly for closure fitting:
  mainline Salt 2/3/4 Jin only.
- Corrected Salt Q rows are useful monitor evidence, but none are admissible for
  closure fitting in this package.
- Salt 1 should remain quarantined from coefficient fitting until a dedicated
  qualification package resolves nominal mdot reference and short-window issues.
- The Ri candidate is a diagnostic screen, not a publishable or ROM-ready F4
  correlation.
- The Fluid hardening is appropriate because it prevents accidental upcomer
  defaults when `F4_leg_class` is selected.

## Outputs

- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py`
- `tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/**`
- External Fluid updates to `friction_closures.py`, `solver.py`, and
  `tests/test_friction_closures.py`

## Validation

- `python3.11 tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py`:
  3 tests passed.
- `python3.11 -m py_compile ...`: passed.
- `pytest tests/test_friction_closures.py` in external Fluid: 45 tests passed.
- Python 3.9 solver-routing smoke: passed for heater, cooler, downcomer, and
  upcomer parent-segment mapping.
- `python3.11 -m pytest` was unavailable; that interpreter lacks `pytest`.
- `python3.11` Fluid package import was blocked by missing `yaml`; Python 3.9
  pytest/import checks covered the Fluid test path.

## Blockers

- Corrected Salt operating-point gate `3279646` has not run because its
  dependencies are still unfulfilled.
- Salt 1 qualification remains unresolved.
- More admissible operating points are needed before claiming a portable
  Ri-based F4 law.

## Exact Next Action

Coordinator review should hold the current F4/Ri candidate as diagnostic-only
and wait for corrected Salt gate `3279646` before any corrected-Q closure
admission decision.
