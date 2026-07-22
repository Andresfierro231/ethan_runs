---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_holdout_metrics.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_field_validation.csv
tags: [salt2, pm5, holdout, admission, recirculation]
related:
  - tools/extract/repair_salt2_pm5_holdout_matched_plane_sampling.py
  - tools/analyze/build_salt2_pm5_holdout_admission.py
task: AGENT-486
date: 2026-07-17
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Salt2 PM5 Holdout Admission

## Result

Salt2 +/-5Q PM5 extraction is repaired for holdout diagnostics by reusing
AGENT-406 staged-copy artifacts. The package contains `6`
admission rows and `0` fit-admitted rows.

The rows are useful for holdout/onset diagnostics, but not for fitting or model
selection. Reverse flow remains high enough that F6 and Internal-Nu fits are not
admitted.

## Files

- `salt2_pm5_holdout_metrics.csv`
- `salt2_pm5_field_validation.csv`
- `salt2_pm5_admission_table.csv`
- `salt2_pm5_runtime_leakage_audit.csv`
- `salt2_pm5_repair_decision.csv`
- `salt2_pm5_reverse_fraction.svg`
- `salt2_pm5_ri.svg`
- `salt2_pm5_wall_core_delta_t.svg`
