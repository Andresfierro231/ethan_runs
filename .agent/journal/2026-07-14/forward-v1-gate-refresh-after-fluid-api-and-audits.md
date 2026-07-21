---
date: 2026-07-14
task: AGENT-366
title: Forward-v1 gate refresh after Fluid API and audits
tags:
  - journal
  - forward-model
  - forward-v1
  - scorecard
  - assumptions
related:
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_gate_refresh_after_fluid_api_and_audits/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/README.md
---

# Forward-v1 gate refresh after Fluid API and audits

Decision: final forward-v1 remains blocked. The refreshed gate state records
real progress without promoting diagnostic or API-only evidence into final
predictive closure.

What changed:

- Fluid reset/development API support landed as
  `MinorLosses.reset_development_k_by_segment`.
- H1 remains blocked because current hydraulic evidence still has 0
  fit-admissible component/cluster K rows and no admitted reset/development
  pressure scorecard.
- AGENT-360 added residual-attribution evidence with 16 model result rows and
  204 TP/TW sensor error rows.
- Salt1 hi10q's stale failed/not-admissible conflict is resolved by
  patch-complete terminal BC evidence, but Salt1 remains outside the current
  Salt2/Salt3/Salt4 final scoring split.
- PM5 matched pressure/upcomer metrics remain pending because job `3295901` is
  still `PENDING` and parsed metric files are absent.

Math and assumptions now documented:

- `e_mdot = mdot_1d - mdot_cfd`.
- `e_T(sensor) = T_1d(sensor) - T_cfd(sensor)`.
- `e_Q(role) = Q_1d(role) - Q_cfd_reference(role)`.
- `e_T_section = T_1d_section - T_cfd_section`.

Runtime-input guardrails:

- No CFD mdot as model input.
- No realized CFD `wallHeatFlux` as predictive runtime input.
- No imposed CFD cooler duty as final predictive HX evidence.
- No validation or holdout temperatures for fitting.
- No diagnostic internal Nu rows as trainable closure data.

Next execution gates:

- Harvest/admit PM5 matched pressure/upcomer metrics after job `3295901`
  reaches terminal state.
- Write a dated perturbation split policy before any +/-5Q row changes
  train/validation/holdout population.
- Build reset/development or F6 hydraulic scorecard only after admitted
  pressure/Re-variation rows exist.
- Build setup-only boundary/HX outputs without CFD duty or realized wallHeatFlux
  runtime leakage.
- Run the final residual-attribution scorecard only after the upstream gates
  land.

Forward-model map and thesis README links were not edited because active
AGENT-365 currently owns those paths.
