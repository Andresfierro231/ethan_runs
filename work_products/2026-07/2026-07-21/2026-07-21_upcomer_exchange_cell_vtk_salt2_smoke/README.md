---
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, cell-vtk, scheduler-smoke, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit
---
# Salt2 Upcomer Exchange Cell VTK Smoke

This package implements the first executable step after geometry release: a
Salt2-only whole-mesh cell VTK export for `U`, `T`, and `rho`. It stages a
task-local reconstructed case under `tmp/` and writes VTK outputs only under
this work-product package.

## Decision

- case: Salt2 `7915`
- expected cells: `2166996`
- submission state: `submitted`
- VTK validation state: `pass`
- native output mutation: `false`
- interface/wall/Q_wall/sampler launch: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `preflight.csv`
- `validation_report.csv`
- `submission_record.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `scripts/run_salt2_cell_vtk_smoke.sh`
- `scripts/submit_salt2_cell_vtk_smoke.sbatch`
- `scripts/validate_salt2_cell_vtk.py`

## Guardrails

Do not write VTK or reconstructed fields into the native Salt2 case. Do not
generate exchange-interface or wall/core VTKs here. Do not run the exchange-cell
sampler, fit, score, admit, rescore Phase 4B, trigger Phase 5/S6, or absorb any
residual into internal `Nu`.
