---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/corrected_q_harvest_3295437_processing_status.csv
  - work_products/2026-07/2026-07-14/2026-07-14_salt_cfd_training_evidence_inventory/recommended_salt_split.csv
  - work_products/2026-07/2026-07-14/2026-07-14_cfd_postprocess_admission_workflow_triage/README.md
tags: [cfd-pp, corrected-q, admission, forward-v1, split-discipline]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_split_admission_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_corrected_q_pm5_admission_split_processing/corrected_q_pm5_heat_role_reduction.csv
task: AGENT-353
date: 2026-07-14
role: cfd-pp/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# Corrected-Q +/-5Q Admission/Split Processing

## Purpose

This package implements the next completed-harvest slice of the forward-v1 plan.
It consumes the completed corrected-Q +/-5Q harvest `3295437` and registry
aggregates, then publishes split-aware admission/use artifacts without changing
registry state or native CFD outputs.

## Decision

The four +/-5Q rows are terminal-harvested and closure-fit admissible under the
current terminal gate, but they do **not** expand independent training,
validation, or holdout rows yet. They are perturbation-family evidence:

- Salt2 +/-5Q: train-family sensitivity/admission evidence pending a dated
  perturbation split policy.
- Salt4 +/-5Q: holdout-family sensitivity/admission evidence; not usable for
  model selection.

## Files

- `corrected_q_pm5_split_admission_matrix.csv`: terminal/admission status and
  split-safe allowed use.
- `corrected_q_pm5_heat_role_reduction.csv`: final-window heat-role reductions
  from read-only registry `wall_heat_flux_grouped.csv`.
- `corrected_q_pm5_forward_gate_queue.csv`: next gate actions for boundary/HX,
  F6, upcomer onset, and forward-v1.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No row is admitted as an independent training point by this package. Realized
CFD wallHeatFlux and cooler duty are diagnostic/score targets only, not runtime
predictive inputs. Radiation remains embedded in `rcExternalTemperature`
`wallHeatFlux`; no separate exported `qr` exists.

Summary: `4` harvested rows processed; independent
training expansion rows now: `0`.
