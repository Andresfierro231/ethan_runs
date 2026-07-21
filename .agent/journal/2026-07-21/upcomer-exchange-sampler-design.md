---
provenance:
  - tools/extract/sample_upcomer_exchange_cell.py
  - tools/extract/test_sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/exchange_sampler_required_schema.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/exchange_sampler_dry_extraction_plan.csv
tags: [journal, upcomer, recirculation, exchange-cell, sampler-design, no-solver]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_sampler_design.json
task: TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21
date: 2026-07-21
role: Implementer/Tester/Writer/Hydraulics/Thermal-modeling
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Sampler Design

## Attempted

Implemented the first executable step after the dry evidence-extraction
contract: a no-solver sampler-design tool and synthetic fixture suite for the
upcomer exchange-cell state. The new tool writes a schema and dry extraction
plan, and it exposes pure calculation functions for future parser/execution
rows.

## Observed

The output schema now has explicit fields for property ratios, recirculation
volume, bidirectional exchange mass flow, residence time, paired thermal state,
wall-core temperature difference, pressure residual, and energy residual. The
dry plan carries the three current mainline windows: salt 2 at `7915` s, salt 3
at `7618` s, and salt 4 at `10000` s. The tests confirm that missing viscosity
does not silently zero or invent `R_mu`; it produces an explicit
`not_available_with_reason` status.

## Inferred

The next row can now focus on compute-node execution because the dry schema and
calculation semantics are fixed enough to test real parser outputs. However,
the current package still does not create admission-grade evidence. Real
extraction, same-QOI UQ, and Phase 4B rescore remain separate gates.

## Contradictions Or Caveats

The fixture VTK files are intentionally synthetic and small. They validate
calculation semantics, not OpenFOAM field availability. The exchange-rate
definition uses half the sum of main-to-cell and cell-to-main fluxes across the
named interface, while preserving the imbalance as a separate diagnostic for a
future execution row.

## Next Useful Actions

1. Claim a compute-node sampler execution row for the salt 2/3/4 queued
   windows.
2. Stage or point to terminal source cases without mutating native outputs.
3. Run extraction through `sbatch` or `srun`, then record job IDs, commands,
   logs, output files, and row-count/finite-value checks.
4. Claim same-QOI UQ pairing before any Phase 4B rescore.
