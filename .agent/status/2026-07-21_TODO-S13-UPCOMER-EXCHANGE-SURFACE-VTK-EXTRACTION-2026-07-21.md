---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - surface-vtk
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/downstream_surface_vtk_inputs.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-SURFACE-VTK-EXTRACTION-2026-07-21`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_surface_vtk_disposition.py`.
- Added `tools/extract/test_s13_upcomer_exchange_surface_vtk_disposition.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction/`.
- Output result: `3` ready cell VTK rows, `0` released surface rows, `12` blocked non-cell surface/harvest rows, and `surface_vtk_extraction_allowed=false`.

## Validation

- `python3.11 -m py_compile ...` passed for all three S13 scripts/tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_surface_vtk_disposition.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_same_window_uq_design tools.extract.test_s13_upcomer_exchange_surface_vtk_disposition tools.extract.test_s13_upcomer_exchange_sampler_manifest_preflight` passed: `Ran 15 tests in 0.253s`.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Surface extraction launched: no.
- Solver, postprocessing, sampler, or harvest launched: no.
- Fitting, model selection, score release, or exchange-cell admission: no.

## Outcome

Complete fail-closed surface disposition. Whole-mesh cell VTK paths are carried forward for Salt2/Salt3/Salt4, but exchange-interface VTK, wall/core VTK, and `Q_wall_W` remain unreleased.
