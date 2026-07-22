---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_model_form_extraction/cfd_postprocessing_contract.csv
  - reports/2026-07/2026-07-20/2026-07-20_cfd_postprocessing_readiness_refresh/README.md
  - reports/2026-07/2026-07-20/2026-07-20_cfd_postprocessing_readiness_refresh/cfd_postprocessing_readiness_refresh.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_loop_plot_and_cfd_heat_audit/heat_audit_and_modeling_recommendations.md
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/README.md
  - .agent/status/2026-07-21_AGENT-576.md
  - .agent/status/2026-07-17_AGENT-485.md
tags: [cfd-postprocessing, litrev-contract, schema-gap, pressure, thermal, uncertainty]
related:
  - operational_notes/maps/cfd-runs-and-admission.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: TODO-LITREV-CFD-POSTPROCESSING-SCHEMA-GAP
date: 2026-07-21
role: cfd-pp/Tester/Writer
type: work_product
status: complete
---
# LitRev CFD Postprocessing Schema Gap Audit

This package compares the 18-row LitRev CFD postprocessing contract against
existing repo artifacts. It is inventory-only: no native CFD/OpenFOAM output,
registry/admission state, scheduler state, Fluid code, or external repo was
mutated, and no postprocessing or solver job was launched.

## Output

- `cfd_postprocessing_schema_gap_audit.csv`: one row per LitRev contract field.

The CSV uses `field_status` values `present`, `missing`, and
`not_applicable`. Partial coverage and admission blockers are tracked separately
in `coverage_status`, `admission_status`, and `missing_subfields_or_gap`.

## Main Findings

Most scalar pressure and thermal reductions already exist somewhere in the
repo. The missing admission-grade pieces are not broad case summaries; they are
component/recovery metadata and same-QOI uncertainty.

- Pressure: gross static pressure, hydrostatic/kinetic terms, velocity basis,
  straight/developing references, and diagnostic section losses exist, but
  component/cluster classification and recovery diagnostics are missing.
- Recirculation: RAF/RMF/SVF exist for lower-right two-tap endpoints and RAF
  proxies exist in pressure ladders, but latest corrected-Q, high-heat, and
  upcomer matched-plane rows still need terminal same-window extraction.
- Thermal: bulk enthalpy, wall heat flux, wall temperature, internal HTC, and
  resistance-network terms exist for Salt2-4 mainline and selected external
  rows, but internal Nu fitting remains non-admitted.
- Heat loss: heater, cooler, passive, junction/stub, and residual ledgers exist;
  storage is not directly measured, radiation is `no qr` rather than separated,
  and junction/stub heat is aggregate.
- Same-QOI uncertainty: general time-window UQ exists, but F6/pressure endpoint
  admission remains blocked because same-QOI time UQ has zero pass rows and mesh
  rows are diagnostic rather than accepted GCI.

## Current Live-Run Caveat

The July 20 PM10 classification has harvested terminal heat/mass evidence from
job `3293924` plus harvester `3295438`. The July 21 corrected-Q continuation
`3307441` is newer and running; any field that must represent the latest
selected corrected-Q continuation remains blocked until a separate terminal
harvest/admission task is claimed.
