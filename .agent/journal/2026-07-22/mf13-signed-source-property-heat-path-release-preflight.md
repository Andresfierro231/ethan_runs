---
provenance:
  - tools/analyze/build_mf13_signed_source_property_heat_path_release_preflight.py
  - work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/summary.json
tags: [journal, mf13, source-property, heat-path]
related:
  - .agent/status/2026-07-22_TODO-MF13-SIGNED-SOURCE-PROPERTY-HEAT-PATH-RELEASE-PREFLIGHT-2026-07-22.md
  - imports/2026-07-22_mf13_signed_source_property_heat_path_release_preflight.json
task: TODO-MF13-SIGNED-SOURCE-PROPERTY-HEAT-PATH-RELEASE-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# MF13 Signed Source/Property Heat-Path Release Preflight

## Attempted

Implemented the first study in the MF12 next-study queue. The goal was not to
run Fluid or evaluate a model form. The goal was to ask whether signed
source/property inputs are admissible enough to support later MF12 formulas.

## Observed

MF08 provides four source-family rows. Heater/lower-leg, cooler/cooling-branch,
and test-section/upcomer have setup-known sign and magnitude metadata.
Passive/downcomer is explicitly marked as needing an independent source basis.

The thermal-accounting source/sink packet includes Salt1/Salt2 train rows and
Salt3/Salt4 protected metadata rows. MF13 copied those values into a
split-aware table, but all rows are marked `not_scored`.

Every source-family row has `runtime_allowed_now=false` and
`source_property_released_now=false`. Therefore release-ready rows equal zero.

## Inferred

The signed heat-path direction is scientifically useful for explaining why
MF12 is the right model-form family to pursue. It is not yet an executable
runtime correction. The heater, cooler, and test-section rows can support
hypothesis design; they cannot be consumed by a predictive formula until a
separate row releases source/property labels, `cp`/property basis, segment
mapping, and runtime legality.

Passive/downcomer should not be repaired by global multiplier. The missing
evidence is independent hA/source-family basis by segment, not another fit.

## Contradictions And Caveats

The thermal-accounting ledger has older evidence that some setup boundary
submodels are admitted for setup-boundary consumption. MF13 does not overturn
that; it only says those rows are still not released as MF12 source/property
formula inputs.

Protected rows are present as metadata because they are in the source evidence.
They were not used for scoring, fitting, model selection, or admission.

## Next Useful Actions

Proceed to `same_qoi_tp_projection_uq`. That study is now the first open queue
item because MF13 left source/property release closed and because TP projection
uncertainty is independently required before any predictive TP formula claim.

After that, run `runtime_wall_profile_basis_for_tp_projection`, then a separate
source/property label release candidate only if exact row-level fields can be
identified. The train-only MF12 formula smoke run remains blocked.

## Guardrails

No Fluid solve, scheduler action, native-output mutation, registry/admission
mutation, source/property release, Qwall release, protected scoring, fitting,
model selection, thesis edit, generated-index refresh, or residual absorption
into internal Nu occurred.
