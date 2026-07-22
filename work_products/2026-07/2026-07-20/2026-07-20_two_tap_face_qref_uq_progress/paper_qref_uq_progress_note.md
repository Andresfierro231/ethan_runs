---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/face_level_qref_flux_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/residual_uq_progress.csv
tags: [paper-diagnostic, two-tap, q-ref, pressure-uq]
task: TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: paper-diagnostic-note
status: complete
---
# Paper Diagnostic Note: Face-Level q_ref And Remaining Pressure Gates

## Result

The harvested VTK surfaces are sufficient to compute face-level positive,
negative, and absolute mass-flux diagnostics. That is progress beyond the
area-mean endpoint ledger. However, the face-level audit still shows material
reverse flow at the `corner_lower_right` endpoint surfaces, so the throughflow
denominator remains diagnostic and cannot support ordinary component `K`.

## Interpretation

The next pressure model should use these face-level flux terms as diagnostic
support for a recirculating section-effective residual. It should not use them
to admit ordinary `K` or F6. Same-QOI residual UQ and either a low-reverse
anchor or a split-safe recirculation scorecard remain required.

## Paper-Safe Claims

- Face-level flux evidence exists for the current two-tap endpoint surfaces.
- Current face-level evidence confirms recirculation remains material.
- Ordinary `component_K` and F6 admission remain blocked.

## Forbidden Claims

- Do not claim face-level q_ref admits ordinary component `K`.
- Do not claim same-QOI mesh/time UQ is complete.
- Do not use current recirculating rows as low-reverse anchors.

Generated face-flux rows: `6`; residual UQ
progress rows: `3`.
