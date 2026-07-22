---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/recommended_model_forms_to_try.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
tags: [journal, thesis, model-form-scoreboard, signed-errors, one-d-model]
related:
  - .agent/status/2026-07-22_TODO-THESIS-MASTER-MODEL-FORM-SCOREBOARD-2026-07-22.md
  - imports/2026-07-22_thesis_master_model_form_scoreboard.json
task: TODO-THESIS-MASTER-MODEL-FORM-SCOREBOARD-2026-07-22
date: 2026-07-22
role: Writer / Implementer / Tester / Reviewer
type: journal
status: complete
---
# Thesis Master Model-Form Scoreboard

Observed: the older endpoint bakeoff was already a good M0-M4 scoreboard, but it
did not incorporate newer LitRev MF taxonomy, S13 upcomer exchange evidence,
S14/F6 pressure screening, two-tap section-effective pressure evidence, or the
S6 blocked-scorecard shell.

Attempted: built a reproducible master scoreboard package that joins these
sources read-only and keeps all admission/gate labels explicit. The package also
computes signed individual TP/TW sensor errors from the existing sensor-level
table using `signed_error_K = predicted_K - target_K` and
`signed_error_percent_of_target = 100 * signed_error_K / target_K`.

Observed: the package emits `204` individual sensor-error rows, with `180`
finite predictions and `24` missing prediction rows. These rows are legacy
numeric context, not final locked-split predictive scores.

Inferred: the highest-value next model-form work is not to force M6 scoring.
The more rigorous order is: implement a true M0 baseline, keep S13/M5 moving
toward source/Qwall/UQ closure, use the two-tap section-effective pressure
negative result for pressure figures, and only then revisit ordinary F6 and M6
freeze gates.

Caveat: no new model was run and no new score was produced. The package is a
thesis-facing synthesis and figure-data product, not a scoring/admission event.
