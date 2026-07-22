---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampled_field_qwall_contract_from_seeded_vtk/sampled_field_scheduler_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
tags: [s13, upcomer-exchange, limited-sampled-field, scheduler]
related:
  - .agent/status/2026-07-21_TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21.md
task: TODO-S13-UPCOMER-EXCHANGE-LIMITED-SAMPLED-FIELD-SCHEDULER-EXTRACTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer
type: work_product
status: complete_nonharvest
---
# S13 Limited Sampled-Field Scheduler Extraction

This package is the scheduler-run limited extraction for interface `U/T/rho`
and wall/core `T` from existing cell VTK fields and released seeded geometry.
It is nonharvest evidence only.

- cases processed: `3`
- interface detail rows: `116640`
- wall detail rows: `116640`
- summary rows: `3`
- Slurm job id: `3307325.srun_s13_limsamp`
- `Q_wall_W` released rows: `0`
- production harvest allowed rows: `0`
- admission allowed rows: `0`

`wall_owner_T_K` is mapped from the owner cell of trusted wall faces. It is not
wallHeatFlux, and it does not release `Q_wall_W`.
