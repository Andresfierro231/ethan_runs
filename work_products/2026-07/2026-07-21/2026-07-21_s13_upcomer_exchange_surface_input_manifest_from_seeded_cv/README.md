---
provenance:
  generated_by: build_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv.py
  generated_at: 2026-07-21T19:24:51-05:00
tags:
  - s13
  - upcomer-exchange
  - seeded-cv
  - surface-input-manifest
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_release_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_exchange_interface_faces.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_rerun_from_geometry_seed/seeded_trusted_wall_faces.csv
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_three_case_cell_vtk_manifest/case_vtk_input_manifest.cells_populated.csv
task: TODO-S13-UPCOMER-EXCHANGE-SURFACE-INPUT-MANIFEST-FROM-SEEDED-CV-2026-07-21
---

# S13 Surface/Input Manifest From Seeded CV

This package inventories the released seeded source-bounded CV inputs for
Salt2, Salt3, and Salt4. It confirms that all three cases have materialized
seeded cell, internal seed/core interface-face, trusted wall-face, wall/core
band, and normal-convention inputs suitable for a later surface-extraction
preflight.

Result: `release_surface_extraction_input_manifest_only`.

- seeded surface-extraction input rows ready: `3` / `3`
- sampler-manifest-ready rows: `0` / `3`
- sampler/harvest/UQ/admission allowed now: `false`

The important boundary is that these are geometry/source-input manifests, not
raw same-window sampled interface/wall VTK outputs. `Q_wall_W`, raw interface
and wall sampled fields, sampler outputs, same-QOI UQ, coefficient admission,
and S11/S12/S13/S15/S6 triggers remain blocked.

## Artifacts

- `seeded_surface_input_inventory.csv`: streamed inventory of required seeded
  CSV inputs and required-column status.
- `seeded_surface_input_manifest.csv`: per-case downstream manifest with
  task-owned mask/face/band CSV paths.
- `input_file_existence_checks.csv`: file existence checks for every manifest
  input consumed by the next extraction row.
- `downstream_gate.csv`: per-case next-row gate status.
- `case_preflight_matrix.csv`: one Salt2/Salt3/Salt4 decision row joining the
  seeded release to existing cell VTK, volume, and source/sink context.
- `surface_input_decision.csv`: package-level release/fail-closed decision.
- `no_mutation_guardrails.csv`: explicit mutation/admission/scheduler guardrail
  status.
- `source_manifest.csv`: provenance for every read-only context file.
