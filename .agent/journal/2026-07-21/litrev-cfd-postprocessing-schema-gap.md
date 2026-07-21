---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - reports/2026-07/2026-07-20/2026-07-20_cfd_postprocessing_readiness_refresh/README.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/README.md
  - work_products/2026-07/2026-07-08/2026-07-08_patchwise_heat_ledger_enthalpy_interfaces/README.md
tags: [cfd-postprocessing, schema-gap, pressure, heat-loss, uncertainty]
related:
  - .agent/status/2026-07-21_TODO-LITREV-CFD-POSTPROCESSING-SCHEMA-GAP.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/README.md
task: TODO-LITREV-CFD-POSTPROCESSING-SCHEMA-GAP
date: 2026-07-21
role: cfd-pp/Tester/Writer
type: journal
status: complete
---
# LitRev CFD Postprocessing Schema Gap

## Attempted

Claimed the open LitRev CFD schema-gap row and compared the July 21
`cfd_postprocessing_contract.csv` against existing pressure, heat-audit,
two-tap, F6 same-QOI, thermal, corrected-Q, and high-heat monitor packages.

## Observed

- The LitRev contract has 18 required rows.
- Pressure station maps and two-tap endpoint rows already preserve many basis
  terms: static pressure, `p_rgh`, hydrostatic correction, kinetic correction,
  velocity basis, and diagnostic section/apparent K values.
- Pressure coefficient admission remains closed: pressure-ladder review still
  reports 66/66 branch rows blocked and zero true `f_D` or component `K`
  admitted.
- Two-tap lower-right corner rows carry RAF/RMF/SVF recirculation metrics and
  fail the ordinary recirculation gate.
- Thermal ledgers carry bulk enthalpy, wall flux, wall temperature, internal
  HTC, and network terms for Salt2-4 mainline, but internal Nu fit-admitted rows
  remain zero.
- Heat-loss ledgers separate heater, cooler, passive, junction/stub, and
  residual terms, but storage is not directly measured, radiation is not
  separated without `qr`, and junction/stub heat is aggregate.
- General time-window UQ exists, but same-QOI endpoint UQ is not admitted:
  F6 preflight has zero same-QOI time-UQ pass rows and mesh spread is diagnostic.
- The current corrected-Q continuation `3307441` is newer and running, so latest
  selected corrected-Q schema coverage remains terminal-harvest blocked.
- High-heat jobs remain monitor/terminal-gated in the cited packages.

## Inferred

The repo does not need another broad case inventory to satisfy this LitRev
contract. The next blocker-free extraction queue should focus on exact
component/recovery and same-QOI UQ tasks:

- Pressure-corner basis/recovery with component versus cluster versus
  section-effective naming.
- Matched-plane RAF/RMF/SVF extraction for latest corrected-Q, high-heat, and
  upcomer/corner anchor candidates.
- Same-QOI endpoint UQ with neighboring windows, mesh/GCI provenance, and plane
  sweeps.
- Split junction/stub thermal ledgers plus storage/radiation treatment without
  hiding residuals in internal Nu.

## Contradictions Or Caveats

Some rows are marked `field_status=present` even though they are not admitted.
The CSV separates field existence from coverage and admission status to avoid
overclaiming diagnostic evidence.

## Next Useful Actions

Use the CSV as the dispatch list. The highest-priority next rows are
`TODO-LITREV-PRESSURE-CORNER-BASIS-RECOVERY`, a same-QOI endpoint UQ execution
row, and a terminal harvest/admission row for live corrected-Q/high-heat cases
after they reach terminal state.
