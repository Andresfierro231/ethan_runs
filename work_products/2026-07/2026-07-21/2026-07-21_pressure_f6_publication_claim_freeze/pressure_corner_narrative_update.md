---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
tags: [pressure, f6, pressure-corner, publication, claim-freeze]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/README.md
task: TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE
date: 2026-07-21
role: Writer / Hydraulics
type: work_product
status: complete
---
# Pressure/F6 Publication Narrative Update

The pressure/F6 evidence should be written as a diagnostic result with explicit
claim boundaries.

The coarse F6 static-pressure basis is no longer ambiguous for diagnostic pair
deltas. The validated relation is `p = p_rgh + rho * (g dot x)`, selected by
comparison against Stage A rows where both `p` and `p_rgh` were sampled. That
result supports diagnostic F6 pressure-basis discussion, not F6 coefficient
admission.

Pressure rise around corners should be described as hydrostatic/recovery/
section-effective/diagnostic evidence. It must not be described as negative
loss, clipped loss, fitted F6, component `K`, or cluster `K`. The current
pressure-corner publication freeze remains the basis for this claim: gross
static pressure rise is hydrostatic-dominated, while recovery/residual evidence
is unadmitted.

Current F6 endpoint evidence remains blocked for scoring. The decisive blocker
is ordinary-flow: `0/10` current endpoint pairs pass RAF/RMF. Same-QOI mesh/time
UQ and F3 comparison also remain unavailable for admission. Therefore the
publication-safe conclusion is that right-leg and test-section-span are future
ordinary F6 lanes, while current sampled endpoint pairs are diagnostic-only and
pressure-corner rows are not F6.

Future admission work must occur in a separate row: terminal low-recirculation
source readiness, staged endpoint harvest, same-QOI UQ, and then F3-vs-F6
comparison. Until those gates pass, S11 and coefficient claims stay closed.
