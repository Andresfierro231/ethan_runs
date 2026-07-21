---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - same-qoi-uq
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_same_qoi_uq_phase_c_admission_table/same_qoi_uq_admission_table.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-SAME-WINDOW-UQ-DESIGN-2026-07-21`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_same_window_uq_design.py`.
- Added `tools/extract/test_s13_upcomer_exchange_same_window_uq_design.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_same_window_uq_design/`.
- Output result: `3` target exchange QOI rows, `4` support-gate rows, `0` S11-reviewable candidates, `uq_release_allowed=false`, and `sampler_or_harvest_allowed=false`.

## Validation

- `python3.11 -m py_compile ...` passed for all three S13 scripts/tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_same_window_uq_design.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_same_window_uq_design tools.extract.test_s13_upcomer_exchange_surface_vtk_disposition tools.extract.test_s13_upcomer_exchange_sampler_manifest_preflight` passed: `Ran 15 tests in 0.253s`.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, sampler, or harvest launched: no.
- Fitting, model selection, score release, or exchange-cell admission: no.
- Residual absorption into internal Nu: no.

## Outcome

Complete fail-closed design. Retained-time evidence alone is insufficient for S13/S11 release; each target QOI still requires same-label neighboring windows, accepted same-QOI mesh/GCI, and trusted interface/wall/source geometry.
