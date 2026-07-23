---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_thesis_endpoint_model_form_bakeoff/model_form_scores.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_litrev_csem_incorporation/model_form_thesis_ladder.csv
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_overnight_compute_node_run/agent360_refresh/sensor_level_errors.csv
tags: [thesis, model-form-scoreboard, signed-errors, one-d-model]
related:
  - .agent/status/2026-07-22_TODO-THESIS-MASTER-MODEL-FORM-SCOREBOARD-REFRESH-TRY-ALL-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-master-model-form-scoreboard-refresh-try-all.md
task: TODO-THESIS-MASTER-MODEL-FORM-SCOREBOARD-REFRESH-TRY-ALL-2026-07-22
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: work_product
status: complete
---
# Thesis Master Model-Form Scoreboard

This package consolidates the thesis-facing 1D model-form evidence into one
scoreboard. It joins the M0-M6 endpoint ladder, MF-01-MF-06 LitRev taxonomy,
S13 upcomer exchange evidence, S14/F6 pressure screening, two-tap
section-effective pressure evidence, D1-D4 diagnostic model-form tests,
PASSIVE-H2, HX, CAND001, M0 shell evidence, and the S6 blocked final scorecard
shell.

It also emits signed individual TP/TW sensor-error rows for available legacy
numeric model forms. These rows include `predicted_K`, `target_K`,
`signed_error_K = predicted_K - target_K`, and
`signed_error_percent_of_target = 100 * signed_error_K / target_K`.

## Outputs

- `master_model_form_scoreboard.csv`
- `term_glossary.csv`
- `signed_sensor_errors.csv`
- `signed_sensor_error_summary.csv`
- `figure_ready_signed_sensor_errors.csv`
- `recommended_model_forms_to_try.csv`
- `try_all_model_form_disposition.csv`
- `diagnostic_tested_model_form_scoreboard.csv`
- `diagnostic_tested_sensor_errors.csv`
- `thesis_figure_plan.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

## Result

- master scoreboard rows: `25`
- glossary rows: `43`
- signed sensor-error rows: `204`
- finite signed sensor-error rows: `180`
- diagnostic tested model-form rows: `6`
- diagnostic tested sensor-error rows: `270`
- recommended model forms to try: `10`
- best current diagnostic form: `D4_M3_segment_offsets_min2_train`

Current scoreable diagnostic forms have been tried through the existing
diagnostic addendum and integrated here. Physics forms that are not currently
scoreable are listed as blocked with their exact required gates. No new solver,
sampler/harvest/UQ execution, source release, coefficient admission, candidate
freeze, final score, thesis current-file edit, or native-output mutation was
performed by this refresh.
