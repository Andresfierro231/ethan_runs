---
provenance:
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - tools/extract/test_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/summary.json
tags: [s13, upcomer-exchange, face-area-vector, repair, medium-fine]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler
task: TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
---
# S13 Face-Area-Vector Repair Rerun Gate

The completed S13 medium/fine sampler landed at the scheduler level but failed
closed scientifically: `exact_label_qoi_rows=0` and `sampling_error_rows=6`.
The generated face CSVs from that run lack `area_vector_x_m2`,
`area_vector_y_m2`, and `area_vector_z_m2`, so they cannot support
interface flux or residence-time reductions.

The current sampler source is ready for a fresh rerun: generated interface,
trusted-wall, and cap face rows are passed through `add_area_vector_columns`,
and `interface_reduction` fails closed if those columns are missing. This row
added writer-side regression coverage so future face-contract CSVs must
preserve the vector columns.

Decision: `face_vector_repair_source_ready_fresh_slurm_rerun_required`.

No fresh Slurm job was submitted here. The next row should be a scheduler
rerun from the current source, then a mesh/GCI gate only if exact-label rows
are produced.

## Guardrails

Native solver outputs were read only. No scheduler submission, solver,
OpenFOAM postProcess, production harvest, registry/admission mutation,
Qwall/source-property release, coefficient admission, final score, or
S11/S12/S13/S15/S6 trigger was performed.
