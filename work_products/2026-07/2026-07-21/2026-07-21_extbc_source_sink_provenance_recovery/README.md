---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_fj_parallel_diagnostics/phase_i_source_sink_admissibility/source_sink_admissibility_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_salt1_train_external_bc_recovery_freeze_gate/document_only_source_sink_rows.csv
  - jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/runs/salt1_jin_nominal_continuation_corrected/case_stage/viscosity_screening_salt_test_1_jin_coarse_mesh_continuation/0/T
  - jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt2_jin/case_stage/viscosity_screening_salt_test_2_jin_coarse_mesh_continuation/0/T
tags: [external-bc, source-sink, provenance, runtime-leakage]
related:
  - .agent/status/2026-07-21_TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21.md
  - .agent/journal/2026-07-21/extbc-source-sink-provenance-recovery.md
task: TODO-EXTBC-SOURCE-SINK-PROVENANCE-RECOVERY-2026-07-21
date: 2026-07-21
role: Forward-pred / Thermal-modeling / Writer / Reviewer
type: work_product
status: complete
---
# External-BC Source/Sink Provenance Recovery

This package separates setup-side source/sink provenance from realized CFD
diagnostics for heater, cooler, and test-section rows.

## Result

- Reviewed `12` primary source/sink rows across Salt1-Salt4.
- Recovered setup-side imposed `Q` provenance for lower-leg heater, cooling
  branch cooler, and upcomer test-section rows from staged `0/T` files.
- Reclassified provenance basis from `forbidden_realized_cfd_only` to
  `setup_known_candidate` for those rows.
- Runtime use remains blocked: `0` source/sink rows are admitted as predictive
  runtime inputs until a source-model API and split/source-property gate release
  them.

## Outputs

- `setup_source_sink_provenance_ledger.csv`
- `reclassification_decision.csv`
- `runtime_leakage_audit.csv`
- `next_use_gate.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repository, blocker register, generated docs index, thesis
body, fitting/model selection, freeze/admission, or final score changed.
Realized `wallHeatFlux`, CFD mdot, validation/holdout temperatures, and heat
residual fills remain forbidden runtime inputs.
