---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_static_p_basis_reconstruction_audit/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_corner_publication_freeze/canonical_pressure_corner_result.csv
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/summary.json
tags: [pressure, f6, pressure-corner, publication, no-admission]
related:
  - .agent/status/2026-07-21_TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE.md
  - imports/2026-07-21_pressure_f6_publication_claim_freeze.json
  - work_products/2026-07/2026-07-21/2026-07-21_pressure_f6_publication_claim_freeze/README.md
task: TODO-PRESSURE-F6-PUBLICATION-CLAIM-FREEZE
date: 2026-07-21
role: Writer / Reviewer / Hydraulics / cfd-pp
type: journal
status: complete
---
# Pressure/F6 Publication Claim Freeze

## Attempted

I consolidated the pressure-corner, F6 static-pressure reconstruction, Stage A/B
endpoint QA, S10 gate, and S14 branch-use results into a publication-facing
claim-freeze package. The package was built by script instead of manual table
editing so the claim ledger, blocker table, source manifest, and narrative
remain reproducible from known source artifacts.

I also checked the generated blocker table for stale chronology. The initial
table repeated the earlier Stage B finding that raw static `p` was missing. I
patched the builder so that row now records the later static-pressure audit:
raw static `p` was missing from the Stage B gate refresh, but `p_rgh`
reconstruction is validated for diagnostic pressure deltas only and still does
not admit a coefficient.

## Observed

The static-pressure convention selected by the audit is
`p = p_rgh + rho * (g dot x)`. It validates against Stage A pairwise pressure
deltas with maximum absolute error `4.382729351630587 Pa`.

The S14 branch-use evidence reviewed `53` rows and admitted `0` rows. Use labels
were `11` diagnostic-only, `8` future-candidate, and `34` do-not-use. The current
endpoint pair set has `0/10` ordinary-flow candidates passing RAF/RMF.

The pressure-corner publication freeze keeps the existing corner rows labeled
as section-effective/recovery/diagnostic evidence. They are not F6, component
`K`, or cluster `K` rows.

## Inferred

The publication-safe claim is now clear: pressure rise around corners can be
discussed as hydrostatic/recovery/section-effective/diagnostic evidence, not as
negative loss. The F6 branch evidence is useful for screening and for choosing
future ordinary lanes, but it does not support fitted F6 coefficients.

Right-leg and test-section-span remain the preferred future ordinary F6 lanes,
but only as future candidates. Admission-relevant work must remain separate
from the publication claim freeze.

## What Worked

The static-pressure audit resolved the pressure-basis ambiguity for diagnostic
delta comparisons. The scripted claim-freeze package keeps allowed, forbidden,
and required-before-admission claims in one table, with a source manifest and
tests that protect against accidental admission language.

## What Did Not Work

The current endpoint family did not provide ordinary-flow F6 evidence. Because
`0/10` endpoint pairs pass RAF/RMF, same-QOI UQ and F3 comparison cannot yet be
used to admit F6/component-K coefficients. The Stage B gate refresh alone also
did not contain raw static `p`; it required the later reconstruction audit to
be interpretable for diagnostic deltas.

## Caveats

The reconstructed static-pressure basis is diagnostic-only. It should not be
promoted to component `K`, cluster `K`, fitted F6, S11 release, or coefficient
admission. The package did not edit manuscript text; it provides the tables and
narrative wording to use after a separate manuscript/report path is claimed.

## Next Useful Actions

Claim a separate terminal low-recirculation source-readiness row. If a terminal
ordinary-flow candidate is found, stage endpoint sampling, run same-QOI
mesh/time UQ, then run F3-vs-F6 comparison before any F6/component-K review. Do
not launch sampler or solver work from this publication-freeze task.
