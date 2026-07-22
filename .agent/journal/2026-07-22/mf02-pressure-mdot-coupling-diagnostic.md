---
provenance:
  generated_by: tools/analyze/build_mf02_pressure_mdot_coupling_diagnostic.py
  task_id: TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22
  generated_at_utc: 2026-07-22T13:28:51.811248+00:00
task: TODO-MF02-PRESSURE-MDOT-COUPLING-DIAGNOSTIC-2026-07-22
tags:
  - journal
  - MF02
  - pressure-mdot
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf02_pressure_mdot_coupling_diagnostic
---

# MF02 pressure-mdot coupling diagnostic

## Attempted

Built a read-only diagnostic package from the section-effective lower-right
pressure scorecard, hybrid no-fit bakeoff, F6 admission gates, and CAND001
retry/UQ gate.

## Observed

The lower-right rows have finite pressure residuals, but they also fail
component isolation, same-QOI UQ, and ordinary recirculation gates. Their
gross-scale residuals are small relative to hydrostatic pressure rise, while
local dynamic-pressure normalization produces large nonordinary apparent
`K_eff` values.

## Inferred

The pressure residual can be discussed as a possible mdot coupling scale, but
only as a diagnostic. It does not justify changing a 1D pressure closure, fitting
F6, clipping K, or applying a hidden global multiplier.

## Contradictions or Caveats

The gross-scale mdot estimate assumes a quadratic balance only to estimate order
of magnitude. It is not a validated loop sensitivity, and the sign convention is
not a component-loss sign convention.

## Next Useful Actions

Keep pressure work separated: wait for CAND001 terminal evidence or another
ordinary-flow source family before any endpoint/F3/F6 review. Use this MF02
package as a thesis-safe diagnostic of how small the section-effective residual
is against gross hydrostatic pressure.
