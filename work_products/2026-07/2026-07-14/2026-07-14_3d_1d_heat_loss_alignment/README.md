---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/section_heat_balance.csv
  - work_products/2026-07/2026-07-13/2026-07-13_patch_boundary_fixed_mdot_1d_parity/fixed_mdot_parity_results.csv
  - work_products/2026-07/2026-07-13/2026-07-13_cfd_bc_no_radiation_1d_parity/section_heat_loss_comparison.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/case_runtime_inputs_forward_v0.csv
tags: [thermal-parity, heat-loss, cfd-to-1d, thesis-source, methodology]
related:
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - operational_notes/maps/forward-predictive-model.md
  - reports/thesis_dossier/README.md
task: AGENT-350
date: 2026-07-14
role: Implementer/Tester/Writer
type: work_product
status: complete
---
# 3D vs 1D Heat-Loss Alignment

## Decision

This package starts the requested heat-loss study. It compares where Ethan's
3D CFD model adds/removes heat against where current fixed-mdot 1D replay modes
add/remove heat for Salt2-4 mainline rows.

The result is **diagnostic parity evidence**, not a predictive closure. The
study uses CFD mdot and realized `wallHeatFlux` only to locate heat-path
mismatches. Those quantities remain forbidden runtime inputs for setup-only
forward prediction.

## Headline

- Cases: `3`
- Segment alignment rows: `90`
- Role/lane rows: `63`
- Assumption rows: `21`
- Publication-ready predictive heat-loss rows: `0`

The package confirms the study has started and gives thesis-ready tables for
same-assumption heat-path bookkeeping. It also keeps the key caveat explicit:
`rcExternalTemperature` radiation is embedded in total CFD `wallHeatFlux`, so
there is no separate radiation heat term to add during realized-wallFlux replay.

## Files

- `assumption_match_matrix.csv`
- `heat_loss_alignment_by_segment.csv`
- `heat_loss_alignment_by_role.csv`
- `case_heat_loss_summary.csv`
- `source_manifest.csv`
- `methodology_and_assumptions.md`
- `thesis_presentation_notes.md`
- `summary.json`
