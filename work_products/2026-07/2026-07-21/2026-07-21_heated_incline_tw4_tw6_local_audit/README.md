---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/thermal_residual_attribution.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/sensor_coordinate_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_figtable_s8_wall_ts_residual_atlas/tw5_tw6_residual_atlas.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
tags: [heated-incline, TW5, TW6, external-bc, diagnostic]
related:
  - .agent/status/2026-07-21_TODO-HEATED-INCLINE-TW4-TW6-LOCAL-AUDIT-2026-07-21.md
  - .agent/journal/2026-07-21/heated-incline-tw4-tw6-local-audit.md
task: TODO-HEATED-INCLINE-TW4-TW6-LOCAL-AUDIT-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Writer / Reviewer
type: work_product
status: complete
---
# Heated-Incline TW4-TW6 Local Audit

This package audits the dominant heated-incline residual lane around TW4, TW5,
and TW6 using existing train-only diagnostics and setup metadata.

## Result

TW5/TW6 should not be treated first as a pure coordinate or unit problem. The
sensor map is bounded rather than exact, but the Phase E train residual pattern
and S8 atlas point to a missing source-treatment/model-form issue: the lower-leg
ambient wall row is legal and present, while the heater row is still
document-only and the Fluid path is underpredicting local wall temperatures.

Classification: `missing_source_term_primary_model_form_secondary`.

## Outputs

- `tw4_tw6_sensor_segment_ledger.csv`
- `heated_incline_bc_audit.csv`
- `heater_source_treatment_audit.csv`
- `failure_classification.csv`
- `next_candidate_recommendation.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native output, scheduler job, solver/postprocessing, Fluid edit, fitting,
source/property release, admission, thesis edit, or protected split scoring was
performed. TW4-TW6 remain diagnostic score targets, not runtime inputs.
