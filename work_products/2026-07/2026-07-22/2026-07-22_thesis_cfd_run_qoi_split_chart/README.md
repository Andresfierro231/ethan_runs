---
provenance:
  task_id: TODO-THESIS-CFD-RUN-QOI-SPLIT-CHART-2026-07-22
  generated_at: 2026-07-22T12:00:42-05:00
tags:
  - thesis
  - cfd-qoi-chart
  - train-holdout
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/README.md
---
# Thesis CFD Run QoI Split Chart

Decision: `cfd_run_qoi_split_chart_complete_no_model_scoring`.

This package creates thesis-facing CSV charts of CFD runs versus split role and
QoIs. It treats `val_salt2` as part of the `holdout_test` bucket while keeping
the subtype `external_test`, so the thesis can report one protected test set
without losing provenance.

Outputs:

- `cfd_run_qoi_split_chart_wide.csv`: one row per CFD run with mdot, TP1-TP6,
  TW1-TW11, TP mean, and TW mean columns.
- `cfd_run_qoi_split_chart_long.csv`: tidy QoI rows for plotting.
- `cfd_run_qoi_source_coverage.csv`: coverage and caveats.
- `holdout_test_policy_update.csv`: split grouping with no-fit/no-selection
  flags.

Salt1 nominal uses the latest corrected Salt1 stopped-run/uncertainty evidence.
That source has TP probe values and a wall-temperature spatial mean, but not
individual TW1-TW11 labels, so the TW columns are intentionally blank for that
row and the coverage status is partial.

No model training, fitting, scoring, source/property release, Qwall release,
coefficient admission, candidate freeze, solver launch, scheduler action,
native-output mutation, or registry/admission mutation was performed.
