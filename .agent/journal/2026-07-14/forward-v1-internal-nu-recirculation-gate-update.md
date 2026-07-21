---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/README.md
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/README.md
tags: [journal, forward-model, internal-nu, recirculation, scorecard]
related:
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-337
date: 2026-07-14
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Forward-v1 Internal-Nu Recirculation Gate Update

## Decision

Forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`. The new
upcomer recirculation evidence does not reopen thermal fitting. It closes the
internal-Nu fit lane more explicitly: current Salt2-4 upcomer evidence is
section-effective diagnostic evidence, not trainable closure data.

## Work So Far

The existing final forward-v1 gate already admitted only strict input hygiene,
the locked split `salt_2=train`, `salt_3=validation`, `salt_4=holdout`,
forward-v0 execution evidence, diagnostic H1 proxy rows, validation-only or
blocked thermal rows, and post-solve sensor targets. It rejected H1 proxy,
imposed cooler duty, and diagnostic thermal rows as final predictive closure
evidence.

This update adds the upcomer recirculation/internal-Nu result from AGENT-330.
That package reports `0` fit-admissible internal-Nu rows, all three current
upcomer diagnostic rows in a recirculating regime, Re_upcomer from about
`71.125` to `134.883`, and material backflow from about `0.171875` to
`0.277778`. The allowed label is
`Nu_section_effective_upcomer_diagnostic`; universal, transferable, or fitted
internal-Nu labels are rejected for these rows.

## Math, Assumptions, And Theory

Forward-v1 must remain a setup-input prediction problem. It may not use
realized CFD mdot, realized CFD wallHeatFlux, validation or holdout
temperatures, imposed cooler duty, or diagnostic CFD-derived Nu as runtime
inputs. Internal Nu is a heat-transfer closure only if its driving temperature,
flow state, time window, mesh/time uncertainty, and residual ownership are
admitted. Otherwise it can incorrectly absorb heater, cooler/HX, wall/radiation,
storage, branch mixing, recirculation, sign, or hydraulic residuals.

Recirculating upcomer flow violates the single-stream assumption behind a
transferable pipe-style Nu label. Therefore the current evidence can validate
that recirculation exists and can provide section-effective diagnostic context,
but it cannot define a fitted closure law.

## Updated Outputs

- `forward_v1_gate_checklist.csv`: now has 9 gate rows, including
  `upcomer_section_effective_nu_diagnostic`.
- `scorecard_inputs_waiting_on_agents.csv`: now has 6 waiting lanes, including
  `upcomer_section_effective_nu_diagnostic`.
- `internal_nu_dependency_blockers.csv`: new 6-row blocker table for reopening
  internal-Nu fitting.
- `summary.json`: records `fitted_internal_nu_rows_consumable=false`,
  `baseline_literature_default_internal_nu_required=true`,
  `cfd_pp_onset_candidates_required_for_internal_nu_reopen=true`, and
  `therm_reconstr_matched_plane_extraction_required_for_internal_nu_reopen=true`.

## Reopen Conditions

Internal-Nu fitting can only be reconsidered after a later dated gate admits
specific trainable rows and the dependency blockers are resolved. Required
evidence includes terminal/admitted cfd-pp onset candidates near Re 150, 200,
and 250 plus a transition or non-recirculating anchor if available; matched
upcomer inlet/mid/outlet vector and thermal planes; direct wall-bulk or
wall-core driving temperature; Gz or equivalent thermal-development metric;
secondary velocity fraction; mesh/time uncertainty; and residual attribution
that separates hydraulic, boundary/HX, wall/radiation, storage/mixing, and
internal-Nu lanes.

Until that lands, forward-v1 runs keep baseline/literature/default internal Nu
behavior and may use `Nu_section_effective_upcomer_diagnostic` only for
diagnostic or validation-only reporting.
