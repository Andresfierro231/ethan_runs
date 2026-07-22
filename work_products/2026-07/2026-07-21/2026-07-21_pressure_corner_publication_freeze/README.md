---
task: TODO-PRESSURE-CORNER-PUBLICATION-FREEZE-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Tester / Writer
type: work_product
status: complete
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_corner_basis_recovery/pressure_corner_basis_recovery_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/pressure_corner_extraction_findings.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
tags: [pressure-ledger, pressure-corner, publication-freeze, section-effective]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - .agent/status/2026-07-21_TODO-PRESSURE-CORNER-PUBLICATION-FREEZE-2026-07-21.md
  - .agent/journal/2026-07-21/pressure-corner-publication-freeze.md
---
# Pressure-Corner Publication Freeze

## Result

This package freezes the July 21 pressure-corner finding for comparison and
publication writing. The current Salt2/Salt3/Salt4 `corner_lower_right` endpoint
pairs are all labeled `section_effective`.

Gross static pressure rises across the endpoint pair, but the rise is hydrostatic
dominated. After hydrostatic and kinetic correction, the signed available
residual is small and negative. That residual is preserved as pressure-recovery /
recirculating-section diagnostic evidence, not clipped into a loss and not
admitted as component `K` or F6.

## Outputs

- `canonical_pressure_corner_result.csv`
- `pressure_corner_figure_data.csv`
- `pressure_corner_publication_claims.csv`
- `pressure_corner_methods_note.md`
- `source_manifest.csv`
- `summary.json`

## Counts

- Frozen rows: `3`
- Label counts: `{'section_effective': 3}`
- Component-K admitted rows: `0`
- F6 fit rows: `0`
- Clipped-K rows: `0`
- Global multiplier rows: `0`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repo file, F6 fit, component-K admission, hidden global
multiplier, or clipped K is introduced by this package.
