# TODO-PRED-HYDRAULIC-GATE Status

Status: COMPLETE 2026-07-13

Role: Implementer / Reviewer

Implemented `tools/analyze/build_predictive_hydraulic_gate.py` and focused tests.
Generated package:

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/`

Outputs:

- `hydraulic_fit_safety_gate.csv`
- `forward_v0_hydraulic_residuals.csv`
- `hydraulic_gate_decisions.csv`
- `summary.json`
- `README.md`

Validation:

- `python3 tools/analyze/test_predictive_hydraulic_gate.py` passed.
- `python3 -m py_compile tools/analyze/build_predictive_hydraulic_gate.py tools/analyze/test_predictive_hydraulic_gate.py` passed.
- `python3 tools/analyze/build_predictive_hydraulic_gate.py` completed from AGENT-262, AGENT-284, and TODO-PRED-FORWARD-V0 package outputs.

Observed result:

- Raw pressure-gradient fit-safe rows: `left_lower_leg`, `left_upper_leg`.
- Momentum-corrected diagnostic fit-safe rows: `left_lower_leg`, `left_upper_leg`, `lower_leg`, `right_leg`, `test_section_span`, `upper_leg`.
- Forward-v0 mdot overprediction vs CFD: `F0_current_fluid_sources` mean `+0.008082 kg/s` (`+53.96%`); `F1_heater_only` mean `+0.005478 kg/s` (`+36.37%`).
- Every Salt forward-v0 row overpredicts mdot despite small fast-scan pressure residuals.

Interpretation:

Pressure/friction evidence supports a separate hydraulic tuning lane for friction, minor-loss, and profile terms before thermal fitting. Training must remain restricted to fit-safe rows; pressure-recovery/noise rows are diagnostic only. Thermal closure remains blocked, and this task admits no thermal UA/HTC/Nu claim.
