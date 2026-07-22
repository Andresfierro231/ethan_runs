---
task: TODO-UPCOMER-EXCHANGE-THREE-CASE-CELL-VTK-MANIFEST-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, cell-vtk, manifest, no-scheduler]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt3_salt4_matrix
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold
---
# Upcomer Exchange Three-Case Cell VTK Manifest

This package publishes the three-case cell-lane manifest for the upcomer
exchange sampler. It joins the validated Salt2, Salt3, and Salt4 whole-mesh
`cell_vtk` artifacts into the reusable sampler manifest template.

## Decision

- cell VTK rows: `3`
- cell VTK pass rows: `3`
- sampler-ready rows: `0`
- remaining blocker rows: `12`
- scheduler action: `false`
- OpenFOAM launch: `false`
- exchange-cell harvest launched: `false`
- fit/score/admission allowed now: `false`

The cell lane is no longer the blocker for Salt2/Salt3/Salt4. The sampler is
still intentionally fail-closed because `exchange_interface_vtk`, `wall_vtk`,
normal vectors, `Q_wall_W`, and the source/sink heat-flow sign convention have
not been released. The static source/sink summary is recorded as context only;
it is not a complete heat-loss ledger.

## Outputs

- `three_case_cell_vtk_manifest.csv`: validated cell VTK paths and provenance.
- `case_vtk_input_manifest.cells_populated.csv`: sampler template with only the
  cell paths populated.
- `three_case_cell_vtk_validation_join.csv`: cell release versus sampler gate.
- `source_sink_wall_loss_readiness.csv`: source/sink context and `Q_wall_W`
  blocker.
- `remaining_sampler_blockers.csv`: non-cell blockers that still prevent
  sampler harvest.
- `no_mutation_guardrails.csv`, `source_manifest.csv`, and `summary.json`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, fit,
score, model selection, exchange-cell admission, Phase 4B rescore, Phase 5/S6
trigger, or internal-Nu residual absorption is changed by this package.
