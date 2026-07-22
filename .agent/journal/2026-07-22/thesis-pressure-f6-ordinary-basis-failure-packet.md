---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_study_pressure_basis_ladder_evidence_packet/README.md
tags: [journal, pressure, f6, ordinary-basis, negative-result]
related:
  - .agent/status/2026-07-22_TODO-THESIS-PRESSURE-F6-ORDINARY-BASIS-FAILURE-PACKET-2026-07-22.md
  - imports/2026-07-22_thesis_pressure_f6_ordinary_basis_failure_packet.json
task: TODO-THESIS-PRESSURE-F6-ORDINARY-BASIS-FAILURE-PACKET-2026-07-22
date: 2026-07-22
role: Hydraulics / cfd-pp / Writer / Reviewer / Tester
type: journal
status: complete
---
# Pressure F6 ordinary-basis failure packet

## Attempted

Claimed the pressure F6 ordinary-basis failure row and assembled a compact
thesis packet from existing pressure basis ladder, low-recirculation anchor,
S10/S14 retry/UQ, and hybrid pressure no-fit evidence.

## Observed

The lower-right two-tap rows are hydrostatic-dominated and have small negative
section-effective residuals after hydrostatic and kinetic terms are separated.
Reverse-flow fractions are material, component isolation lacks a valid
straight/development reference, same-QOI UQ is missing, and no endpoint source
fields or CAND001 terminal success are available.

## Inferred

The negative-K artifact is now a publishable negative result, not a coefficient
to salvage. The thesis should say these rows motivate section-effective or
throughflow-plus-recirculation pressure modeling, while ordinary component-K
and F6 admission remain closed.

## Caveats

The packet does not perform an F3/Shah numerical comparison because no admitted
ordinary F6 candidate exists. The Salt2 section-effective transfer value is
diagnostic and not a final pressure score.

## Next Useful Actions

Seek different pressure anchors with low recirculation/nonrecirculation, or
build an explicit throughflow-plus-recirculation pressure residual model in a
separate predeclared row. Do not reuse the lower-right rows as component-K/F6
fit evidence.
