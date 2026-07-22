---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_axial_mixing_dry_contract/README.md
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_salt1_4_bounded_comparison_intake/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_localized_form_smoke_intake/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_amx1_lower_multiplier_smoke_intake/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_amx1_gradient_clipped_smoke_intake/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_amx1_physics_revision_smoke_intake/summary.json
tags: [amx1, axial-mixing, fluid-api-handoff, thermal-modeling, fail-closed]
related:
  - .agent/status/2026-07-22_TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22.md
  - .agent/journal/2026-07-22/1d-amx1-axial-mixing-fluid-api-handoff.md
task: TODO-1D-AMX1-AXIAL-MIXING-FLUID-API-HANDOFF-2026-07-22
date: 2026-07-22
role: Forward-pred / Thermal-modeling / Coordinator / Writer / Reviewer
type: work_product
status: complete
---
# AMX1 Axial-Mixing Fluid API Handoff

Decision: `handoff_superseded_by_existing_fluid_smokes_no_new_amx1_expansion`.

The original AMX1 dry contract asked for an external Fluid implementation row.
That row, and follow-on smoke variants, have already happened. The current
useful handoff is therefore not another request to implement pairwise axial
mixing. It is a stop/go packet: it records the API capability that now exists,
the tested-form performance, and the evidence required before any new AMX1
Fluid implementation or Salt1-Salt4 expansion is justified.

## Result

- API/root/ledger readiness is no longer the blocker for basic AMX1 forms.
- Tested AMX1 rows were runtime-clean and conservative in the Fluid smoke
  audits.
- No tested AMX1 form passed the progression gate because temperature residual
  metrics, especially all-probe and TP RMSE, worsened.
- The parent-cell physics revision did not rescue the failure mode.
- The current AMX1 route should stay diagnostic-only until new CFD structure
  evidence supports a different local exchange law, directionality rule, or
  physically bounded source envelope.

## Outputs

- `source_manifest.csv`
- `current_fluid_capability_matrix.csv`
- `amx1_tested_form_performance.csv`
- `external_fluid_handoff_decision.csv`
- `source_evidence_required_before_next_amx1.csv`
- `runtime_input_contract.csv`
- `conservation_test_contract.csv`
- `next_board_tasks.csv`
- `summary.json`

## Stop/Go Rule

Do not claim another AMX1 external Fluid row merely to retune multiplier
strength, retry Salt1-Salt4, or broaden the score grid. The next AMX1
implementation row is useful only if it is driven by new source evidence such
as signed local exchange direction, wall/core stratification shape near
TW5/TW6, or a source-bounded physical exchange envelope. Until then, shift the
primary blocker-unlock effort to setup-only wall/test-section/passive-boundary
modeling and S13 same-label mesh/GCI generation.

## Guardrails

No Fluid files were edited, no scheduler action was taken, no native CFD output
was mutated, no registry or admission state changed, no fitting or model
selection was run, no validation/holdout/external-test scoring was performed,
and no source/property label was released.
