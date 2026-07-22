---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_final_property_package_selection_gate/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_final_property_package_selection_gate/property_package_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_strict_row_specific_source_envelope_recovery/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf12_bulk_to_tp_formula_gate/candidate_bulk_to_tp_formulas.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/model_form_training_roster.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/field_release_contract.csv
tags: [property-sensitivity, cp, viscosity, thermal-conductivity, train-support, source-envelope]
related:
  - .agent/status/2026-07-22_TODO-CANDIDATE-CP-MU-K-TRAIN-SUPPORT-SENSITIVITY-PREFLIGHT-2026-07-22.md
  - .agent/journal/2026-07-22/candidate-cp-mu-k-train-support-sensitivity-preflight.md
  - imports/2026-07-22_candidate_cp_mu_k_train_support_sensitivity_preflight.json
task: TODO-CANDIDATE-CP-MU-K-TRAIN-SUPPORT-SENSITIVITY-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Candidate cp/mu/k Train/Support Sensitivity Preflight

Decision: `cp_mu_k_sensitivity_preflight_complete_fail_closed_no_release`.

This package executes the requested candidate-specific property sensitivity
unlock as a strict preflight. It does not fit, score, freeze, release a property
package, or touch protected rows. The selected candidate family is
`MF12_signed_source_memory_bulk_to_TP` paired with the current named property
family `jin_viscosity_parida_cp_santini_k`.

## Result

The algebraic sensitivity contract is ready for train/support diagnostics, but
model execution and candidate freeze remain blocked. The strict source-envelope
repair package still reports `0` strict-pass rows, `0` source/property release
rows, and `0` S13+MF12 admission rows. CAND001 pressure endpoint readiness also
remains gated because job `3308712` is still running under the monitor lane.

## Sensitivity Basis

For fixed geometry and a fixed flow/velocity basis:

- `Re` scales as `1 / mu`;
- `Pr` scales as `cp * mu / k`;
- `Gz` scales as `Re * Pr * D_h / x_reset`, so the simple fixed-flow product
  scales as `cp / k`;
- source-temperature rise from a released source integral scales as
  `1 / (mdot * cp)`;
- wall/layer conduction resistance scales as `1 / k`.

Those relationships are sufficient to define candidate-specific sensitivity
lanes before any protected scoring. They are not sufficient to release numeric
property values, source terms, or coefficients.

## Outputs

- `candidate_property_sensitivity_contract.csv`
- `train_support_case_matrix.csv`
- `property_perturbation_grid.csv`
- `qoi_propagation_targets.csv`
- `execution_readiness_gate.csv`
- `source_envelope_repair_status.csv`
- `pressure_endpoint_dependency.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repo, protected target, source/property release state,
candidate-freeze state, or thesis body file was mutated.
