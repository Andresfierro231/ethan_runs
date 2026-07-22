---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - source-bounded-cv
  - geometry-seed
  - surface-ready
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed/seed_cv_release_decision.csv
---

# Task TODO-S13-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21

Task: `TODO-S13-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21`

## Objective

Rerun the S13 source-bounded CV release gate using the completed
geometry-backed right-leg/upcomer seed, without launching surface extraction,
sampler/harvest, UQ, fitting, admission, or S11/S12/S13/S15/S6 triggers.

## Changes Made

- Claimed the board row for the seed-based source-bounded CV rerun.
- Added `tools/extract/build_s13_source_bounded_cv_rerun_from_geometry_seed.py`.
- Added `tools/extract/test_s13_source_bounded_cv_rerun_from_geometry_seed.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed/`.
- Output result: `3/3` seed source-bounded CV geometry rows released and `3/3` surface-extraction-ready rows; `0` sampler-ready rows and `s12_hiax1_unlocked=false`.

## Outcome

Complete geometry release, not a candidate/admission release. Salt2/Salt3/Salt4
all pass the seed geometry gate with `38880` seed cells, `38880` trusted wall
faces, `0.063435001093 m2` trusted wall area, positive internal seed/core
interface area, classified caps, and `0` unclassified escapes. The next row can
claim surface/source manifest refresh. Sampler manifest, production harvest,
same-QOI UQ, S12-HIAX1 implementation, S11/S13/S15/S6, fitting, and exchange
coefficient admission remain blocked.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_source_bounded_cv_rerun_from_geometry_seed.py tools/extract/test_s13_source_bounded_cv_rerun_from_geometry_seed.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_source_bounded_cv_rerun_from_geometry_seed` passed: `Ran 4 tests`.
- `python3.11 tools/extract/build_s13_source_bounded_cv_rerun_from_geometry_seed.py` passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed` passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed --strict` passed: `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_source_bounded_cv_rerun_from_geometry_seed` passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-SOURCE-BOUNDED-CV-RERUN-FROM-GEOMETRY-SEED-2026-07-21` passed.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker register OK.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, surface extraction, sampler, or harvest launched: no.
- Fluid or external repo mutated: no.
- Fitting, tuning, model selection, exchange-cell coefficient admission, or S11/S12/S13/S15/S6 trigger: no.
- Blocker register or generated index mutated: no.
- Residual absorption into internal Nu: no.
