---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - operational_notes/07-26/21/2026-07-21_HEATLOSS_PHASED_PROGRESS_PLAN.md
  - work_products/2026-07/2026-07-16/2026-07-16_predictive_boundary_submodel_admission/submodel_admission_summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_segment_thermal_models/thermal_model_slot_admission.csv
  - work_products/2026-07/2026-07-17/2026-07-17_final_predictive_scorecard_shell/README.md
tags: [thermal-modeling, heat-loss, release-gate, fluid-walls]
related:
  - .agent/BOARD.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
task: TODO-HEATLOSS-PHASE-0-BASELINE-RELEASE-GATE
date: 2026-07-21
role: Coordinator/Writer/Reviewer
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 0 Baseline Release Gate

## Decision

Phase 0 releases the current heat-loss accounting contract for downstream work.
It does not score a model, admit a candidate, tune a coefficient, or change
Fluid. The released baseline is the July 21 heat-path contract with additional
consumer gates for the next heat-loss phases.

The release keeps ten lanes separate: heater/source to fluid, internal `Nu`,
wall conduction, contact/layer resistance, insulation/quartz, external
convection, radiation, jacket/cooler removal, storage, and residual.

## Observed Facts

- The heater and cooler/HX setup scalar lanes are admitted as current predictive
  boundary submodels in the July 16 boundary package.
- Wall/test-section passive boundary candidates remain blocked and must not be
  final-scorecard consumers until external BC/radiation and split heat evidence
  are release-gated.
- Internal `Nu` has zero fit-admissible rows. It remains a diagnostic or
  source-envelope lane and cannot absorb heat residual.
- Current CFD radiation is embedded in total `wallHeatFlux`; no separate `qr`
  output is available in the cited evidence.
- The final scorecard shell has no final frozen prediction rows and no
  fit/model-selection-enabled rows after source/property policy.

## Outputs

- `heat_path_release_gate.csv` lists each heat path, executable/admission
  status, forbidden runtime fields, current blocker, and the next consuming row.
- `dependency_release_matrix.csv` states which later phase may consume each
  output and what remains blocked.
- `runtime_forbidden_field_audit.csv` centralizes the runtime-leakage fields
  that are forbidden for predictive model execution.
- `source_manifest.csv` records the source paths used.
- `summary.json` provides machine-readable package counts and guardrails.

## Current Blockers

- Phase 1 must make external BC and radiation semantics executable and audited.
- Phase 2 must improve split heat-loss evidence without inferring missing `qr`
  or storage from residual.
- Phase 3 must wait for Phase 1 and Phase 2 before scoring wall/test-section
  candidates.
- Phase 4 must keep the default at zero internal-`Nu` fit rows unless
  recirculation, source-envelope, sign/heat-balance, and same-QOI gates pass.

## Do-Not-Do Guardrails

- Do not hide heat residual in internal `Nu`.
- Do not add radiation on top of realized CFD `wallHeatFlux` in replay mode.
- Do not use realized CFD `wallHeatFlux`, CFD `mdot`, validation temperatures,
  imposed CFD cooler duty, realized test-section heat, or residual as
  predictive runtime inputs.
- Do not admit or score a new model from this release package.

## Next Action

Proceed to `TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION` using this
package as the baseline release gate.
