---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
tags: [pressure, f6, publication, claim-freeze, no-admission]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE.md
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/README.md
task: TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE
date: 2026-07-21
role: Writer / Reviewer / Hydraulics / cfd-pp
type: work_product
status: complete
---
# Pressure/F6 Publication Claim Freeze

## Decision

This package freezes the publication-facing pressure/F6 claims after the F6
static-pressure audit and S14 branch-use study.

Result: `0` F6/component/cluster coefficient rows are admitted. Current F6
evidence may be used for diagnostic pressure-basis and branch-screening
discussion only.

## Open First

1. `pressure_f6_publication_claim_freeze.csv`
2. `pressure_corner_narrative_update.md`
3. `f6_use_decision_publication_table.csv`
4. `admission_blocker_table.csv`
5. `ordinary_flow_next_steps.csv`

## Publication Boundary

Allowed: coarse F6 static pressure can be reconstructed diagnostically from
`p_rgh` using the validated hydrostatic relation; pressure-corner static rise is
hydrostatic/recovery/section-effective/diagnostic evidence; right-leg and
test-section-span remain future ordinary F6 lanes.

Forbidden: fitted F6, component `K`, cluster `K`, clipped `K`, hidden global
multiplier, negative-loss wording, S11 release, or any admission claim.

## Guardrails

No native output, registry/admission state, scheduler state, solver/sampler,
Fluid/external repo, blocker register, generated index, manuscript file,
fitting/model selection, clipped `K`, hidden multiplier, F6 fit, component `K`,
or cluster `K` was changed or produced.
