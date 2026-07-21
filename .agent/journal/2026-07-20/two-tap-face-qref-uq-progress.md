---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/paper_qref_uq_progress_note.md
tags: [journal, pressure-ledger, two-tap, q-ref, same-qoi-uq]
related:
  - .agent/status/2026-07-20_TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS.md
  - imports/2026-07-20_two_tap_face_qref_uq_progress.json
task: TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: journal
status: complete
---
# Two-Tap Face q_ref And UQ Progress

Task: `TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS`

## Work Completed

Built a face-level q_ref/UQ progress package from the already harvested VTK
surfaces. The package parses OpenFOAM VTK `POLYDATA` cell data, computes
polygon areas, positive/negative/absolute mass flux, reverse area/mass
fractions, secondary velocity fraction, and diagnostic q_ref values for all six
current `corner_lower_right` endpoint surfaces.

## Scientific Decision

Face-level flux evidence now exists, but it does not unlock ordinary
`component_K` or F6. The face-level evidence confirms material reverse flow,
while same-QOI residual mesh/time UQ and clean component isolation remain
missing. The correct next use is recirculating section-effective residual
diagnostics, not ordinary coefficient admission.

## Next Evidence Needed

- same-QOI residual mesh/time UQ;
- low-reverse same-topology anchor for ordinary `K` contrast;
- split-safe recirculation pressure scorecard against `F3_shah_apparent` before
  any F6 promotion.

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/build_two_tap_face_qref_uq_progress.py`
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/test_two_tap_face_qref_uq_progress.py`

Both passed before closeout.
