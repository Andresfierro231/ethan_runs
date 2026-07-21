---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - source-bounded-cv
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21`

## Objective

Define or fail-close a source-bounded, face-closed S13 recirculation control
volume for Salt2/Salt3/Salt4 with trusted exchange-interface faces, trusted
right-leg wall faces, wall/core band, outward normal convention, source/sink
boundary classification, and exact provenance.

## Changes Made

- Claimed the board row for the source-bounded CV definition task.
- Added `tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py`.
- Added `tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/`.
- Output result: `219380` recirculation-CV cell rows, `30128` exchange-interface face rows, `0` trusted-wall face rows, `17028` untrusted boundary faces, and `0/3` source-bounded CV releases.

## Outcome

Complete fail-closed. Existing evidence cannot produce a source-bounded,
face-closed S13 recirculation CV with trusted wall faces. Salt2/Salt3/Salt4
all have finite interface face rows and finite outward normal conventions, but
all three have no trusted right-leg wall faces and touch unreleased lower-leg
boundary patches. Therefore wall/source `Q_wall_W`, sampler preflight rerun,
S13/S12 harvest, same-QOI UQ, and S11/S12/S13 candidate claims remain blocked.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_source_bounded_cv_definition` passed: `Ran 4 tests`.
- `python3.11 tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py` passed and wrote the package.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition` passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition --strict` passed: `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition` passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21` passed.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker register OK.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, surface extraction, sampler, or harvest launched: no.
- Fluid or external repo mutated: no.
- Fitting, tuning, model selection, exchange-cell admission, or S11/S12/S13/S15/S6 trigger: no.
- Blocker register or generated index mutated: no.
- Residual absorption into internal Nu: no.
