---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation/candidate_triplet_reconciliation.csv
tags: [journal, s13, recirculation, exchange-cell, mesh-gci, coarse-equivalence]
related:
  - .agent/status/2026-07-22_TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22.md
  - imports/2026-07-22_s13_candidate_coarse_medium_fine_reconciliation.json
task: TODO-S13-CANDIDATE-COARSE-MEDIUM-FINE-RECONCILIATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Candidate Coarse/Medium/Fine Reconciliation

## Attempted

Claimed a narrow follow-on row to reconcile the now-canonical medium/fine
exact-label split rerun with the current-coarse candidate rows produced by the
same-label mesh-family generation package. Added a builder and tests so the
diagnostic comparison can be regenerated from CSV inputs.

## Observed

Candidate triplets exist for all `12` Salt2/Salt3/Salt4 case/QOI combinations.
`Q_wall_W` is the only low-spread lane: candidate coarse/fine spread is at most
about `1.58%`, and medium/fine spread remains about `0.50%`. The exchange
positive-outward proxy has a much larger candidate coarse/fine spread, up to
about `304.85%`. Residence-time and wall/core/bulk contrast are also large or
unstable enough to keep closed.

## Inferred

The result improves the thesis evidence story but does not unlock formal GCI.
The completed coarse-equivalence/open-CV contract is controlling: current-coarse
rows are still reference candidates only, not admitted same-label coarse mesh
members. Running formal Richardson/GCI on those rows would overstate the
evidence.

## Caveats

The current-coarse values are useful for diagnostic trend checks and figure
context, but they do not clear geometry-mask, time-window, field/source/property,
closed-CV, or source-release criteria. No source-side heat flow was relabeled as
`Q_wall_W`, and no exchange coefficient was fit.

## Next Useful Actions

Do not spend more effort on S13 coefficient fitting until strict same-basis
coarse/medium/fine extraction exists or the equivalence contract criteria are
audited and admitted. Use `Q_wall_W` as a diagnostic heat-flow result in thesis
tables/panels, with explicit wording that S13 production/admission remains
fail-closed.
