---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/recirc_pressure_basis_table.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/current_corner_lower_right_recirc_rows.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_recirc_section_effective_model/paper_claims_and_limitations.csv
tags: [paper-results, pressure-ledger, two-tap, recirculation]
task: TODO-TWO-TAP-RECIRC-SECTION-EFFECTIVE-MODEL
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: paper-results-note
status: complete
---
# Paper Results Note: Current Two-Tap Recirculation Evidence

## Result

The current Salt2/Salt3/Salt4 `corner_lower_right` endpoint rows are complete
enough to explain the blocker and choose the next model form, but they are not
complete enough to admit a coefficient. All current rows fail ordinary
reverse-flow gates, remain `apparent_cluster_only` for component isolation, and
lack same-label/same-formula/same-sign mesh/time UQ.

## Scientific Interpretation

The static pressure drops are large, but those drops track the hydrostatic
correction. The `p_rgh` differences are small and negative under the preserved
downstream-minus-upstream sign convention. This is exactly why a static
apparent `K` is not a buoyancy-corrected local component coefficient.

The recirculation metrics are material, not marginal: the current rows have
aggregate reverse area fraction near `0.763` and aggregate reverse mass fraction
near `0.500`. Those values place the evidence in the recirculating
section-effective lane.

## What The Paper Can Say

- Current two-tap data provide diagnostic evidence for pressure-basis,
  recirculation, and model-form selection.
- Ordinary `component_K` and F6 promotion remain blocked.
- The next model should use a named section-effective recirculation pressure
  residual, scored separately from ordinary straight-pipe and component losses.
- A non-recirculating anchor and same-QOI UQ family are still required before
  ordinary component `K` can be revisited.

## What The Paper Must Not Say

- Do not say the static apparent `K` is locally buoyancy-corrected.
- Do not say the current rows isolate clean component K.
- Do not say same-QOI UQ has been supplied.
- Do not collapse recirculation into a hidden global multiplier.

Generated package row count: `3` current rows;
paper claim rows: `4`.
