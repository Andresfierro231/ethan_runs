---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/component_repair_targets.csv
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_contract/future_extractor_schema.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv
tags: [pressure-ledger, two-tap, component-k, extractor]
related:
  - .agent/status/2026-07-17_AGENT-530.md
  - .agent/journal/2026-07-17/two-tap-component-repair-extractor.md
task: AGENT-530
date: 2026-07-17
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Repair Extractor

Generated: `2026-07-17T21:44:36+00:00`

## Decision

The extractor emits the AGENT-525 future schema for the three current
`corner_lower_right` targets from existing preserved/staged evidence only.
All rows remain diagnostic because raw endpoint pressures, final bases,
same-window recirculation metrics, component isolation, and same-QOI uncertainty
are still missing or failing.

## Outputs

- `two_tap_component_repair_output.csv`
- `extractor_gate_results.csv`
- `next_raw_postprocessing_queue.csv`
- `extractor_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Extractor rows: `3`.
- Ordinary admitted rows: `0`.
- Missing endpoint-pressure rows: `3`.
- Negative current `K_local` rows: `3`.
- Failed gate rows: `15`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, or active-agent scoped artifacts were mutated.
Blank endpoint-pressure, RAF/RMF/SVF, and uncertainty fields are intentional:
they are blockers, not values to infer.
