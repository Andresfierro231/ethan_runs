---
provenance:
  created_by: codex
  date: 2026-07-21
tags: [thesis, pressure, F6, gate-waterfall, figure-table-package]
related:
  - .agent/BOARD.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_same_qoi_uq_and_admission_gate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/README.md
---

# S10 Pressure/F6 Gate Waterfall Figure-Table Package

This package converts existing pressure-corner, F6, and same-QOI gate evidence into thesis-ready table inputs. It is a documentation and figure/table-source package only.

## Outputs

- `pressure_f6_gate_waterfall.csv`: ordered gate rows for pressure-corner and F6 evidence.
- `f3_shah_apparent_comparison_table.csv`: F3 comparison status; currently not evaluated because no ordinary admissible F6 candidate exists.
- `claim_boundary_ledger.csv`: explicit non-admission and no-value-publication ledger.
- `caption_bank.md`: thesis-safe captions for the figure/table package.
- `source_manifest.csv`: read-only source evidence list.
- `summary.json`: package counts and guardrail flags.

## Result

The rigorous result is zero admitted pressure-loss rows. Existing evidence can support diagnostic pressure/F6 limitation narrative and next-evidence ordering, but it cannot publish component K, cluster K, clipped K, F6 fit, or hidden multiplier values.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state, Fluid/external source, generated indexes, thesis chapters, or figure assets were modified.
