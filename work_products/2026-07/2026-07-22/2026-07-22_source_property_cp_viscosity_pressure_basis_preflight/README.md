---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_mf13_signed_source_property_heat_path_release_preflight/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf15_runtime_wall_profile_basis_gate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_mf16_source_property_exact_fields_release_candidate/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_nominal_train_release_preflight/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/summary.json
tags: [source-property, cp, viscosity, pressure-basis, preflight, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22.md
  - .agent/journal/2026-07-22/source-property-cp-viscosity-pressure-basis-preflight.md
task: TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / cfd-pp / Tester / Writer / Reviewer
type: work_product
status: complete
---
# Source/Property CP, Viscosity, And Pressure-Basis Preflight

Decision: `fail_closed_exact_cp_viscosity_pressure_basis_not_release_ready`.

This packet preflights the exact source/property basis needed before any
thermal, upcomer-exchange, or pressure/F6 release. It is a cross-domain
contract, not a release. No values are promoted into a runtime candidate.

## Result

- Nominal train source/property release-ready rows: `0/4`.
- MF13 signed heat-path release-ready rows: `0`.
- MF15 wall/profile release-ready rows: `0`.
- MF16 exact-field release-ready rows: `0`.
- S13 exchange-cell source/property release-ready rows: `0`.
- Pressure/F6 release-ready rows: `0`.

The missing release basis is not one scalar. It is the combination of
row-specific `cp_J_kg_K`, viscosity/property mode, pressure basis (`p`, `p_rgh`,
and head/hydrostatic correction), legal setup-known source/sink fields,
same-window ownership of signed heat paths, split-role permission, and same-QOI
uncertainty.

## Outputs

- `field_release_contract.csv`
- `case_qoi_preflight_matrix.csv`
- `pressure_basis_contract.csv`
- `heat_path_lane_separation.csv`
- `runtime_forbidden_replay_audit.csv`
- `next_extraction_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Claim Boundary

This packet may be cited to explain why source/property release remains closed
and what exact fields are needed next. It must not be cited as releasing
`cp_J_kg_K`, viscosity, pressure-basis rows, `Q_wall_W`, exchange coefficients,
F6, component K, wall/profile corrections, or passive-boundary coefficients.
