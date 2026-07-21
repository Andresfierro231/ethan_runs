---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f6_branch_use_scorecard.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/f3_vs_f6_comparison_readiness.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence/s11_decision.csv
tags: [thesis-dossier, s14, pressure, f6, branch-use, no-admission]
related:
  - .agent/status/2026-07-21_TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21.md
  - imports/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence.json
task: TODO-THESIS-STUDY-S14-PRESSURE-F6-NONRECIRC-ANCHOR-EVIDENCE-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---

# S14 Pressure/F6 Nonrecirculating Anchor Evidence

## Attempted

I implemented the S14 study as an existing-evidence F6 scoring package. The
package consolidates the prior non-upcomer F6 candidate matrix, Stage A/B F6
endpoint QA, static-pressure reconstruction audit, S10 low-recirculation study,
pressure-corner publication/review evidence, and F3 comparison gate.

The goal was to assign every relevant row one use label: `admit`,
`diagnostic_only`, `future_candidate`, or `do_not_use`. No sampler, scheduler
job, fitting, or admission mutation was attempted.

## Observed

The scorecard contains `53` rows:

- `36` legwise inventory rows
- `10` current F6 endpoint-pair rows
- `4` low-recirculation anchor rows
- `3` pressure-corner section-effective rows

No row passes all gates. The use-label counts are:

- `0` admit
- `11` diagnostic-only
- `8` future-candidate
- `34` do-not-use

The only preferred future ordinary F6 lanes are `right_leg` and
`test_section_span`. Current endpoint-pair evidence is diagnostic-only because
ordinary-flow and same-QOI UQ gates fail. Pressure-corner rows are explicitly
not F6 evidence; they remain section-effective or pressure-recovery diagnostics.

## Inferred

The correct scientific decision is not to force an F6 score. Current evidence
supports a branch-use map and publication guardrails, not an admitted F6
coefficient. F3-vs-F6 comparison remains not evaluated because no row clears
the ordinary-flow, endpoint, same-QOI UQ, and source/property gates needed for a
meaningful comparison.

This improves the publication position: the paper can say exactly where F6 is
promising, where it is diagnostic, and where it is forbidden. It should not
claim an F6 improvement score yet.

## Contradictions Or Caveats

Static pressure reconstruction is no longer the dominant blocker for coarse F6
rows; the reconstructed pressure basis is diagnostic-ready. The remaining hard
blockers are ordinary-flow and same-QOI UQ. That distinction matters because it
prevents old wording that says coarse F6 is blocked only by missing static `p`.

Low-recirculation anchor candidates are still future candidates because the
terminal/source harvest is not ready in current evidence. They should not be
treated as failed physics; they are incomplete source-family evidence.

## Next Useful Actions

Refresh terminal readiness for the low-recirculation source family, then claim
a separate staged-copy sampler/UQ row only if terminal cases are available.
After a candidate passes ordinary-flow and same-QOI UQ, run an F3-vs-F6
comparison package. Until then, keep S11 blocked for pressure/F6.
