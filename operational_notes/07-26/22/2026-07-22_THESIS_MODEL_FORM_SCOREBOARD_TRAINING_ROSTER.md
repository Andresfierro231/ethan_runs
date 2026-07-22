---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/README.md
tags: [operational-note, thesis, model-form-scoreboard, training-roster]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/README.md
task: TODO-THESIS-MODEL-FORM-SCOREBOARD-TRAINING-ROSTER-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Hydraulics / Implementer / Tester / Writer / Reviewer
type: operational_note
status: complete
---
# Thesis Model-Form Scoreboard Training Roster

Open first:

- `work_products/2026-07/2026-07-22/2026-07-22_thesis_model_form_scoreboard_training_roster/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/README.md`
- `model_form_training_roster.csv`
- `canonical_train_validation_holdout_plan.csv`
- `trainability_gate.csv`
- `next_training_sequence.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/cfd_run_qoi_split_chart_wide.csv`

Why this exists:

The next modeling phase should train key 1D forms on Salt1-4 nominal rows and
later test validation/holdout/external rows. This note and package make that
sequence explicit without relaxing leakage guardrails or rewriting the completed
master scoreboard.

Update on protected test terminology:

`val_salt2` is now carried inside the `holdout_test` bucket with
`split_subrole=external_test` in the CFD QoI split chart. This gives the thesis
one protected test set while preserving the external-test provenance and the
no-fit/no-model-selection restrictions.

Trusted packages:

- master scoreboard:
  `work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/`
- MF16 source/property release candidate:
  `work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/`
- MF17 same-QOI wall/core exchange UQ:
  `work_products/2026-07/2026-07-22/2026-07-22_mf17_same_qoi_wall_core_exchange_uq_execution/`
- MF07/MF08/MF10 development and signed wall-flux gates:
  `work_products/2026-07/2026-07-22/2026-07-22_mf07_entrance_development_and_reset_source_basis/`,
  `work_products/2026-07/2026-07-22/2026-07-22_mf08_signed_wall_flux_developing_thermal_branches/`,
  `work_products/2026-07/2026-07-22/2026-07-22_mf10_entrance_wallflux_train_only_variant_bakeoff/`
- CFD run/QoI split chart:
  `work_products/2026-07/2026-07-22/2026-07-22_thesis_cfd_run_qoi_split_chart/`

Next task sequence:

1. Close the active 1D train-only setup-UQ smoke execution.
2. Repair or reaffirm fail-closed source/property exact-field release.
3. Predeclare a small Salt1-4 nominal training set: M0, M3, MF12, MF15/M5,
   and MF07/MF08/MF10 only if source gates open.
4. Train on Salt1-4 nominal rows only.
5. Freeze exactly one runtime-legal candidate before reading validation,
   holdout, or external-test targets.
6. Score support/validation, holdout, and external-test rows separately and
   do not change coefficients afterward.

Do not do:

- Do not treat legacy Salt3/Salt4 transfer rows as validation after training on
  Salt1-4 nominal.
- Do not use CFD mdot, realized wallHeatFlux, scored-row TP/TW temperatures,
  imposed post-solve cooler duty, or residual fills as runtime inputs.
- Do not admit D1-D4 empirical bias corrections as final physics. Use them as
  mechanism hypotheses for source-bounded MF12/MF15 forms.
- Do not hide residuals by relabeling empirical offsets/multipliers as physics.
  If D1-D4 or similar cases are discussed in the thesis, label them as
  diagnostic residual-hiding/negative evidence and pair them with the physical
  discrepancy studies they motivated.
