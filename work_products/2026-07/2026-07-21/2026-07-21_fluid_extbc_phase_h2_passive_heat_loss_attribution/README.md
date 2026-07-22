---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensitivity_metrics.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_extbc_phase_h_compute_safe_sensitivity/sensor_delta.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_external_bc_phase_e_train_full_solve/role_row_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_extbc_source_sink_provenance_recovery/setup_source_sink_provenance_ledger.csv
tags: [forward-model, external-bc, heat-loss-attribution, train-only]
related:
  - .agent/status/2026-07-21_TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21.md
  - .agent/journal/2026-07-21/fluid-extbc-phase-h2-passive-heat-loss-attribution.md
  - imports/2026-07-21_fluid_extbc_phase_h2_passive_heat_loss_attribution.json
task: TODO-FLUID-EXTBC-PHASE-H2-PASSIVE-HEAT-LOSS-ATTRIBUTION-2026-07-21
date: 2026-07-21
role: Forward-pred/Thermal-modeling/Implementer/Tester/Writer
type: work_product
status: complete
---
# Phase H2 Passive Heat-Loss Attribution Audit

## Why This Exists

Phase H showed that the Phase E thermal residual is strongly responsive to
global passive hA scaling, but weakly responsive to lower-leg-only passive hA
scaling. This package asks whether that signal points to a row-family defect,
a segment cluster, or broad whole-loop passive-wall/source uncertainty.

## Open First

- `passive_hA_family_contribution.csv`
- `tw5_response_waterfall.csv`
- `physical_plausibility_matrix.csv`
- `source_sink_coupling_matrix.csv`
- `repair_candidate_predeclaration_gate.csv`

## Trusted Packages

- Phase E full train solve package.
- Phase F/J residual decomposition package.
- Phase H compute-safe sensitivity package.
- Source/sink provenance recovery package.
- Heated-incline TW4-TW6 audit package.

## Result

- Passive role rows reviewed: `12`.
- Heat-ledger segment rows reviewed: `46`.
- Source/sink metadata rows reviewed: `12`.
- H2 decision: `global_passive_hA_response_broad_and_physical_basis_needed_before_repair`.

The global passive hA response is broad rather than lower-leg-local. Lower-leg
hA half improves TW5 by `4.593107 K`; the
global hA half improves TW5 by `51.633694 K`.
The remaining response is allocated across non-lower-leg passive families only
as an attribution heuristic, not as a replacement for one-at-a-time sweeps.

## Output Contract

- `passive_hA_family_contribution.csv`: row-family hA shares and TW5 response attribution.
- `segment_heat_loss_sweep.csv`: segment heat-loss shares and fixed-state hA-scale proxy.
- `hA_area_unit_audit.csv`: h/area/hA consistency and provenance screen.
- `sign_and_drive_audit.csv`: heat-loss sign and ambient-drive consistency.
- `tw5_response_waterfall.csv`: Phase E to Phase H response waterfall.
- `physical_plausibility_matrix.csv`: follow-on study 1.
- `source_sink_coupling_matrix.csv`: follow-on study 2.
- `repair_candidate_predeclaration_gate.csv`: follow-on study 3.

## Do Not Do

Do not treat `global_passive_hA_scale_0.5` as an admitted repair. Do not score
validation, holdout, or external-test rows from this package. Do not use train
residuals to choose a coefficient. Do not mutate Fluid, native CFD/OpenFOAM
outputs, registry/admission state, blocker register, generated indexes, or
thesis current files from this row.
