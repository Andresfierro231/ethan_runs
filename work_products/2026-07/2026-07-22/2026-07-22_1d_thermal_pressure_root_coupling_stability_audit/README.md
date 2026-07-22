# 1D Thermal/Pressure Root Coupling Stability Audit

Decision: `root_coupling_stability_audit_ready_dry_no_compute`.

This is a dry audit. It does not execute Fluid, run a solver, fit parameters,
score protected rows, or release source/property inputs.

## Main Findings

- The highest coupled-root risk families are cooler/HX strength, fluid property
  mode, pressure-loss terms, heater/source fraction, external convection, and
  sensor projection.
- Pressure/F6 terms remain blocked by ordinary-flow and same-QOI UQ gates.
- The next implementation step is train-only smoke testing: finite brackets,
  finite roots, finite TP/TW projections, and runtime-legality checks.
