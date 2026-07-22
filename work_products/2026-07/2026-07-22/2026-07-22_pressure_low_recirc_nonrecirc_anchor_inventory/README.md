---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_non_upcomer_branch_modeling_analysis/non_upcomer_f6_candidate_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_endpoint_raw_face_sampler/ordinary_flow_gate.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json
tags: [pressure, f6, nonrecirculating-anchor, section-effective, no-admission]
related:
  - .agent/status/2026-07-22_TODO-PRESSURE-LOW-RECIRC-NONRECIRC-ANCHOR-INVENTORY-2026-07-22.md
  - .agent/journal/2026-07-22/pressure-low-recirc-nonrecirc-anchor-inventory.md
  - imports/2026-07-22_pressure_low_recirc_nonrecirc_anchor_inventory.json
task: TODO-PRESSURE-LOW-RECIRC-NONRECIRC-ANCHOR-INVENTORY-2026-07-22
date: 2026-07-22
role: Hydraulics/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
---
# Pressure Low-Recirculation / Nonrecirculating Anchor Inventory

Decision: `pressure_anchor_inventory_ready_no_f6_revisit_yet`.

This package advances the pressure unblock by ranking admissible-anchor
requirements before any F3/F6/Shah comparison. It preserves lower-right two-tap
pressure as section-effective residual evidence only.

Key counts:

- candidate rows reviewed: `36`
- preferred future ordinary anchor rows: `6`
- sampled endpoint ordinary-flow pass rows: `0`
- F6 fit-ready rows now: `0`
- lower-right section-effective rows preserved: `3`

Primary outputs:

- `anchor_inventory_gate.csv`
- `sampled_endpoint_ordinary_flow_gate.csv`
- `f3_f6_shah_revisit_gate.csv`
- `next_unblock_queue.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
- `summary.json`

No scheduler action, sampler/harvest/UQ launch, native-output mutation, fitting,
component-K admission, F6 admission, clipped K, hidden multiplier, or F3/F6/Shah
numeric comparison occurred.
