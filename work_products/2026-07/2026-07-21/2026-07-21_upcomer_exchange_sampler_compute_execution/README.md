---
task: TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, sampler, compute-gate]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design
---
# Upcomer Exchange-Cell Compute-Execution Gate

This package implements the next rigorous gate after the dry exchange-cell
sampler design. It inventories the queued Salt2/Salt3/Salt4 source windows,
checks field readiness, writes a future compute-node scaffold, and records why
the sampler was not submitted by this row.

## Decision

- queued windows: `3`
- primary-field-ready windows: `3`
- blocking diagnostic gap: `['cellVolume']`
- scheduler action: `false`
- sampler/postprocessing launched: `false`
- fit/admission changed: `false`

The primary reconstructed fields are present for all queued windows, but the
exchange-cell row cannot be assembled with the current VTK path because
`cellVolume` is absent. `mu` remains optional and should emit an unavailable
status for `R_mu`; the recirculation mask can fall back to `U dot n`; wall
heat-flux evidence is diagnostic/support-only and must be generated only in a
task-owned staged case on a compute node.

## Outputs

- `source_case_readiness.csv`: Salt2/Salt3/Salt4 field and diagnostic readiness.
- `required_field_gap.csv`: per-case source/derived field gaps tied to output QOIs.
- `compute_submission_decision.csv`: explicit no-submit decision and release condition.
- `execution_script_plan.csv`: generated script inventory.
- `scripts/`: future no-submit scaffold that exits before OpenFOAM work.
- `next_agent_handoff.csv`: ordered continuation tasks.
- `no_mutation_guardrails.csv`: side-effect and admission guardrails.
- `source_manifest.csv`: read-only context and changed artifacts.

## Guardrails

No native CFD/OpenFOAM output, staged source case, registry/admission state,
scheduler state, Fluid source, external repository, blocker register, or
generated docs index was mutated. No solver, OpenFOAM postprocessor, sampler,
fitting, model selection, ordinary upcomer closure admission, component-K
admission, pressure residual absorption, energy residual absorption, Phase 4B
rescore, Phase 5, or S6 trigger was run.
