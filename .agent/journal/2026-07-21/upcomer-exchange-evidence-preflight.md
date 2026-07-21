---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_evidence_preflight/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_4_upcomer_exchange_and_internal_nu_gate/phase4_decision_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_matched_plane_recirc_field_harvest/recirc_harvest_readiness.csv
tags: [journal, forward-model, upcomer, recirculation, heat-loss, preflight]
related:
  - .agent/status/2026-07-21_TODO-UPCOMER-EXCHANGE-EVIDENCE-PREFLIGHT-2026-07-21.md
  - imports/2026-07-21_upcomer_exchange_evidence_preflight.json
task: TODO-UPCOMER-EXCHANGE-EVIDENCE-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Thermal-modeling/Hydraulics/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# Upcomer Exchange Evidence Preflight

## Attempted

Implemented the planned no-solver preflight after the Phase 4
upcomer exchange/internal-`Nu` gate. The builder reads existing Phase 4,
matched-plane recirculation harvest, and first-wave predictive-model artifacts
and emits a variable-availability ledger, sampler source-family queue, row-level
QOI table, same-QOI UQ status, Phase 4B decision table, manifest, summary, and
README.

## Observed

The current Phase 4 package has `42` upcomer exchange-readiness rows. Existing
rows include useful RAF/RMF/SVF diagnostics and `27` nonblank energy-residual
values, but they do not provide admission-grade `V_recirc`, `mdot_exchange`,
`tau_recirc`, same-window `T_main`/`T_recirc`, same-window pressure residual
basis, or same-QOI UQ. The recirculation harvest readiness table has five
source families; none are safe for immediate sampler launch from this row.

## Inferred

The scientifically rigorous next step is not a duplicate sampler or a Phase 4B
rescore. The evidence should instead be used to document why ordinary
single-stream upcomer closures remain disabled and what exact exchange-state
fields are missing. Any later sampler must be claimed separately with a fixed
source family, QOI contract, terminal-state policy, and same-QOI uncertainty
plan.

## Caveats

This task did not inspect native CFD fields directly. It intentionally relies
on the already-published Phase 4 and matched-plane recirculation packages.
Because terminal/live CFD state was read only, this package does not decide
whether a terminal harvest is ready; it only prevents a duplicate or premature
sampler launch from the predictive-model planning row.

## Next Useful Actions

1. If terminal corrected-Q or high-heat evidence lands, claim a narrow terminal
   harvest/admission row before any exchange-state sampler.
2. If no terminal source can provide the fields, claim a sampler-design row with
   explicit `V_recirc`, `mdot_exchange`, `tau_recirc`, thermal-state, pressure,
   and same-QOI UQ outputs.
3. Keep Phase 5 final scorecard work trigger-gated until a runtime-legal
   candidate or a formal negative freeze exists.
