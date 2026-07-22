---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_localized_fixed_k_forward_score/summary.json
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hydraulic_correction_candidates/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_f6_hydraulic_screen/f6_hydraulic_scorecard.csv
tags: [hydraulics, h1, f6, friction, pressure-ledger]
task: AGENT-333
date: 2026-07-14
role: Hydraulics / Implementer / Tester / Writer
status: complete
---
# H1 Faithful Gap And F6 Decision

## Decision

Retire the current H1 forms as proxy-only. The aggregate H1 proxy remains useful
diagnostic evidence that added hydraulic resistance can move mdot toward CFD,
but it is not a faithful closure. The localized fixed-K-only follow-up failed
the directional screen, and the missing physics is exactly the part H1 was meant
to represent: reset/redevelopment plus separated component/cluster losses.

The next hydraulic candidate is `F6_phi_re` as a bounded screen, not a validated
closure. It should run only after corrected-Q or equivalent Re-variation rows
are terminal/admitted, with no thermal fitting, no recirculation-invalid fit
rows, and no global multiplier.

## Recommended Next Hydraulic Run/Edit

Do not launch another H1 fixed-K run. The faithful-H1 path first needs a
reset/development input table and diagnostics that keep component K, cluster K,
branch-apparent loss, straight friction, and recirculation diagnostics separate.
If that edit is not being taken immediately, the next hydraulic test should be a
bounded F6/Re screen under the acceptance criteria in
`f6_candidate_decision_table.csv`.

## Outputs

- `h1_faithful_implementation_gap_table.csv`
- `f6_candidate_decision_table.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

- Thermal fitting used: `false`.
- Native CFD outputs mutated: `false`.
- Global friction multiplier exported: `false`.
