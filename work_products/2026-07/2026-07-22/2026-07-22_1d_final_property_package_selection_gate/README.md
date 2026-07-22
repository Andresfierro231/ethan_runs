---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_evidence_packet_source_property_release_atlas/source_property_release_atlas.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/field_release_contract.csv
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/nominal_train_release_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/exact_field_release_matrix.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_regime_map_nondimensional_closure_eligibility/formula_validity_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_train_only_setup_uq_smoke_terminal_harvest_and_validator/sensitivity_family_summary.csv
tags: [property-package, source-property, cp, viscosity, nondimensional-gates]
related:
  - .agent/status/2026-07-22_TODO-1D-FINAL-PROPERTY-PACKAGE-SELECTION-GATE-2026-07-22.md
  - .agent/journal/2026-07-22/1d-final-property-package-selection-gate.md
  - imports/2026-07-22_1d_final_property_package_selection_gate.json
task: TODO-1D-FINAL-PROPERTY-PACKAGE-SELECTION-GATE-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Forward-pred / Writer / Reviewer / Tester
type: work_product
status: complete
---
# 1D Final Property-Package Selection Gate

Decision: `property_package_selection_sensitivity_only_no_release_no_freeze`.

The current best property-package label for Salt1-Salt4 nominal rows remains
`jin_viscosity_parida_cp_santini_k`, but it is not released as a final
predictive property package. Existing source/property evidence has complete
labels for the four nominal rows, yet release-ready rows remain `0/4`, MF16
exact-field release-ready rows remain `0`, and `cp_J_kg_K` plus viscosity basis
are still documented as required but not release-ready.

## What Is Admitted Now

Only the bookkeeping/provenance layer is admitted:

- property family label;
- nondimensional-coordinate definitions;
- sensitivity-only use in train/support diagnostics;
- release blockers and next gates.

No final property package, coefficient, source-property value, candidate freeze,
protected score, or final score is emitted.

## Current Technical Position

Use the Jin viscosity / Parida cp / Santini k family as the default named
candidate in future train-only design packets because it is the established
label in the nominal-train audit. Treat all propagated effects as sensitivity
or eligibility coordinates until candidate-specific source/property release
passes:

- `Re = rho U D_h / mu` is blocked by property mode and velocity-basis release.
- `Pr = cp mu / k` is blocked by cp/mu/k release.
- `Gr`, `Ra`, and `Ri` are blocked by beta, viscosity, wall-bulk drive, and
  orientation/source provenance.
- `Gz = Re Pr D_h / x_reset` is blocked by Re/Pr release and thermal reset
  labels.
- storage and heat-loss residual terms need cp and mass/volume ownership before
  they can become predictive energy terms.

## Outputs

- `property_package_gate.csv`
- `property_effect_propagation.csv`
- `freeze_margin_flags.csv`
- `next_unblock_sequence.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No native CFD/OpenFOAM output, registry, scheduler, Fluid source, external repo,
protected target, or thesis body file was mutated.
