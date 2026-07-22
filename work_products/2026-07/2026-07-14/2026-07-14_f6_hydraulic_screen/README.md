---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_gate/hydraulic_fit_safety_gate.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/candidate_rankings.csv
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/h1_hydraulic_scorecard.csv
tags: [hydraulics, friction, f6, mdot, forward-v1]
task: AGENT-318
date: 2026-07-14
role: Implementer/Tester/Writer
status: complete
---
# F6 Hydraulic Screen

## Decision

`F6_phi_re` remains a candidate screen, not a blocker-closing validated
hydraulic closure. The implementation exists in Fluid, but the current evidence
still lacks corrected-Q/held-out admission and has zero publication-ready GCI
rows for the hydraulic fit gate.

H1 localized named-loss/reset remains the hydraulic path that improves mdot
without thermal fitting. For the `F1_heater_only` rows, mean mdot error drops
from `0.0054775` to
`0.0021442` kg/s, a
`60.29%` mean reduction. This is enough
to unblock forward-v1 diagnostic scorecard refresh, but not enough to publish a
final localized closure.

## Boundaries

- No native CFD solver outputs were mutated.
- No thermal parameter fitting was used.
- No one global friction multiplier was exported as a model correction.
- Raw pressure-gradient fit-safe rows, component/localized K, cluster/reset
  effects, branch-apparent loss, and recirculation limitations remain separate.
