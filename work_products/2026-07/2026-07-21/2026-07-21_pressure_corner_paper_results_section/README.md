---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_comparison_matrix.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/pressure_corner_gate_review.csv
tags: [pressure-ledger, pressure-corner, publication-writing, section-effective]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_comparison_admission_review/README.md
task: TODO-PRESSURE-CORNER-PAPER-RESULTS-SECTION
date: 2026-07-21
role: Writer / Reviewer / Hydraulics
type: work_product
status: complete
---
# Pressure-Corner Paper Results Section

## Result

This package converts the frozen pressure-corner finding into paper-facing
methods, results, limitations, table-ledger, and caption text. The current
Salt2/Salt3/Salt4 lower-right corner rows remain `section_effective` pressure
diagnostics.

## Outputs

- `paper_results_section.md`
- `table_ready_claim_ledger.csv`
- `caption_text.md`
- `source_manifest.csv`
- `summary.json`

## Guardrails

The writing preserves the pressure-budget interpretation: gross static pressure
rise, hydrostatic dominated budget, signed available residual, and
section-effective pressure diagnostic. No coefficient admission, F6 fit, clipped
coefficient, hidden global multiplier, native-output mutation, registry change,
scheduler action, solver/postprocessing launch, Fluid edit, or external edit was
performed.
