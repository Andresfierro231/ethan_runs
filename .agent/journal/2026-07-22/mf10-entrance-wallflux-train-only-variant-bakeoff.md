---
provenance:
  generated_by: tools/analyze/build_mf10_entrance_wallflux_train_only_variant_bakeoff.py
  task_id: TODO-MF10-ENTRANCE-WALLFLUX-TRAIN-ONLY-VARIANT-BAKEOFF-2026-07-22
  generated_at_utc: 2026-07-22T14:05:57.992942+00:00
task: TODO-MF10-ENTRANCE-WALLFLUX-TRAIN-ONLY-VARIANT-BAKEOFF-2026-07-22
tags: [journal, MF10, train-only-bakeoff]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff
---
# MF10 entrance/wall-flux train-only variant bakeoff

## Attempted

Built the MF10 dry bakeoff gate from completed MF07/MF08/MF09 evidence and the
master scoreboard numeric context.

## Observed

MF07 is diagnostic-only, MF08 needs source basis, MF09 is blocked by missing
mesh/GCI/source basis, and the source-property preflight has 0 release-ready
rows. Existing M2/M3 scoreboard metrics can be carried as context, but new
development/exchange-cell variants are not executable.

## Inferred

MF10 should not run a hidden train/support score. The rigorous next step is to
release source/property/cp and candidate disable/default behavior before any
train-only Fluid smoke.

## Contradictions or Caveats

Existing scoreboard metrics are legacy numeric context, not a new locked-split
score. They are useful for residual-owner direction, not for selecting a new
coefficient.

## Next Useful Actions

Claim a source-property/cp release row for the entrance/wall-flux/exchange-cell
candidate family, then claim a separate bounded train-only Fluid smoke row only
if at least one variant becomes executable.
