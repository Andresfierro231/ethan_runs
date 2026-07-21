---
provenance:
  - tools/extract/build_upcomer_exchange_sampler_reusable_harvest_scaffold.py
  - tools/extract/test_build_upcomer_exchange_sampler_reusable_harvest_scaffold.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/README.md
tags: [upcomer, exchange-cell, reusable-scripts, validation, blockers]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold.json
task: TODO-UPCOMER-EXCHANGE-SAMPLER-REUSABLE-HARVEST-SCAFFOLD-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Sampler Reusable Harvest Scaffold

## Attempted

Built a reusable scaffold around `tools/extract/sample_upcomer_exchange_cell.py`
so a later task can harvest exchange-cell rows without recreating command lines.
The builder emits a case-volume map, input contract, populated-but-blocked
manifest template, blocker ledger, reusable scripts, README, summary, and source
manifest.

## Observed

The completed input-generation package provides task-owned Salt2/Salt3/Salt4
cell-volume CSVs and summaries. Each volume summary reports `2166996` cells,
`0` negative-volume cells, and `0` zero-or-negative-volume cells. The remaining
blocking inputs are the same-window cell VTK, named exchange-interface VTK,
wall/core VTK, and source/sink ledger.

The dry sampler already exposes `--throughflow-normal`, `--interface-normal`,
and `--volume-csv`, so no sampler interface change was needed. The generated
scripts require explicit normals in the manifest path rather than relying on the
sampler defaults.

## Inferred

The fastest rigorous next step is to let the active surface/source-generation
work finish or fail with exact paths. Once those paths exist, a new harvest row
can copy `case_vtk_input_manifest.template.csv`, replace `MISSING_*` values and
blank normals, run the validator, then run `harvest_exchange_case_matrix.sh`.

## Contradictions Or Caveats

The volume basis is ready, but that does not make the sampler scientifically
ready. Without a named exchange interface and normal sign convention,
`mdot_exchange` is not interpretable. Without the source/sink ledger, the energy
residual remains unavailable or diagnostic-only.

## Next Useful Actions

1. Publish or consume same-window cell/interface/wall/source products from a
   separate claimed row.
2. Fill a concrete `case_vtk_input_manifest.csv` with real paths and normals.
3. Run `validate_exchange_case_inputs.py` before any sampler harvest.
4. Harvest rows only under a new task-owned output directory.
5. Attach same-QOI UQ before any Phase 4B rescore or exchange-cell admission
   decision.
