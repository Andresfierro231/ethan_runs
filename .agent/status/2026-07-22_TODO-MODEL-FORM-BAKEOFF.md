---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff/README.md
  - tools/analyze/build_model_form_bakeoff_from_observations.py
tags: [model-form, bakeoff, diagnostic-only, no-admission]
related:
  - TODO-MODEL-FORM-BAKEOFF
task: TODO-MODEL-FORM-BAKEOFF
date: 2026-07-22
role: Implementer/Reviewer/Tester/Writer
type: status
status: complete
---
# TODO-MODEL-FORM-BAKEOFF

## Objective

Refresh the model-form bakeoff from existing observation and model-form outputs
without Fluid reruns, protected scoring, or new coefficient fitting.

## Outcome

Complete. The package consumed `1032` observation rows and emitted `15`
model/case score rows across `5` model forms. The best current mdot comparator
is `F3_shah_apparent` with mean absolute mdot error `2.669%`; this remains a
diagnostic comparator, not a final frozen candidate.

## Changes Made

- `tools/analyze/build_model_form_bakeoff_from_observations.py`
- `tools/analyze/test_model_form_bakeoff_from_observations.py`
- `work_products/2026-07/2026-07-22/2026-07-22_model_form_bakeoff/`
- `.agent/journal/2026-07-22/model-form-bakeoff.md`
- `imports/2026-07-22_model_form_bakeoff.json`

## Validation

- `env PYTHONPATH=. python3.11 tools/analyze/test_model_form_bakeoff_from_observations.py`: passed.
- Four-package CSV/JSON parse batch: passed; `26` CSV files, `169` CSV rows, and `4` JSON summaries loaded.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
Fluid/external edit, validation/holdout/external scoring, source/property
release, coefficient admission, final-score claim, or residual absorption into
internal `Nu` was performed.
