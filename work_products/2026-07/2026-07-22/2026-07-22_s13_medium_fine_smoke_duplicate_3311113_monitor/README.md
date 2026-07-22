---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/smoke_salt2_medium_one_window/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_sampler_face_area_repair/slurm-3311113.err
tags: [s13, scheduler-monitor, duplicate-smoke, no-admission]
related:
  - .agent/status/2026-07-22_TODO-S13-MEDIUM-FINE-SMOKE-DUPLICATE-3311113-MONITOR-2026-07-22.md
---
# S13 Duplicate Smoke 3311113 Monitor

Decision: `duplicate_smoke_cancelled_after_canonical_smoke_completed`.

The canonical S13 one-case/window smoke job `3311109` completed successfully
with four exact-label QOI rows, zero sampling-error rows, and generated
exchange-interface face rows containing `area_vector_x_m2`,
`area_vector_y_m2`, and `area_vector_z_m2`.

The later job `3311113` had the same Slurm name and same one-case/window smoke
purpose, but wrote to a separate output tree. It was cancelled after the
canonical smoke had already completed, to avoid duplicate sampler work. Its
partial output tree contains only pre-reduction/header files and is
nonadmissible.

No full medium/fine rerun, production harvest, source/property release, Qwall
release, coefficient admission, final score, or model-trigger action occurred.
