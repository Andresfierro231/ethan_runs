---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_medium_fine_exact_label_sampler/sampling_error_log.csv
  - tools/extract/build_s13_upcomer_exchange_medium_fine_exact_label_sampler.py
tags: [s13, upcomer-exchange, face-area-vector, repair, journal]
related:
  - .agent/status/2026-07-22_TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22.md
  - imports/2026-07-22_s13_upcomer_exchange_face_area_vector_repair_rerun.json
task: TODO-S13-UPCOMER-EXCHANGE-FACE-AREA-VECTOR-REPAIR-RERUN-2026-07-22
date: 2026-07-22
role: Implementer/Tester/Writer
type: journal
status: complete
---
# S13 face-area-vector repair rerun

## Attempted

Claimed the narrow repair path after the medium/fine sampler completed at the
scheduler level but produced no exact-label QOI rows.

Added regression coverage proving generated face-contract CSVs preserve
`area_vector_x_m2`, `area_vector_y_m2`, and `area_vector_z_m2`.

## Observed

The fail-closed sampler package generated mesh masks and face identities for
all six Salt2/Salt3/Salt4 medium/fine cases. The reduction failed because the
generated face CSV rows did not carry face area vector components.

## Inferred

The best next repair is local and mechanical: derive or preserve the vector
components from read-only `constant/polyMesh` face geometry and ensure the
interface/wall reducers consume them. This should be tested before any new
Slurm submission.

The current source already has the required vector writer and reader guards;
the old Slurm outputs are stale/fail-closed because their generated face CSVs
lack the vector columns. A fresh Slurm rerun from the current source is the
next evidence-producing step.

## Next Useful Actions

1. Claim a scheduler-authorized rerun row.
2. Regenerate the S13 medium/fine face contracts from current source.
3. Confirm generated face CSVs include vector columns before exact reductions.
4. If exact-label rows land, rerun the same-label mesh/GCI gate.
