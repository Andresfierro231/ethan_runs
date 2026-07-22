---
task: TODO-UPCOMER-EXCHANGE-GEOMETRY-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, geometry-release, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold
---
# Upcomer Exchange Geometry Release

This package implements the geometry-release phase for the upcomer exchange
blocker sequence. It releases only the whole-mesh `cell_vtk` policy and keeps
the exchange-interface and wall/core lanes blocked until a trusted geometry
source exists.

## Decision

- case windows: `3`
- released cell VTK rows: `3/3`
- facezone audit rows: `15`
- released exchange-interface rows: `0`
- wall/core audit rows: `18`
- released wall/core rows: `0`
- scheduler action: `false`
- OpenFOAM launch: `false`
- fit/score/admission allowed now: `false`

The next executable compute row should generate whole-mesh cell VTKs only.
Interface and wall/core generation remain blocked because loop mass-flow planes
and the representative upcomer outlet proxy do not define a conservative
main/recirculation exchange interface.

## Outputs

- `geometry_release_decision.csv`: lane-level release or blocker decision.
- `cell_vtk_contract.csv`: whole-mesh cell VTK extraction contract.
- `facezone_candidate_audit.csv`: rejected faceZone/proxy interface candidates.
- `wall_core_candidate_audit.csv`: wall span audit and blocker rationale.
- `planned_extraction_commands.csv`: next scheduler-row command contract.
- `no_mutation_guardrails.csv`, `next_agent_handoff.csv`, `source_manifest.csv`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, fit,
score, model selection, exchange-cell admission, Phase 4B rescore, Phase 5/S6
trigger, or internal-Nu residual absorption is changed by this package.
