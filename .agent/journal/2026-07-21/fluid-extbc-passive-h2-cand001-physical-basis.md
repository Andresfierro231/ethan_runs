---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/repair_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/source_sink_interaction_update.csv
tags: [journal, forward-model, passive-boundary, physical-basis]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21.md
  - imports/2026-07-21_fluid_extbc_passive_h2_cand001_physical_basis.json
  - work_products/2026-07/2026-07-21/2026-07-21_passive_h2_cand001_physical_basis/README.md
task: TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: journal
status: complete
---
# PASSIVE-H2-CAND001 Physical Basis

## Attempted

Built a no-solve physical-basis package for the predeclared
`PASSIVE-H2-CAND001 passive_hA_source_basis_rebuild_v1` candidate. The package
uses Phase E role rows, Phase H2 family attribution, Phase H2 heat/ambient
ledgers, and the completed setup-known heater source packages.

## Observed

The strict gate is `needs_more_source`.

All five passive families have current h values inside broad independent
engineering screens:

- `junction`: current h `9.621920204 W/m2-K`, screen `2-12`.
- `downcomer`: current h `3.42388628 W/m2-K`, screen `2-10`.
- `upcomer`: current h `3.703887805 W/m2-K`, screen `2-10`.
- `cooling_branch`: current h `4.045201782 W/m2-K`, screen `2-12`.
- `lower_leg`: current h `3.945999179 W/m2-K`, screen `2-12`.

Fixed-state q estimates also sit inside the broad q-loss envelopes for every
family. The screens therefore do not provide an independent contradiction of
the current passive basis.

The source/sink follow-on packages are now complete. The lower-leg heater
contract has three train-only spans totaling `265.7 W`, but the residual
decomposition is mixed: TW4 and TW5 worsen while TW6 improves. This keeps source
physics relevant but does not authorize a passive hA repair.

## Inferred

The Phase H global passive hA response remains scientifically important, but
the current physical-basis evidence cannot convert it into a repair. The
correct next work is source release: trace geometry/area/coverage, ambient and
surroundings temperatures, insulation/exposure, room airflow, and correlation
inputs. A train-only repair solve would be premature until that release exists.

## Contradictions Or Caveats

The engineering screens cite Churchill-Chu-style natural-convection logic only
as a broad plausibility envelope. They are not a complete literature extraction
or source-property release because characteristic length, orientation, room
airflow, and insulation exposure are not yet source-backed.

## Next Useful Actions

1. Claim a narrow ambient/geometry/insulation source-release row for passive
   external surfaces.
2. If that row yields a family-specific hA envelope outside current values,
   claim exactly one train-only repair-run row.
3. Keep `global_passive_hA_scale_0.5` forbidden as a fitted repair.
4. Continue keeping validation, holdout, and external-test scoring blocked
   until a frozen runtime-legal candidate exists.
