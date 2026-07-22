---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/README.md
tags: [status, thesis, cfd-qoi-chart, holdout-test]
related:
  - .agent/journal/2026-07-22/thesis-cfd-run-qoi-split-chart.md
  - imports/2026-07-22_thesis_cfd_run_qoi_split_chart.json
task: TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22
date: 2026-07-22
role: Forward-pred / cfd-pp / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22

## Objective

Build a thesis-friendly CSV chart of CFD runs versus split role and key QoIs
(`mdot`, TP1-TP6, TW1-TW11), while treating the external-test row as part of
the protected holdout/test bucket with an explicit `external_test` subtype.

## Outcome

Published:
`work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/`.

Decision:
`cfd_run_qoi_split_chart_complete_no_model_scoring`.

Key results:

- wide CFD chart rows: `7`
- long/tidy QoI rows: `127`
- train rows: `4`
- holdout_test rows: `3`
- external-test rows grouped as holdout_test: `1`
- all source paths existed: `true`
- model scoring performed: `false`
- fitting/model selection performed: `false`
- source/property release: `false`
- candidate freeze: `false`

## Changes Made

- Added `tools/analyze/build_thesis_cfd_run_qoi_split_chart.py`.
- Added `tools/analyze/test_thesis_cfd_run_qoi_split_chart.py`.
- Published `cfd_run_qoi_split_chart_wide.csv`, `cfd_run_qoi_split_chart_long.csv`,
  source coverage, holdout/test policy, source manifest, guardrails, summary,
  and package README.
- Added this status file, a journal entry, and import manifest.
- Added a pointer from the model-form training-roster operational note.

## Validation

- `python3.11 -m py_compile tools/analyze/build_thesis_cfd_run_qoi_split_chart.py` - passed.
- `python3.11 -m unittest tools.analyze.test_thesis_cfd_run_qoi_split_chart` - passed; 2 tests OK.
- `python3.11 tools/analyze/build_thesis_cfd_run_qoi_split_chart.py` - passed and regenerated the package.
- Manual CSV inspection confirmed `val_salt2` is `split_group=holdout_test`,
  `split_subrole=external_test`, and all rows retain
  `coefficient_fit_allowed_now=False` and `model_selection_allowed_now=False`.

## Unresolved Blockers

Corrected Salt1 nominal still lacks individual `TW1`-`TW11` labels in the
latest stopped-run/uncertainty source used here. The chart therefore reports
Salt1 `TP1`-`TP6`, `mdot`, and `TW_mean_K`, but leaves individual Salt1 TW
columns blank with partial coverage status.

Salt1-4 nominal rows are the intended training split, but current coefficient
fitting remains locked until source/property release because the MF16
source/property exact-field gate is fail-closed.

## Guardrails

No validation, holdout, or external-test model scoring occurred. No fitting,
model selection, source/property release, Qwall release, coefficient admission,
candidate freeze, solver/postprocessing/sampler/harvest/UQ launch, scheduler
action, native-output mutation, registry/admission mutation, Fluid/external
edit, thesis-current/LaTeX edit, S11/S12/S13/S15/S6 trigger, generated-index
refresh, deletion, staging, commit, push, or runtime-leakage relaxation
occurred.
