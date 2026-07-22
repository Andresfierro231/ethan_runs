---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/README.md
tags: [s12, tp-first, handoff, upcomer-exchange]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/thesis_tp_first_handoff.md
task: TODO-S12-TP-FIRST-UPCOMER-EXCHANGE-EVIDENCE-GATE-2026-07-22
date: 2026-07-22
role: Writer / Reviewer
type: operational_note
status: complete
---
# S12 TP-First Upcomer Exchange Evidence Gate

## Why This Exists

The user clarified that TP matters more than TW for the next S12 continuation.
The prior S12 package emphasized TW5/TW6 residual ownership; this handoff
reorients S12 toward TP-first exchange/energy-state evidence.

## Open First

1. `work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/README.md`
2. `work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_unlock_gate_matrix.csv`
3. `work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/s12_tp_next_executable_queue.csv`
4. `work_products/2026-07/2026-07-22/2026-07-22_s12_tp_first_upcomer_exchange_evidence_gate/thesis_tp_first_handoff.md`

## Trusted Packages

- S12 disposition package:
  `work_products/2026-07/2026-07-22/2026-07-22_s12_thermal_residual_candidate_disposition_and_thesis_panels/`
- S12-HIAX1 train score:
  `work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_f_s12_hiax1_train_score/`
- S13 exchange limited sampled-field synthesis:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_limited_sampled_field_evidence_synthesis/`
- S13 exact pressure/Qwall:
  `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_exact_pressure_qwall_compute/`
- S13 source-side/neighbor gate:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_source_side_conservation_neighbor_uq_gate/`
- Signed-error scoreboard:
  `work_products/2026-07/2026-07-22/2026-07-22_thesis_scoreboard_signed_error_shape_and_model_form_dispatch/`

## Current Interpretation

TP should be the primary S12 continuation QOI. Current M3 TP RMSE is smaller
than TW RMSE, but TP remains systematically cold-biased. S12-HIAX1 has large
train-only TP error and must not be frozen. The useful scientific path is to
explain TP through exchange residence time, core/bulk temperature state,
pressure, and source-side energy balance.

## Next Task Sequence

1. TP-first retained-window join of S13 exchange proxies with exact pressure and
   `Q_wall_W`.
2. Source/property release audit for cp, property mode, validity envelope,
   source category, pressure/enthalpy basis, and energy residual sign.
3. Same-QOI neighbor-window and mesh/GCI UQ after exact QOI contract.
4. Freeze review only if production harvest, source/property release, and UQ
   pass.

## Do Not Do

- Do not claim S12-HIAX1 improves TP.
- Do not use protected split scoring before freeze.
- Do not relabel source-side heat as wall heat flux.
- Do not release source/property or Qwall from this package.
- Do not fit a coefficient, admit a closure, publish a final score, or absorb
  the residual into internal Nu.
