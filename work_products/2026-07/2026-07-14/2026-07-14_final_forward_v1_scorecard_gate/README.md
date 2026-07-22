---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_predictive_h1_hydraulic_scorecard/h1_hydraulic_scorecard.csv
  - work_products/2026-07/2026-07-14/2026-07-14_thermal_admission_internal_nu_final_gate/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_upcomer_recirculation_internal_nu_admissibility/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_forward_model_readiness_after_h1_proxy/blockers_to_final_forward_v1.csv
tags: [forward-model, predictive-1d, scorecard, admission-gate]
related:
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/maps/thermal-closures-and-internal-nu.md
task: AGENT-321
updated_by: AGENT-337
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# Final Forward-v1 Scorecard Gate

This is the final gate decision for the current evidence set. It is not a new fitted model run.

## Decision

- Final forward-v1 status: `blocked_no_go_final_forward_v1_not_admitted`.
- Current evidence is scored-but-blocked: H1 is still proxy-only, thermal internal Nu has no fit-admissible rows, and boundary/HX/wall/radiation support is not final setup-only evidence.
- No CFD mdot, realized CFD wallHeatFlux, or validation/holdout temperatures are admitted as runtime predictive inputs.
- The active split remains `salt_2=train`, `salt_3=validation`, `salt_4=holdout` unless a new dated split supersedes it.

## Admitted Now

- Strict input hygiene and current Salt2/3/4 split discipline.
- Forward-v0 solve_case confirmation as execution evidence.
- H1 aggregate fixed-K rows only as diagnostic/proxy hydraulic evidence.
- Thermal rows only as validation-only or blocked evidence, not fit targets.
- `Nu_section_effective_upcomer_diagnostic` only as diagnostic/validation-only upcomer recirculation evidence.
- Sensor labels only as post-solve validation targets with blocked labels excluded.

## Math And Assumptions

- The forward model must map setup inputs to predicted mdot and sensor targets; realized CFD mdot, realized CFD wallHeatFlux, and validation/holdout temperatures are target data only.
- Train/validation/holdout discipline is fixed at `salt_2=train`, `salt_3=validation`, `salt_4=holdout`; fitted parameters can only use admitted training rows.
- Hydraulic residuals are evaluated before thermal closure fitting because mdot bias propagates into advection, residence time, and heat-transfer residuals.
- Thermal closure evidence must pass admission gates before any internal Nu/HTC/UA fit; validation-only rows can score predictions but cannot fit parameters.
- Upcomer recirculation invalidates universal single-stream Nu/f_D/K labels for current Salt2-4 upcomer rows; use section-effective diagnostic names only.
- Predictive runs keep baseline/literature/default internal Nu behavior unless a later dated gate admits a specific row.
- Boundary/HX terms must be setup-only model outputs. Imposed cooler duty and replayed realized wall heat are diagnostic controls, not final predictive boundary evidence.
- Sensor-map rows are post-solve comparisons. They cannot be used as corrections to the forward run.

## Residual Attribution Plan

- Hydraulic lane: compare predicted and CFD mdot plus any pressure residuals from localized H1 or successor scorecards.
- Boundary/HX lane: report modeled cooler/HX duty, passive wall/radiation terms, and heat-balance residual from setup-only boundary inputs.
- Thermal lane: report sensor, segment, and `Nu_section_effective_upcomer_diagnostic` residual context only after hydraulic and boundary/HX lanes declare their admissible modes.
- Split lane: summarize train/validation/holdout residuals separately and reject any row whose fit sources include validation or holdout data.
- Internal-Nu fit lane: remain closed until `internal_nu_dependency_blockers.csv` dependencies are resolved and a later thermal gate admits trainable rows.

## Upcomer Recirculation Impact

- The upcomer recirculation package reports `0` fit-admissible internal-Nu rows today.
- Current Salt2-4 upcomer evidence spans only recirculating rows, so it supports an admission/naming rule rather than a fitted Nu closure.
- Before reopening internal-Nu fitting, cfd-pp must provide onset candidates and therm-reconstr must provide matched vector/thermal plane extraction.
- Until then, forward-v1 cannot consume fitted internal Nu rows and must keep baseline/literature/default internal Nu behavior for predictive runs.

## Pending

- cfd-pp admitted case inventory or corrected-Q terminal admission rows.
- Hydraulics localized H1/reset/redevelopment scorecard with no validation or holdout fitting.
- BC-modeling setup-only HX/external-boundary outputs with runtime-input audit.
- Internal-Nu gate reopening only after cfd-pp onset candidates, therm-reconstr matched-plane extraction, mesh/time uncertainty, and residual-ownership evidence land.

## Blocked

- Final forward-v1 scoring remains blocked while the checklist has blocking gates.
- H1 proxy, imposed cooler duty, and diagnostic thermal rows are not final predictive closure evidence.
- `Nu_section_effective_upcomer_diagnostic` cannot be treated as trainable closure data.

## Files

- `forward_v1_gate_checklist.csv`
- `scorecard_inputs_waiting_on_agents.csv`
- `internal_nu_dependency_blockers.csv`
- `final_forward_v1_gate_table.csv`
- `forward_v1_score_rows.csv`
- `source_manifest.csv`
- `summary.json`
