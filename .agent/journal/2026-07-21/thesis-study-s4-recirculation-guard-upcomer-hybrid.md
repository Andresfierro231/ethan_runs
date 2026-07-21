---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid/README.md
tags: [journal, thesis-study, recirculation, upcomer]
related:
  - .agent/status/2026-07-21_TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21.md
  - imports/2026-07-21_thesis_study_s4_recirculation_guard_upcomer_hybrid.json
task: TODO-THESIS-STUDY-S4-RECIRCULATION-GUARD-UPCOMER-HYBRID-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Thesis S4 Recirculation Guard Upcomer Hybrid

## Attempted

Built a reproducible S4 thesis-study package from existing Phase 4,
exchange-preflight, LitRev exchange-cell, switching, and ordinary-branch gate
outputs.

## Observed

The current package reviews `90` ordinary single-stream candidates and disables
ordinary closure for all reviewed branch groups. It preserves `45`
reverse-flow/exchange rows as diagnostics and reviews `14` exchange variables.
Every current row remains non-scoreable and non-admitted.

## Inferred

The thesis can state that recirculation evidence invalidates ordinary
single-stream closure labels for the current upcomer lane. It cannot state that
an exchange-cell coefficient, ordinary upcomer `Nu`, ordinary `f_D`, ordinary
`K`, or F6 model is admitted.

## Contradictions Or Caveats

Reverse-flow metrics are useful, but they are not substitutes for coherent
recirculation volume, exchange mass flow, residence time, same-window pressure
residual, energy residual, or same-QOI uncertainty.

## Next Useful Actions

1. Use this S4 package as read-only input to the S5 source/property/split
   release gate.
2. Keep exchange-cell scoring blocked until admitted exchange-state variables
   exist.
3. Keep ordinary upcomer closure rows out of `Nu/f_D/K` fit and model-selection
   pools.

## Guardrails

No native-output, registry/admission, scheduler, Fluid, external repo,
fitting/tuning/model-selection, blocker-register, or generated-index state was
changed.
