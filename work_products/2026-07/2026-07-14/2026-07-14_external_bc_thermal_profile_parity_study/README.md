---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv
  - work_products/2026-07/2026-07-13/2026-07-13_wall_layer_drive_mapping/external_bc_drive_table.csv
  - work_products/2026-07/2026-07-14/2026-07-14_best_predictive_heat_loss_discrepancy/best_predictive_leg_heat_loss_discrepancy.csv
  - operational_notes/maps/thermal-boundary-and-radiation.md
tags: [thermal-parity, external-boundary, radiation, heat-loss, thesis-source]
related:
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/README.md
task: AGENT-365
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# External-BC and Thermal-Profile Parity Study

## Decision

This package makes the requested 3D-vs-1D heat-release study repeatable and
presentation-ready. It starts from the same heat-path assumptions as Ethan's CFD
setup, then separates external boundary metadata, source/sink contracts,
realized CFD heat fluxes, and the thermal-profile drive problem.

The result is diagnostic/model-form evidence. It does not admit a final
predictive thermal closure because the current best executable model still uses
imposed cooler duty and because wall-adjacent drive corrections have not been
validated under the Salt2/Salt3/Salt4 split.

## Headline

- Cases: `3` (`salt_2`, `salt_3`, `salt_4`).
- Patch contract rows: `207`.
- Segment-equivalent boundary rows: `24`.
- Heat-loss comparison rows: `15`.
- Thermal-profile drive rows: `15`.
- Publication-ready predictive heat-loss rows: `0`.

Main finding: the best current predictive-style model has a near-closed
aggregate heat balance for the wrong reason. It over-loses heat in pipe legs and
under-loses heat in junction/stub connector regions. That points to external
boundary placement, source/sink separation, and wall-adjacent drive as model
changes, not to one global heat-loss multiplier.

## Radiation Policy

The old assumption that CFD has no radiation is superseded. CFD
`rcExternalTemperature` includes emissivity/Tsur effects, and current exported
`wallHeatFlux` is total heat flux with radiation inseparable. Therefore:

- do not add separate 1D radiation on top of realized CFD `wallHeatFlux`;
- do not call radiation-off 1D replay CFD parity;
- setup/predictive parity must carry h, Ta, Tsur, emissivity, and layer metadata.

## Open First

1. `presentation_brief.md`
2. `section_heat_loss_comparison.csv`
3. `thermal_profile_drive_comparison.csv`
4. `external_bc_segment_equivalents.csv`
5. `methodology_and_assumptions.md`
6. `repeatability_and_refinement_guide.md`
7. `thesis_reuse_index.md`

## Files

- `external_bc_patch_contract.csv`
- `external_bc_segment_equivalents.csv`
- `source_sink_parity_contract.csv`
- `section_heat_loss_comparison.csv`
- `thermal_profile_drive_comparison.csv`
- `case_summary.csv`
- `model_change_recommendations.csv`
- `admission_decision_table.csv`
- `source_manifest.csv`
- `methodology_and_assumptions.md`
- `equations_and_sign_conventions.md`
- `presentation_brief.md`
- `repeatability_and_refinement_guide.md`
- `thesis_reuse_index.md`
- `summary.json`
