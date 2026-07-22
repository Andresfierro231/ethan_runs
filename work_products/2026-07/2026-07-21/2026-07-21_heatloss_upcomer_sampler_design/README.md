---
task: TODO-HEATLOSS-UPCOMER-SAMPLER-DESIGN
date: 2026-07-21
role: Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [heat-loss, upcomer, sampler-design, exchange-cell, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest
---
# Heat-Loss Upcomer Sampler Design

This package implements Phase 1 of the heat-loss alignment sequence: a
design-only sampler contract for extracting upcomer exchange-state evidence.
It does not edit `tools/extract`, launch OpenFOAM, launch a sampler, or admit a
model.

## Decision

- Output schema rows: `17`
- Algorithm stages: `9`
- Dry-run rows: `51`
- Execution case windows: `3`
- Sampler launched: `false`
- Extractor edited: `false`
- Fit or score allowed now: `false`

## Outputs

- `sampler_output_schema.csv`: required output fields, units, source fields,
  method contracts, missing behavior, and runtime/admission policy.
- `algorithm_contract.csv`: implementation stages from case/window lock through
  same-QOI UQ hook and admission guard.
- `dry_run_emission_matrix.csv`: salt 2/3/4 by output-field dry-run ledger.
- `future_implementation_change_list.csv`: exact future extractor changes for
  the next row.
- `execution_preflight_cases.csv`: compute-node execution queue and command
  templates for the later execution row.
- `validation_cases.csv`: required tests and fail-closed behavior.
- `source_manifest.csv`: read-only provenance.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repositories, `tools/extract`, generated indexes, or
blocker register were mutated. No solver, postprocessor, sampler, fitting,
model selection, closure admission, or scorecard trigger was run. Heat residual
remains separate from internal Nu.
