---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - sampler-manifest
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_vtk_extraction/downstream_manifest_fragment.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-PREFLIGHT-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-SAMPLER-MANIFEST-PREFLIGHT-2026-07-21`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_sampler_manifest_preflight.py`.
- Added `tools/extract/test_s13_upcomer_exchange_sampler_manifest_preflight.py`.
- Published or refreshed `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_sampler_manifest_preflight/`.
- Output result: `3` manifest rows, `0` ready rows, `3` fail-closed rows, `harvest_allowed=false`, and `sampler_launch_allowed=false`.

## Validation

- `python3.11 -m py_compile ...` passed for all three S13 scripts/tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_sampler_manifest_preflight.py` passed.
- Reusable scaffold validator ran against `case_vtk_input_manifest.preflight.csv` and returned nonzero as expected because interface VTK, wall VTK, and normals are missing.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_same_window_uq_design tools.extract.test_s13_upcomer_exchange_surface_vtk_disposition tools.extract.test_s13_upcomer_exchange_sampler_manifest_preflight` passed: `Ran 15 tests in 0.253s`.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, sampler, or harvest launched: no.
- Fitting, model selection, score release, or exchange-cell admission: no.
- Residual absorption into internal Nu: no.

## Outcome

Complete fail-closed preflight. The manifest now carries real Salt2/Salt3/Salt4 cell VTK and volume CSV paths, but fails closed on missing exchange-interface VTK, wall/core VTK, throughflow normal, and interface normal inputs.
