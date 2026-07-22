---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_pressure_velocity.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/raw_endpoint_surface_file_manifest.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
tags: [pressure-ledger, two-tap, q-ref, same-qoi-uq, f6]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS.md
  - .agent/journal/2026-07-20/two-tap-face-qref-uq-progress.md
task: TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: work_product
status: complete
---
# Two-Tap Face q_ref And UQ Progress

Generated: `2026-07-20T18:10:59+00:00`

## Decision

Face-level q_ref evidence is now extracted from the harvested VTK surfaces, but
the evidence remains diagnostic only. Material reverse flow still blocks
ordinary component `K` and F6 promotion, and same-QOI mesh/time UQ remains
missing.

## Outputs

- `face_level_qref_flux_audit.csv`
- `residual_uq_progress.csv`
- `pressure_f6_two_tap_progress.csv`
- `paper_qref_uq_progress_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Face flux audit rows: `6`.
- Residual UQ progress rows: `3`.
- Rows with component K admitted: `0`.
- Rows with F6 fit performed: `0`.

## Guardrails

No scheduler work, native CFD/OpenFOAM mutation, registry/admission mutation,
Fluid edit, solver/postprocessing launch, F6 fit, component-K admission, hidden
global multiplier, clipped K, or endpoint-pressure invention was performed.
