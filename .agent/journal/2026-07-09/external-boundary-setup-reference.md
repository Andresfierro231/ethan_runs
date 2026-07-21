# External Boundary Setup Reference

Date: `2026-07-09`
Task: `AGENT-236`
Role: Coordinator / Writer

## Prompt

The user asked whether the workspace already has thorough documentation for
what Ethan runs are doing for external boundary conditions and setup, and asked
for very thorough documentation plus a table summarizing findings for later
reference.

## Work Performed

Read the existing July 1 and July 8 setup/thermal packages and consolidated the
findings into:

- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/boundary_setup_summary.csv`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/source_index.csv`
- `reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/summary.json`

Also wrote manifest:

- `imports/2026-07-09_external_boundary_setup_reference.json`

No new OpenFOAM extraction, Fluid rerun, solver-output mutation, registry edit,
or scheduler action was performed.

## Main Findings

- Yes, the documentation is now thorough, but it was distributed across many
  packages rather than one durable reference.
- The admitted Salt CFD rows should be described as having a `1.4 in` layer
  present in the boundary stack, with surface-emissivity metadata but no
  exported `qr`/`G` radiation heat term.
- The CFD patchwise heat ledger separates heater, cooler, ambient wall,
  test-section, and junction roles. That role split is the correct language for
  setup documentation.
- CFD-informed comparison should use realized heater and cooler wallHeatFlux at
  the fluid interface. It should not use resistor/imposed heater duty or the
  current idealized 1D cooler capacity as CFD truth.
- The current defended 1D setup is a `1.0 in`, radiation-on,
  predictive-airside-HX surrogate, not a published global `1.4 in` matched
  setup.
- Fixed-mdot replays show the current 1D cooler/HX path is the largest thermal
  boundary mismatch: prescribing CFD cooler duty drops mean loop-temperature
  error from about `63.75 K` to about `4.46 K` across admitted Salt 2/3/4.

## Interpretation Boundary

This package is a documentation synthesis and reference table. It is not new
closure evidence, not a mesh/GCI package, and not a replacement for a future
physically matched 1D boundary reconstruction.

## Next Suggested Actions

1. Build or run a physically matched 1D scenario for the CFD `1.4 in` wall/layer
   contract.
2. Audit the exact `rcExternalTemperature` implementation to determine how
   emissivity is used.
3. Add first-class fixed-mdot/frozen-hydraulics replay support in Fluid.
4. Develop predictive heater-to-fluid and cooler-removal submodels so future
   agreement does not depend on importing CFD wallHeatFlux.
