---
provenance:
  - tools/analyze/build_1d_thermal_pressure_root_coupling_stability_audit.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit/summary.json
task: TODO-1D-THERMAL-PRESSURE-ROOT-COUPLING-STABILITY-AUDIT-2026-07-22
date: 2026-07-22
role: Forward-pred / Hydraulics / Thermal-modeling / Tester / Writer
type: journal
status: complete
tags: [journal, root-solve, pressure, thermal, stability]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit
---

# Thermal/pressure root-coupling stability audit

## Attempted

Claimed the dry stability-audit row and consumed setup-only UQ sensitivity,
MF02 pressure/mdot coupling diagnostics, F3/F6 prerequisites, pressure-basis
evidence, and the model hierarchy packet. Built a reproducible audit and tests.

## Observed

The setup-only sensitivity table flags cooler/HX strength, fluid property mode,
and pressure-loss terms as high mdot pathways. Heater/source fraction, external
heat-loss terms, and sensor projection remain important for TP/TW behavior. The
MF02 diagnostic warns that local apparent K values in recirculating sections are
not admissible ordinary mdot sensitivity.

## Inferred

The next Fluid implementation should be protected by train-only smoke tests:
finite mdot pressure brackets, finite thermal states, finite TP/TW projections,
runtime-legality checks, and F6/component-K disable checks. A dry audit is
enough to define those tests; it is not evidence of a stable scored candidate.

## Contradictions or Caveats

This packet does not execute a numerical root solve. It only defines expected
monotonicity, failure modes, and smoke-test criteria from existing evidence.

## Next Useful Actions

Claim a train-only root-smoke row before running Fluid. Keep validation,
holdout, external-test, source/property release, and candidate freeze locked
until train-only finite-root evidence and attribution exist.
