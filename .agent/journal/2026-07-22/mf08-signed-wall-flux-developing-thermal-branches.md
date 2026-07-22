---
provenance:
  generated_by: tools/analyze/build_mf08_signed_wall_flux_developing_thermal_branches.py
  task_id: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
  generated_at_utc: 2026-07-22T14:05:57.924311+00:00
task: TODO-MF08-SIGNED-WALL-FLUX-DEVELOPING-THERMAL-BRANCHES-2026-07-22
tags:
  - journal
  - MF08
  - signed-wall-flux
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches
---

# MF08 signed wall-flux developing thermal branches

## Attempted

Built an evidence-only gate for four predeclared sign-aware thermal-development
variants: cooler negative wall flux, passive/downcomer negative cooling, heater
positive heating, and piecewise signed reset-memory.

## Observed

Setup-known source/sink rows provide consistent signs and rough magnitudes for
cooler, lower-leg heater, and test-section/upcomer heat. The runtime contract
and source/property gate still block source release. M2 blocks passive repair
execution. D2/D3/D4 support thermal-development/source-placement structure but
remain diagnostic-only.

## Inferred

The model-form axis is scientifically worth preserving, but not worth running
yet. The correct next state is `needs_source_basis`, not a train-smoke candidate
and not a wallHeatFlux fit.

## Contradictions or Caveats

The setup-known signs are not a predictive source model. MF08 does not decide
the magnitude or reset length scale, and it does not repair upcomer
recirculation. Those remain separate source-basis/MF07/MF09 problems.

## Next Useful Actions

Finish the reset/Graetz source basis, assemble independent passive/source-side
heat basis, and evaluate recirculating-upcomer alternatives before any
train-only smoke execution.
