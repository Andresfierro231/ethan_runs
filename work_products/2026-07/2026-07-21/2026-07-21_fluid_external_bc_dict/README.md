---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/external_bc_dictionary_contract.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/external_bc_segment_role_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/fluid_handoff_contract.csv
tags: [thermal-modeling, external-boundary, fluid, runtime-contract]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTERNAL-BC-DICT.md
  - .agent/journal/2026-07-21/fluid-external-bc-dict.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
task: TODO-FLUID-EXTERNAL-BC-DICT
date: 2026-07-21
role: Implementer/Tester/Writer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Fluid External Boundary Dictionary Contract

## Decision

This package releases the repo-local Fluid external-boundary dictionary
contract. It provides the schema, runtime dictionary rows, allowed modes,
validation cases, handoff stubs, and leakage audit needed before external Fluid
source can be edited under a separate row.

## Results

- Runtime dictionary rows: `24`.
- Predictive passive external rows: `15`.
- Document-only source/sink rows: `9`.
- Validation cases: `5`.
- External Fluid files edited: `False`.

## Outputs

- `fluid_external_boundary_schema.csv`
- `fluid_external_boundary_runtime_dictionary.csv`
- `allowed_runtime_mode_table.csv`
- `validation_cases.csv`
- `fluid_handoff_stubs.csv`
- `runtime_leakage_audit.csv`
- Legacy-compatible aliases: `external_bc_runtime_field_contract.csv`,
  `external_bc_representative_dictionary_rows.csv`,
  `external_bc_mode_policy.csv`, `external_bc_validation_cases.csv`, and
  `fluid_api_handoff_stubs.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Predictive mode excludes forbidden realized heat flux, CFD `mdot`, and imposed
forbidden cooler duty. Predictive mode also excludes forbidden validation
temperatures and forbidden residual-derived field fills. Replay total heat and
predictive radiation/convection are mutually exclusive.
