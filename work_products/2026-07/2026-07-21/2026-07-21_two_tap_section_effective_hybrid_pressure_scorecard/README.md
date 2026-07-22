---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_throughflow_recirc_exchange_cell/residual_equation_contract.md
tags: [pressure-ledger, two-tap, section-effective, hybrid-pressure, thesis]
related:
  - .agent/status/2026-07-21_TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21.md
  - .agent/journal/2026-07-21/two-tap-section-effective-hybrid-pressure-scorecard.md
  - imports/2026-07-21_two_tap_section_effective_hybrid_pressure_scorecard.json
task: TODO-TWO-TAP-SECTION-EFFECTIVE-HYBRID-PRESSURE-SCORECARD-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Section-Effective Hybrid Pressure Scorecard

## Result

This package converts the existing `corner_lower_right` pressure evidence into a
thesis-safe section-effective hybrid pressure scorecard. It does not admit a
component `K`, F6 correction, or predictive pressure closure.

Rows scored: `3`. Component-K rows admitted: `0`. F6 fit
rows: `0`. Clipped-K rows: `0`. Hidden/global multiplier rows: `0`.

## Interpretation

The gross static pressure rise is hydrostatic dominated. After hydrostatic and
kinetic correction, the available signed residual is small and negative:
Salt2 `-1.25366731683 Pa`, Salt3 `-1.84957005859 Pa`,
and Salt4 `-1.67833900273 Pa`.

The named hybrid term is `Delta_p_recirc_section`. The Salt2-frozen diagnostic
transfer check applies Salt2 `K_eff_recirc` to Salt3/Salt4 without refitting.
This is useful thesis quantification, not model admission.

## Outputs

- `section_effective_pressure_scorecard.csv`
- `hybrid_pressure_term_contract.csv`
- `three_level_score.csv`
- `thesis_claim_ledger.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native CFD/OpenFOAM output, registry/admission state, scheduler state, Fluid
source, external repo, validation/holdout/external scoring, fitting, model
selection, component-K/F6 admission, clipped K, hidden/global multiplier, S11,
S15, S6, blocker register, generated index, thesis current file, or internal-Nu
residual absorption is changed by this package.
