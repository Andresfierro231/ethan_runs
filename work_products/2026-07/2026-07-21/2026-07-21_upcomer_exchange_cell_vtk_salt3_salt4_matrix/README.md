---
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT3-SALT4-MATRIX-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, cell-vtk, salt3, salt4, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation
---
# Salt3/Salt4 Upcomer Exchange Cell VTK Matrix

This package extends the validated Salt2 whole-mesh cell VTK path to Salt3 and
Salt4. It stages local task-owned reconstructed cases under `tmp/` and writes
cell-field VTK artifacts only under this work-product package.

## Decision

- cases: Salt3 `7618`, Salt4 `10000`
- required fields: `U;T;rho`
- expected cells per case: `2166996`
- passed cases: `2/2`
- submission state: `submitted`
- native output mutation: `false`
- interface/wall/Q_wall/sampler launch: `false`
- fit/score/admission allowed now: `false`

## Outputs

- `preflight.csv`
- `validation_report.csv`
- `submission_record.csv`
- `scheduler_terminal_status.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `scripts/run_salt3_salt4_cell_vtk_matrix.sh`
- `scripts/submit_salt3_salt4_cell_vtk_matrix.sbatch`
- `scripts/validate_salt3_salt4_cell_vtk.py`

## Guardrails

Do not write VTK or reconstructed fields into native Salt3/Salt4 cases. Do not
generate exchange-interface or wall/core VTKs here. Do not run the exchange-cell
sampler, fit, score, admit, rescore Phase 4B, trigger Phase 5/S6, or absorb any
residual into internal `Nu`.
