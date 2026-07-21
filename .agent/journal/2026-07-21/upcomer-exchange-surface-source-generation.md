---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/surface_extraction_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/source_sink_static_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_surface_source_generation/source_sink_summary.csv
tags: [journal, upcomer, exchange-cell, surface-generation, source-ledger, no-solver]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_surface_source_generation.json
task: TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Surface/Source Generation

## Attempted

Tried to advance from volume readiness to same-window cell/interface/wall/source
readiness. The work built a reproducible package that parses the case thermal
boundary contract and emits exact release conditions for the surface lanes that
would feed `sample_upcomer_exchange_cell.py`.

## Observed

The Salt2/Salt3/Salt4 `0/T` files contain constant `Q` boundary-condition terms
for heater/source patches and cooler/sink patches. Those terms can be recorded
as a static source/sink ledger without launching OpenFOAM or mutating native
case directories.

The same files and prior audit do not define a conservative exchange interface
between main throughflow and recirculation cell. Existing `topoSetDict`
faceZones represent loop mass-flow planes, not an exchange-cell interface. The
wall/core band tied to the exchange cell is also not defined.

## Inferred

It is rigorous to mark source/sink static BC accounting ready, but not rigorous
to launch surface extraction. Running OpenFOAM now would create outputs for
surfaces whose physical ownership is still ambiguous. The correct next step is
a geometry-release row, then a scheduler row that writes only into a task-owned
staged case.

## Contradictions Or Caveats

The source/sink ledger is a boundary-condition contract, not a realized
same-window wall heat balance. Energy residual rows still require `Q_wall_W`
from task-owned wallHeatFlux integration plus the exchange-state terms. No
residual was moved into internal `Nu`.

## Next Useful Actions

1. Approve the cell-region/cellId policy: whole mesh versus upcomer cellSet,
   with explicit cell-volume CSV alignment.
2. Define the exchange-interface geometry and sign convention from a trusted
   source, not from the existing representative outlet proxy.
3. Define the wall/core surface or band tied to the recirculation region.
4. Claim a scheduler row to run staged OpenFOAM sampling only after the three
   geometry contracts are ready.
5. Run the diagnostic sampler only after cell/interface/wall VTK and `Q_wall_W`
   lanes exist; keep fit, score, and admission disabled.
