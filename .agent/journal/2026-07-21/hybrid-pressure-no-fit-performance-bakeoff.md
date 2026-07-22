---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff/README.md
tags: [journal, pressure-ledger, hybrid-pressure, no-fit]
related:
  - .agent/status/2026-07-21_TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21.md
  - imports/2026-07-21_hybrid_pressure_no_fit_performance_bakeoff.json
task: TODO-HYBRID-PRESSURE-NO-FIT-PERFORMANCE-BAKEOFF-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Tester/Writer
type: journal
status: complete
---
# Hybrid Pressure No-Fit Performance Bakeoff

## Attempted

Built a reproducible no-fit bakeoff package from existing pressure-corner and
F3/F6 artifacts. The task did not read or mutate native solver output and did
not run any scheduler, solver, sampler, or Fluid command.

## Observed

The existing two-tap section-effective scorecard contains three train-context
rows and three score levels per row. Observed and oracle rows are exact by
construction. The Salt2-frozen diagnostic transfer gives a max Salt3/Salt4
error of `0.47046606946166093438399 Pa`. The available F3/Shah apparent
artifacts all mark numeric comparison unavailable because no ordinary
admissible F6 candidate exists.

## Inferred

The hybrid pressure residual is useful for thesis explanation and residual
ownership, but it is not yet a candidate for freeze/admission. The absence of a
numeric F3/Shah comparison is not a missing calculation in this row; it is an
admission gate result inherited from the F6 packages.

## Contradictions Or Caveats

The no-fit transfer error is small, but the row is still diagnostic. Treating
the Salt2-frozen coefficient as predictive would skip the same-QOI UQ,
ordinary-flow, and component-isolation blockers.

## Next Useful Actions

Use the package as thesis evidence and as a baseline for a later bakeoff only
after an ordinary admissible F6 row or a source-resolved section-effective
candidate passes the required gates.
