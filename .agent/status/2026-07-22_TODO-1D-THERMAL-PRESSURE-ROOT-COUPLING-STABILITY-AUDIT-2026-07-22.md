---
provenance:
  - tools/analyze/build_1d_thermal_pressure_root_coupling_stability_audit.py
  - tools/analyze/test_1d_thermal_pressure_root_coupling_stability_audit.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit/summary.json
task: TODO-1D-THERMAL-PRESSURE-ROOT-COUPLING-STABILITY-AUDIT-2026-07-22
date: 2026-07-22
role: Forward-pred / Hydraulics / Thermal-modeling / Tester / Writer
type: status
status: complete
tags: [status, root-solve, pressure, thermal, stability, dry-audit]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_thermal_pressure_root_coupling_stability_audit
---

# TODO-1D-THERMAL-PRESSURE-ROOT-COUPLING-STABILITY-AUDIT-2026-07-22

## Objective

Audit whether the current 1D coupled pressure/thermal root-solve path is
numerically and physically stable under setup-only perturbations, without
launching Fluid or scoring protected rows.

## Outcome

Decision: `root_coupling_stability_audit_ready_dry_no_compute`.

Published `4` root monotonicity/bracketing rows, `9` coupled sensitivity rows,
`5` high coupled-root risk rows, `5` failure modes, and `5` recommended Fluid
smoke tests. The high-risk pathways are cooler/HX strength, fluid property
mode, pressure-loss terms, heater/source fraction, and sensor projection /
thermal pathways that can feed TP/TW residuals.

The audit keeps F6/component-K disabled until ordinary-flow and same-QOI UQ
prerequisites are met. It recommends train-only smoke tests for finite pressure
brackets, finite roots, finite projected TP/TW, runtime legality, and F6 disable
enforcement.

## Changes Made

- Added `tools/analyze/build_1d_thermal_pressure_root_coupling_stability_audit.py`.
- Added `tools/analyze/test_1d_thermal_pressure_root_coupling_stability_audit.py`.
- Wrote `root_monotonicity_bracketing_audit.csv`.
- Wrote `coupled_sensitivity_risk_matrix.csv`.
- Wrote `root_failure_mode_table.csv`.
- Wrote `fluid_smoke_test_recommendations.csv`.
- Wrote `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`,
  and README.

## Validation

- `python3.11 tools/analyze/build_1d_thermal_pressure_root_coupling_stability_audit.py`:
  passed; decision `root_coupling_stability_audit_ready_dry_no_compute`.
- `python3.11 -m pytest tools/analyze/test_1d_thermal_pressure_root_coupling_stability_audit.py`:
  passed, `3` tests.

## Guardrails

- Native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid
  and external repos: not mutated.
- No solver, Fluid, sampler, harvester, or UQ launch.
- No fit, model selection, protected scoring, source/property release, or
  candidate freeze.
