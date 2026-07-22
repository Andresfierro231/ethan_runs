---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation/corrected_outer_surface_passive_operator_family.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_runtime_operator_smoke_uq_gate/summary.json
tags: [thermal, passive-h2, radiation, runtime-basis, journal]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation/README.md
  - .agent/status/2026-07-22_TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22.md
  - imports/2026-07-22_thermal_passive_h2_radiation_runtime_basis_reconciliation.json
task: TODO-THERMAL-PASSIVE-H2-RADIATION-RUNTIME-BASIS-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Uncertainty / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# PASSIVE-H2 Radiation Runtime-Basis Reconciliation

## Attempted

Rebuilt the PASSIVE-H2 diagnostic operator around the user-raised concern that
the prior radiation calculation may have used fluid/pipe/wall state rather than
outer insulation temperature. The work consumed only existing setup-UQ and
source-basis packets.

## Observed

The prior direct operator reported `656.493
W` of nominal radiation. Recomputing radiation from the same inner wall-state
sensor projection reproduces that order of magnitude. When the source-backed
layer stack is inserted between the inner model state and the environment, the
nominal outer-surface radiation becomes
`22.215 W` and the total corrected
passive operator is `38.557 W`.

The existing train-only `radiation_on` setup-UQ variant remains identical to
nominal in the model outputs, so the model switch itself is not admitted.

## Inferred

The large radiation term is best explained as a runtime-basis error in the
diagnostic operator: radiation was evaluated at the hot inner wall/pipe-state
basis. The physically relevant emitting surface for insulated passive loss is
the outer insulation surface after conduction through source-backed layers.

## Caveats

This is still a diagnostic train-only gate. It does not release source/property
rows, numeric q-loss, Qwall, coefficients, or protected scores. It also does
not prove the Fluid `radiation_on` switch is wired for H2; it shows how a
separately tested corrected operator should be constructed.

## Next Useful Actions

Use this package to fail-close any claim that H2 has a released `656 W`
radiation correction. A future source/property release gate should require a
runtime-executable radiation implementation whose emitting-surface state is
source-backed and whose train-only same-QOI movement is nonzero and audited.
