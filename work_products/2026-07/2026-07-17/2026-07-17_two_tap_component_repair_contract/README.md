---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_named_pressure_extraction_readiness/named_pressure_readiness.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/component_cluster_k_recomputed_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_pressure_evidence_corner_k_diagnosis/corner_k_gate_matrix.csv
tags: [pressure-ledger, two-tap, component-k, extraction-contract]
related:
  - .agent/status/2026-07-17_AGENT-525.md
  - .agent/journal/2026-07-17/two-tap-component-repair-contract.md
task: AGENT-525
date: 2026-07-17
role: Hydraulics/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Component Repair Contract

Generated: `2026-07-17T21:31:29+00:00`

## Decision

This package implements the first AGENT-523 queue item as a future extraction
contract. It does not admit any component K row.

## Outputs

- `component_repair_targets.csv`
- `repair_field_contract.csv`
- `future_extractor_schema.csv`
- `acceptance_gate_matrix.csv`
- `repair_contract_summary.csv`
- `source_manifest.csv`
- `summary.json`

## Counts

- Component/cluster target rows: `3`.
- Ordinary admitted rows now: `0`.
- Required field rows: `7`.
- Acceptance gates: `5`.

## Guardrails

No native CFD outputs, registry/admission state, scheduler state, external Fluid
files, generated index files, or active-agent scoped artifacts were mutated. The
contract forbids universal K, hidden global friction multipliers, clipping
negative K, and ordinary pressure coefficients from reverse-flow sections.
