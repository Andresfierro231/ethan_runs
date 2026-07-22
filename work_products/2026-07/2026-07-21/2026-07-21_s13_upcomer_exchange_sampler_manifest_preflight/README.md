---
provenance:
  generated_by: build_s13_upcomer_exchange_sampler_manifest_preflight.py
  generated_at: 2026-07-21T17:18:46-05:00
tags:
  - s13
  - upcomer-exchange
  - sampler-manifest
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction/downstream_manifest_fragment.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_reusable_harvest_scaffold/case_vtk_input_manifest.template.csv
---

# S13 Upcomer Exchange Sampler Manifest Preflight

This package populates the reusable exchange sampler manifest as far as current
inputs allow. The Salt2, Salt3, and Salt4 cell VTK and volume CSV paths are
present, but interface VTKs, wall VTKs, and trusted normal vectors remain
missing.

Result: fail-closed. The scaffold validator was run as a preflight and is
expected to fail until the missing geometry/surface lanes are released. No
sampler, harvest, scheduler job, solver, postprocessing run, fit, score, or
admission step was launched.
