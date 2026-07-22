---
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-PARSER-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, cell-volume, parser]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/README.md
---
# Upcomer Exchange Cell-Volume Parser

This package implements the missing cell-volume path that blocked the
exchange-cell sampler. The parser computes OpenFOAM cell volumes from ASCII
`constant/polyMesh` files using the oriented owner/neighbour face-flux identity.

## Decision

- queued production meshes inventoried: `3`
- parser validation rows: `3`
- full production mesh volume export run here: `false`
- scheduler action: `false`
- fit/admission changed: `false`

The source meshes are multi-million-cell meshes, so this row does not run full
production parsing on the login node. The parser and exchange-cell CSV fallback
are unit-tested and ready for a scheduler-authorized extraction row.

## Outputs

- `mesh_volume_parser_readiness.csv`: queued Salt2/Salt3/Salt4 mesh metadata.
- `parser_validation_checks.csv`: validation and guardrail checks.
- `source_manifest.csv`: provenance and mutation flags.
- `summary.json`: package summary.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state,
Fluid source, external repository, blocker register, or generated docs index was
mutated. No OpenFOAM command, solver, postprocessor, sampler, fitting, model
selection, exchange-cell admission, Phase 4B rescore, Phase 5, or S6 trigger was
run.
