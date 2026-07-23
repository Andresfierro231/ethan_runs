---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset/README.md
  - tools/analyze/build_upcomer_onset_regime_table.py
tags: [upcomer, onset, recirculation, diagnostic-only]
related:
  - TODO-UPCOMER-ONSET
task: TODO-UPCOMER-ONSET
date: 2026-07-22
role: Writer/Implementer/Tester
type: status
status: complete
---
# TODO-UPCOMER-ONSET

## Objective

Refresh the upcomer onset regime package with current recirculation-fraction and
UQ context while preserving ordinary-pipe and exchange-coefficient guardrails.

## Outcome

Complete. The package emits `3` Salt2/Salt3/Salt4 regime rows, all classified as
`recirculation_cell_observed`. Ordinary upcomer pipe admission rows remain `0`
and exchange-coefficient admission rows remain `0`.

## Changes Made

- `tools/analyze/build_upcomer_onset_regime_table.py`
- `tools/analyze/test_upcomer_onset_regime_table.py`
- `work_products/2026-07/2026-07-22/2026-07-22_upcomer_onset/`
- `.agent/journal/2026-07-22/upcomer-onset.md`
- `imports/2026-07-22_upcomer_onset.json`

## Validation

- `env PYTHONPATH=. python3.11 tools/analyze/test_upcomer_onset_regime_table.py`: passed.
- Four-package CSV/JSON parse batch: passed; `26` CSV files, `169` CSV rows, and `4` JSON summaries loaded.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
Fluid/external edit, validation/holdout/external scoring, ordinary upcomer
`Nu/f_D/K` admission, exchange-cell coefficient admission, source/property
release, final score, or residual absorption into internal `Nu` was performed.
