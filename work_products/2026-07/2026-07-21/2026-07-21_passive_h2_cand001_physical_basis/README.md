---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_source_sink_runtime_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_setup_known_heater_source_train_residual_decomp/README.md
tags: [forward-model, passive-boundary, physical-basis, no-solve]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-passive-h2-cand001-physical-basis.md
  - imports/2026-07-21_fluid_extbc_passive_h2_cand001_physical_basis.json
task: TODO-FLUID-EXTBC-PASSIVE-H2-CAND001-PHYSICAL-BASIS-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# PASSIVE-H2-CAND001 Physical Basis Package

## Why This Exists

Phase H2 showed broad passive-network sensitivity but blocked admission because
the current passive hA basis traces through `wallHeatFlux`. This package asks
whether independent setup/geometry/engineering evidence justifies one
train-only passive repair run.

## Open First

- `repair_gate.csv`
- `current_hA_basis_and_provenance_risk.csv`
- `independent_h_estimate_range.csv`
- `expected_q_loss_envelope.csv`
- `source_sink_interaction_update.csv`

## Result

Gate decision: `needs_more_source`.

All current passive family h values and fixed-state q estimates sit inside the
broad engineering screens used here, but every current passive family still has
wallHeatFlux-derived provenance and the ambient/geometry/insulation basis is
not source-released. Therefore no train-only repair run is justified by this
row.

## Output Contract

- `current_hA_basis_and_provenance_risk.csv`
- `independent_h_estimate_range.csv`
- `area_coverage_basis.csv`
- `ambient_surroundings_basis.csv`
- `expected_q_loss_envelope.csv`
- `source_sink_interaction_update.csv`
- `repair_gate.csv`
- `source_manifest.csv`
- `summary.json`

## Do Not Do

Do not run Fluid from this package. Do not use `global_passive_hA_scale_0.5` as
a fitted repair. Do not score validation, holdout, or external-test rows. Do
not mutate native CFD/OpenFOAM outputs, registry/admission state, Fluid source,
blocker register, generated indexes, or thesis files.
