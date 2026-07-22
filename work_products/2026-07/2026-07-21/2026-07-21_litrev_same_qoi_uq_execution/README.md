---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/cfd_postprocessing_schema_gap_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/residual_uq_progress.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/endpoint_pair_selection.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/endpoint_face_sampling_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_same_qoi_uq_preflight/pm10_uq_gate.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_mesh_gate/thermal_mesh_gate_qois.csv
  - work_products/2026-07/2026-07-15/2026-07-15_thermal_row_admission_ledger/thermal_row_admission_ledger.csv
tags: [same-qoi-uq, cfd-pp, pressure, f6, thermal, recirculation]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/pressure_corner_methods_note.md
task: TODO-LITREV-SAME-QOI-UQ-EXECUTION
date: 2026-07-21
role: cfd-pp/Hydraulics/Thermal-modeling/Tester/Writer
type: work_product
status: complete
---
# Same-QOI UQ Execution

This package executes the same-QOI uncertainty lane from existing artifacts. It
does not launch solvers, samplers, fit routines, or scheduler jobs.

## Result

- Admission table rows: 83
- Gap queue rows: 83
- Newly admitted rows: 0
- Component-K, cluster-K, F6-fit, clipped-K, and package-applied global-multiplier rows: 0

Rows lacking neighboring windows, same-QOI GCI, raw sampler output, or thermal
sign/policy support remain blocked or diagnostic. The pressure-increasing
corner rows remain `section_effective`/diagnostic pressure-recovery evidence,
not negative loss and not coefficient admission.

## Files

- `same_qoi_uq_admission_table.csv`: canonical row-level gate table across
  pressure delta, section/component-K candidates, F6 endpoints, PM10
  recirculation metrics, HTC/Nu, and heat-loss rows.
- `uq_gap_queue.csv`: next evidence queue for rows still blocked by missing
  neighboring windows, GCI, sampler output, sign review, or policy gates.
- `same_qoi_uq_summary_by_family.csv`: row counts and blocked/diagnostic counts
  by source family.
- `source_manifest.csv`: exact read-only source artifacts with hashes.
- `summary.json`: machine-readable counts and guardrail summary.

## Guardrails

No coefficient is admitted from this task. No clipped K, F6 fit, or hidden
multiplier is applied. Thermal setup candidates remain candidates only under
their existing ledgers; this package only records their same-QOI UQ status.
