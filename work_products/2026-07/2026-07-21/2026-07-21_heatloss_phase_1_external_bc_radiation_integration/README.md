---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_0_baseline_release_gate/heat_path_release_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_thermal_heat_loss_contract_alignment/heat_loss_path_contract.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_cfd_radiative_boundary_guidance/cfd_emissivity_by_run.csv
  - operational_notes/maps/thermal-boundary-and-radiation.md
tags: [thermal-modeling, external-boundary, radiation, heat-loss, fluid-walls]
related:
  - .agent/BOARD.md
  - TODO-FLUID-EXTERNAL-BC-DICT
  - TODO-1D-RADIATION-CAPABILITY
  - TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE
task: TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 1 External BC And Radiation Integration

## Decision

Phase 1 releases a repo-local external-boundary dictionary contract, segment-role
coverage audit, radiation semantics audit, and analytic radiation contract. It
does not edit external Fluid, launch postprocessing, score a model, fit a
coefficient, or admit a candidate.

The runtime distinction is fixed:

- Predictive mode computes external convection and radiation from setup fields
  and solved states.
- Replay mode may consume realized total CFD `wallHeatFlux`, but then separate
  external convection and radiation terms are disabled.
- Radiation-off rows are sensitivity rows only, not CFD parity.

## Observed Facts

- Mainline Salt `rcExternalTemperature` patches carry emissivity and `Tsur`
  metadata.
- Existing evidence says radiation is embedded in total OpenFOAM `wallHeatFlux`;
  there is no separate exported `qr` heat term in the cited outputs.
- The prior external-boundary dictionary provides `24`
  segment/role rows across `3` cases. Rows with unavailable
  passive boundary fields are explicitly labeled instead of being filled from a
  residual.
- Phase 0 marks these as forbidden predictive runtime inputs: realized CFD
  `wallHeatFlux`, CFD `mdot`, validation temperatures, imposed CFD cooler duty,
  and heat residual.

## Outputs

- `external_bc_dictionary_contract.csv`
- `external_bc_segment_role_audit.csv`
- `runtime_mode_matrix.csv`
- `radiation_semantics_audit.csv`
- `radiation_analytic_tests.csv`
- `fluid_handoff_contract.csv`
- `validation_report.json`
- `source_manifest.csv`
- `summary.json`

## Current Blockers

- `TODO-FLUID-EXTERNAL-BC-DICT` remains the first-class implementation row for
  Fluid/API source integration.
- `TODO-1D-RADIATION-CAPABILITY` remains open for executable 1D radiation terms,
  ledgers, and sensitivity tables.
- Phase 2 still needs split heat-loss evidence, especially explicit `qr`
  absence/presence and storage/source status.

## Do-Not-Do Guardrails

- Do not add separate radiation on top of realized CFD `wallHeatFlux`.
- Do not call radiation-off replay CFD parity.
- Do not back-calculate missing `qr`, contact resistance, storage, or external
  convection from residual.
- Do not hide heat residual in internal `Nu`.

## Next Action

Run `TODO-HEATLOSS-PHASE-2-SPLIT-HEAT-LOSS-EVIDENCE` before any Phase 3
wall/test-section model score consumes this schema.
