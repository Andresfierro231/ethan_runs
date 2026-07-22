---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight/summary.json
tags: [journal, source-property, cp, viscosity, pressure-basis]
related:
  - .agent/status/2026-07-22_TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22.md
  - imports/2026-07-22_source_property_cp_viscosity_pressure_basis_preflight.json
task: TODO-SOURCE-PROPERTY-CP-VISCOSITY-PRESSURE-BASIS-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / Forward-pred / cfd-pp / Tester / Writer / Reviewer
type: journal
status: complete
---
# Source/Property CP, Viscosity, And Pressure-Basis Preflight

## Attempted

Claimed the open source/property CP, viscosity, and pressure-basis preflight
row. Read MF13, MF15, MF16, nominal source/property preflight, thermal
accounting, pressure-basis ladder, S13 production-harvest gate, pressure F6
source recovery, and S12 thermal freeze-gate summaries.

## Observed

All relevant release candidates remain closed. MF13 has signed/source heat-path
context but `0` release-ready rows. MF15 has a useful D3 diagnostic wall/profile
signal but `0` wall/profile release-ready rows. MF16 reviewed exact fields but
has `0` exact-field release-ready rows. Nominal train source/property release
is `0/4`. S13 source/property release and pressure/F6 release also remain zero.

## Inferred

The blocker is a combined basis problem, not just a missing scalar. A release
requires row-specific `cp_J_kg_K`, viscosity/property mode, pressure basis
(`p`, `p_rgh`, head/hydrostatic correction), legal setup source/sink fields,
split permission, signed heat-path ownership, and same-QOI uncertainty.

## Caveats

This row did not inspect native CFD fields or run a sampler. It is a preflight
contract built from completed package summaries and tables.

## Next Useful Actions

1. Let the active S13 exact-label sampler finish, then run post-sampler GCI.
2. After CAND001 job `3308712` becomes terminal, run terminal readiness before
   any pressure/F6 source release.
3. Build the nondimensional regime map to decide which literature closures are
   eligible before future source/property release attempts.
