---
task: TODO-UPCOMER-EXCHANGE-CELL-VOLUME-EXPORT-SBATCH-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Scheduler / Implementer / Tester / Writer
type: work_product
status: submitted
tags: [upcomer, recirculation, exchange-cell, cell-volume, sbatch]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_volume_parser/README.md
---
# Upcomer Exchange Cell-Volume Export Sbatch

This package submits the production cell-volume export for the Salt2/Salt3/Salt4
upcomer exchange-cell queue. It writes task-owned CSV and JSON outputs only; it
does not mutate native OpenFOAM case directories and does not run OpenFOAM.

## Expected Outputs

See `expected_outputs.csv`.

## Guardrails

The submitted command runs only `tools/extract/openfoam_cell_volumes.py` against
read-only `constant/polyMesh` inputs and writes outputs under this package.
There is no solver, OpenFOAM postprocessing, sampler extraction, registry edit,
admission change, fitting, Phase 4B rescore, Phase 5, or S6 trigger.
