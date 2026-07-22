---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_conservative_thermal_ledger_residual_owner_contract/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
tags: [predictive-1d, uncertainty, setup-only, runtime-leakage, no-admission]
related:
  - .agent/status/2026-07-22_TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22.md
  - .agent/journal/2026-07-22/1d-setup-only-bc-uq-propagation.md
  - imports/2026-07-22_1d_setup_only_bc_uq_propagation.json
task: TODO-1D-SETUP-ONLY-BC-UQ-PROPAGATION-2026-07-22
date: 2026-07-22
role: Uncertainty / Forward-pred / Thermal-modeling / Hydraulics / Tester / Writer
type: work_product
status: complete
---
# 1D Setup-Only BC UQ Propagation Contract

Generated: `2026-07-22T14:37:05.336117+00:00`

Decision: `setup_only_uq_contract_ready_no_compute_no_publication_interval`.

This package defines the setup-only uncertainty propagation plan for the 1D
model. It is a runbook and screening-prior contract, not a completed UQ
calculation and not a publication interval.

## Scope

The contract covers heater source fraction, cooler/HX strength, ambient and
radiation fields, external convection, wall/layer materials, fluid property
mode, pressure-loss terms, and TP/TW sensor projection. All ranges are marked as
screening priors unless a later release row admits tighter source-specific
intervals.

## Files

- `uncertainty_source_table.csv`: 9 setup-only UQ sources and ranges.
- `propagation_plan.csv`: 5 phased propagation stages.
- `lightweight_sensitivity_matrix.csv`: 9 expected QOI pathways.
- `protected_row_guardrails.csv`: 9 leakage and split guardrails.
- `readiness_gate.csv`: 6 execution/admission gates.
- `source_manifest.csv`, `no_mutation_guardrails.csv`, `summary.json`.

## Scientific Use

Use this to design train-only smoke/UQ runs and to document what must remain
fixed before protected validation/holdout/external scoring. Do not cite the
screening ranges as final uncertainty intervals.

## Guardrails

No solver, sampler, scheduler job, Fluid edit, external thesis/LaTeX edit,
registry/admission mutation, source/property release, protected scoring,
fitting, model selection, or blocker-register change was performed.
