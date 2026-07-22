---
provenance:
  - reports/2026-06/2026-06-02/2026-06-02_ethan_case_metadata_index/ethan_case_metadata_index.csv
  - work_products/2026-07/2026-07-09/2026-07-09_timeseries_steadystate/steady_state_summary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_thermal_boundary_patch_role_table/thermal_boundary_patch_role_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/steady_candidate_admission_triage.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/corrected_q_harvest_3295437_processing_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv
tags: [flow-rate, temperature, boundary-conditions, cfd-admission]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: AGENT-351
date: 2026-07-14
role: BC-modeling/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Flow Rate, Temperature, and Boundary-Condition Response Study

## Purpose

This package consolidates existing CFD evidence into one chart-first study of
how loop flow rate varies with temperature and boundary-condition choices. It
does not run OpenFOAM, mutate solver outputs, edit registry/admission state, or
change external Fluid code.

## Current Result

- Case response rows: `56`.
- Patch-role BC rows: `18`.
- Admitted/usable response rows with mdot: `3`.
- Invalid false-steady Q perturbation rows tracked: `14`.
- Corrected-Q terminal harvested but split-pending rows: `4`.
- Paper conclusion rows: `6`.

The strongest physically usable trend evidence today remains the mainline Salt
2/3/4 split rows. Diagnostic and historical rows are retained because they
explain which boundary conditions were attempted and why some apparent steady
results cannot be used as physical response data.

## Paper-Ready Interpretation

See `paper_ready_analysis.md` for methods/results prose, the admissible
observational trend statement, limitations, and paper-safe conclusions. The
mainline Salt2/Salt3/Salt4 trend is admissible as an observed monotonic ordering
only; it is not a controlled causal fit because temperature, heater power,
cooler power, and external boundary settings co-vary by case design.

## Boundary-Condition Semantics

Case-level setup fields come from the Ethan case metadata index. Patch-level
OpenFOAM boundary details come from the thermal boundary patch-role table.
Current CFD `rcExternalTemperature` includes emissivity/Tsur radiation inside
total `wallHeatFlux`; no separate exported `qr` term exists.

## Important Caveats

- Old Q perturbation rows are false-steady provenance only; their mdot did not
  move by the expected operating-point response.
- Corrected-Q +/-5 rows harvested by job `3295437` are terminal in that gate,
  and now linked to AGENT-353 heat-role reductions, but still need split-policy
  and operating-point gate updates before being treated as independent training
  or scoring rows.
- Rows with missing mdot or temperature aggregates stay in the tables with an
  explicit missing-result reason instead of being silently dropped.

## Files

- `case_bc_response_matrix.csv`
- `patch_role_bc_summary.csv`
- `flow_temperature_response_summary.csv`
- `trend_correlation_analysis.csv`
- `paper_conclusions.csv`
- `corrected_q_pm5_response_overlay.csv`
- `paper_ready_analysis.md`
- `invalid_or_diagnostic_runs.csv`
- `bc_semantics_and_assumptions.csv`
- `source_manifest.csv`
- `summary.json`
- `figures/*.svg`
