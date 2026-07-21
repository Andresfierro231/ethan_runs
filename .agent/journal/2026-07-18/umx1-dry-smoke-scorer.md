---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/summary.json
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/umx1_root_status_by_case.csv
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/umx1_probe_smoke_score.csv
tags: [umx1, forward-predictive, smoke, journal]
related:
  - .agent/status/2026-07-18_AGENT-544.md
  - imports/2026-07-18_umx1_dry_smoke_scorer.json
  - work_products/2026-07/2026-07-18/2026-07-18_umx1_dry_smoke_scorer/README.md
task: AGENT-544
date: 2026-07-18
role: Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
supersedes:
  - AGENT-543 no-run scoring-readiness handoff
superseded_by:
---

# UMX1 Dry/Smoke Scorer Journal

Task: `AGENT-544`

## Observed

AGENT-540 established that Fluid has a real UMX1 upcomer exchange hook. AGENT-543
then supplied the no-run scoring-readiness contract. AGENT-544 owns the narrow
dry/smoke scorer and treats Fluid source and native outputs as read-only.

The work-product CSVs already contained `9` fast-scan smoke rows. The package
summary was refreshed from those CSVs so it now reports
`fast_scan_smoke_complete`, `9` smoke rows, `3/9` root passes, and `9/9`
conservation passes.

## Attempted

I hardened the scorer around package integrity instead of rerunning the solver:
validation now reloads existing CSV state and rejects stale `summary.json` or
stale `umx1_no_admission_review.csv`. A new `--refresh-summary` mode regenerates
the summary, README, and no-admission review from existing package CSVs.

## Inferred

The Fluid hook is usable as an energy-conserving smoke scorer: the active UMX
exchange rows produce finite main/reservoir temperatures and zero exchange
residuals within the scorer tolerance. That is not enough to advance UMX1.
Salt3/Salt4 fast-scan rows are not accepted for validation, and the exchange
candidates worsen all scored probe groups relative to the disabled baseline:
Salt2 worsens by at least `0.352842 K` in all-experimental MAE, Salt3 by
`0.0147321 K`, and Salt4 by `0.0147359 K`.

## Contradictions And Caveats

- This task did not edit Fluid source. AGENT-544 explicitly kept Fluid and
  `../cfd-modeling-tools/**` read-only.
- The smoke result is not a final scientific rejection of every possible UMX
  form. It rejects expansion/admission of this predeclared smoke family.
- `fast_scan` is a bounded smoke engine. Full `solve_case` remains available in
  the package harness but was not launched in this closeout.
- Targets are joined after solve only for scoring; validation temperatures are
  not runtime inputs.

## Next Useful Actions

- Do not launch a UMX1 grid from AGENT-544 outputs; accepted roots block
  expansion.
- If UMX1 remains the top avenue, open a separate Fluid-edit row that explicitly
  claims `../cfd-modeling-tools/**` and implements a richer setup-only
  stratification/source state before any new score run.
- Keep Salt1 blocked until schema promotion lands, then revisit split coverage
  under the canonical final predictive split.
