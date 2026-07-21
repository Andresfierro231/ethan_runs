---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/validation_report.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scheduler_attempts_observed.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scheduler_terminal_status.csv
tags: [journal, upcomer, exchange-cell, cell-vtk, salt2, scheduler]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke.json
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Salt2 Cell VTK Smoke

## Attempted

Implemented the first executable step after geometry release: Salt2-only
whole-mesh cell VTK extraction for `U`, `T`, and `rho`. The row staged the case
under task-owned `tmp/`, sourced OF13, reconstructed the selected time, ran
`foamToVTK`, copied the internal VTK into the package, and validated cell count
and required fields.

## Observed

Salt2 time `7915` reconstructed successfully in the task-owned staged case.
`foamToVTK` emitted a whole-mesh internal VTK and patch VTKs. The package VTK
validated with `2166996` `CELL_DATA` rows and fields `T`, `U`, `cellID`, and
`rho`.

The scheduler attempts are terminal failed, not completed. Attempt `3308472`
nevertheless produced and copied the valid VTK, then failed because the
generated validator script could not import the repo-local `tools` package.
That wrapper/import-path issue was repaired after the job, and the validator
then passed on the copied VTK. Attempt `3308473` was a redundant submission made
after direct compute-node `sbatch` reported that submission must occur from a
login node; it failed in the same wrapper class and did not produce a new
artifact.

## Inferred

The Salt2 `cell_vtk` lane is now unblocked for downstream manifest population.
The corrected runner pattern should be used for Salt3/Salt4, but the next row
should avoid duplicate submissions and should record terminal scheduler state
separately from artifact validation.

## Contradictions Or Caveats

This is not exchange-cell evidence by itself. It is only the whole-mesh cell
field snapshot required by the sampler. Exchange-interface, wall/core, and
`Q_wall_W` ownership remain unresolved, and no residual was moved into internal
`Nu`.

## Next Useful Actions

1. Claim a Salt3/Salt4 matrix or separate smoke row using the repaired runner
   pattern.
2. Populate a three-case cell VTK manifest only after Salt3/Salt4 pass the same
   `CELL_DATA == 2166996` and `U/T/rho` checks.
3. Define the conservative main/recirculation exchange basis separately.
4. Define the recirculation wall/core band separately before wallHeatFlux or
   residual accounting.
