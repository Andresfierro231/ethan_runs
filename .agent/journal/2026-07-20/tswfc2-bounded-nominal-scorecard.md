---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/coupled_delta_vs_m3.csv
  - work_products/2026-07/2026-07-20/2026-07-20_final_scorecard_source_property_refresh/README.md
tags: [forward-model, tswfc2, bounded-scorecard, not-admitted]
related:
  - .agent/status/2026-07-20_AGENT-557.md
  - imports/2026-07-20_tswfc2_bounded_nominal_scorecard.json
task: AGENT-557
date: 2026-07-20
role: Forward-pred/Thermal-modeling/Implementer/Tester
type: journal
status: complete
---
# TSWFC2 Bounded Nominal Scorecard

## Attempted

Ran the next-agent contract from AGENT-556: one bounded TSWFC2 nominal
scorecard using the AGENT-553 four-node setup only. The package solved
Salt1-4 nominal through the read-only Fluid API and wrote post-solve validation
scorecards against M3/prior wall-source references.

## Observed

The root problem is not the immediate blocker for this candidate. Salt1-4 all
return `root_status=accepted`, `accepted_for_validation=True`, and bracketed
pressure/temperature roots.

The candidate is still not admissible. Salt2, Salt3, and Salt4 regress versus
M3 in mdot, TP RMSE, TW RMSE, and all-probe RMSE. Salt1 solves but lacks an M3
comparator in the cited comparator table, so it is a release-gated row rather
than an admission row. Source/property gates also block admission: Salt1 labels
remain partial, and Salt2-4 retain conservative mixed/outside envelope plus
diagnostic/no-fit source-use labels.

## Inferred

The distributed TSWFC2 API is executable, but the specific four-node setup from
the smoke test is not a blocker unlock. The large TP/TW/all-probe regressions
mean the problem is not merely that TSWFC2 needed to be promoted from smoke to
nominal scoring. Repeating this exact candidate would waste time unless a new
physical hypothesis changes the candidate or a separate release gate changes
what can be admitted.

## Caveats

Validation records were loaded only after `solve_case` returned and were used
for scoring, not runtime inputs. This task did not run a broad grid, fit a
parameter, select a model, mutate native CFD outputs, edit Fluid source,
change registry/admission state, or update the blocker register.

## Next Useful Actions

Run AGENT-558: ingest the completed external Fluid UMX1 follow-up and decide
whether UMX1 is scorecard-ready, blocked, or superseded. Keep source/property
label work and upcomer-onset anchor design as separate gates. Do not rerun this
unchanged TSWFC2 four-node candidate for admission.
