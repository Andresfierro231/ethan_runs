---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_0_baseline_release_gate/README.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - reports/2026-07/2026-07-09/2026-07-09_external_boundary_setup_reference/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_phase_1_external_bc_radiation_integration/README.md
tags: [journal, thermal-modeling, external-boundary, radiation]
related:
  - .agent/status/2026-07-21_TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION.md
  - imports/2026-07-21_heatloss_phase_1_external_bc_radiation_integration.json
task: TODO-HEATLOSS-PHASE-1-EXTERNAL-BC-RADIATION-INTEGRATION
date: 2026-07-21
role: Implementer/Tester/Writer/Thermal-modeling
type: journal
status: complete
supersedes: []
superseded_by:
---
# Heat-Loss Phase 1 External BC And Radiation Integration

## Attempted

Claimed Phase 1 and built a reproducible repo-local external BC/radiation
contract package from existing setup, patch-role, and Phase 0 release-gate
evidence.

## Observed

The patch-role evidence already exposes fields that a first-class external BC
dictionary needs: case, patch, role, role group, area, `h`, `Ta`, `Tsur`,
emissivity, layer metadata, wallHeatFlux diagnostic paths, and radiation
metadata status. The radiation map and setup reference both state that
`rcExternalTemperature` radiation is active but inseparable from total
`wallHeatFlux`.

The prior external-boundary dictionary supplies 24 segment/role rows across
Salt2/Salt3/Salt4. The Phase 1 package now preserves those rows in
`external_bc_segment_role_audit.csv`, with cooler source/sink rows explicitly
labeled unavailable for passive external-boundary use rather than filled from
residuals.

## Inferred

The immediate correction is a mode contract: predictive rows may compute
external convection and radiation from setup fields, while replay rows may use
total CFD `wallHeatFlux` only if separate external convection and radiation are
disabled. That mode split is enough to unblock Phase 2 evidence planning and
future implementation rows without editing Fluid now.

The analytic Stefan-Boltzmann tests are deliberately small contract tests, not
a heat-loss score. They prove the sign/zero-emissivity/linearized-`h_rad` and
replay no-double-counting semantics needed by later Fluid/API work.

## Contradictions Or Caveats

This package proves the dictionary coverage and radiation semantics at contract
level, not at Fluid source level. `TODO-FLUID-EXTERNAL-BC-DICT` and
`TODO-1D-RADIATION-CAPABILITY` remain open for implementation, ledgers, and
score-ready tests.

## Next Useful Actions

1. Run Phase 2 split heat-loss evidence.
2. Keep radiation-off rows labeled sensitivity only.
3. Do not score Phase 3 wall/test-section candidates until Phase 2 has split
   missing fields and residual owners.
