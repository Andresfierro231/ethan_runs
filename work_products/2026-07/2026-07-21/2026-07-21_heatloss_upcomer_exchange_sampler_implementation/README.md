---
task: TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, recirculation, exchange-cell, sampler-design, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction
---
# Upcomer Exchange-Cell Sampler Design

This package implements the dry sampler-design step for the throughflow plus
recirculation/exchange-cell path. It defines the output schema and validates the
calculation kernels with synthetic fixtures, but it does not run OpenFOAM or
sample native CFD fields.

## Decision

- required schema fields: `10`
- dry case/time plan rows: `3`
- fixture validation rows: `2`
- compute execution allowed from this row: `false`
- fit/admission/scorecard allowed now: `false`

The next row may use the schema for compute-node extraction, but only after
claiming a separate scheduler/execution scope.

## Outputs

- `exchange_sampler_required_schema.csv`: field names, units, bases, and
  unavailable-field policies.
- `exchange_sampler_dry_extraction_plan.csv`: salt 2/3/4 queued windows and
  required schema.
- `fixture_validation_rows.csv`: dry package validation rows.
- `no_launch_guardrails.csv`: side-effect and admission guardrails.
- `next_agent_handoff.csv`: ordered follow-on work.
- `source_manifest.csv`: provenance and mutation flags.

## Guardrails

No native CFD/OpenFOAM output, case directory, registry/admission state,
scheduler state, Fluid source, external repository, blocker register, or
generated docs index was mutated. No solver, postprocessor, sampler execution,
fitting, model selection, closure admission, Phase 4B rescore, or Phase 5/S6
scorecard trigger was run.
