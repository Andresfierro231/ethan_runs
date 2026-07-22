---
provenance:
  - tools/extract/sample_upcomer_exchange_cell.py
  - tools/extract/test_sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/exchange_sampler_rows.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/summary.json
tags: [heat-loss, upcomer, exchange-cell, sampler-implementation, fail-closed, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_sampler_implementation/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit/README.md
  - .agent/status/2026-07-21_TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION.md
task: TODO-HEATLOSS-UPCOMER-EXCHANGE-SAMPLER-IMPLEMENTATION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling/Hydraulics/cfd-pp
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Upcomer Exchange Sampler Implementation Note

This package is the implementation-interface follow-on to the existing
`TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21` sampler. The reusable sampler
still writes its original design README and summary when pointed at a custom
output directory; this note records the current heat-loss implementation row.

## Implementation Delta

`tools/extract/sample_upcomer_exchange_cell.py` now emits explicit extraction
rows from supplied VTK inputs or fail-closed rows when required VTK inputs are
missing. The row schema carries `extraction_status`, `missing_inputs`,
`same_window_id`, pressure and energy residual statuses, no-admission guard
columns, and the residual policy `do_not_hide_heat_residual_in_internal_Nu`.

The package contains a dry Salt2 row at `7915` s with
`extraction_status=not_available_with_reason:missing_required_vtk_inputs`
because no `cell_vtk` or `interface_vtk` was supplied from a production
input-generation row.

## Decision

- production sampler launch: `false`
- native CFD/OpenFOAM output mutation: `false`
- scheduler action: `false`
- fit, score, Phase 4B rescore, or closure admission: `false`
- residual absorption into internal Nu: `false`

The next row should generate or point to trusted `cellVolume`, `recircMask`,
exchange-interface VTK, wall/core surface VTK, and source/sink ledger inputs
before running production extraction.
