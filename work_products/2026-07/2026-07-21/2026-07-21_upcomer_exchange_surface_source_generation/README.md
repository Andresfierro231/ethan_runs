---
task: TODO-UPCOMER-EXCHANGE-SURFACE-SOURCE-GENERATION-2026-07-21
date: 2026-07-21
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete
tags: [upcomer, exchange-cell, surface-generation, source-ledger, no-solver]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_input_generation
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_source_field_audit
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design
---
# Upcomer Exchange Surface/Source Generation

This package advances the post-volume input lanes for the upcomer exchange
sampler. It parses the static `0/T` boundary-condition `Q` terms into explicit
source/sink lanes and emits a fail-closed surface extraction contract for the
cell, exchange-interface, and wall/core VTKs.

## Decision

- case windows: `3`
- surface/input contract rows: `15`
- static source/sink rows: `21`
- source/sink summary rows: `3`
- ready static source/sink summaries: `3/3`
- scheduler action: `false`
- OpenFOAM launch: `false`
- fit/score/admission allowed now: `false`

No surface sampling was launched because the exchange interface and wall/core
band are not defined by an approved source. The generated sbatch wrapper exits
before OpenFOAM work until a later row supplies those geometry contracts.

## Outputs

- `surface_extraction_contract.csv`: per-case ready/blocked input lanes.
- `source_sink_static_ledger.csv`: parsed constant `Q` source/sink entries from
  `0/T`.
- `source_sink_summary.csv`: per-case `Q_source_W`, `Q_sink_W`, and net static
  boundary source/sink accounting.
- `submission_decision.csv`: fail-closed scheduler decision.
- `scripts/`: preflight-only runner and sbatch wrapper.
- `no_mutation_guardrails.csv`, `next_agent_handoff.csv`, `source_manifest.csv`.

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, Fluid source, external
repository, blocker register, generated docs index, fit, score, model selection,
exchange-cell admission, Phase 4B rescore, Phase 5/S6 trigger, or internal-Nu
residual absorption is changed by this package.
