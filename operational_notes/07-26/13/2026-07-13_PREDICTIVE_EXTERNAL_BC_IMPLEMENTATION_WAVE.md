---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/fluid_external_boundary_patch_plan.md
tags: [forward-model, predictive-1d, external-boundary, fluid-handoff]
related:
  - .agent/status/2026-07-13_AGENT-297.md
  - .agent/journal/2026-07-13/predictive-external-bc-implementation-wave.md
task: AGENT-297
date: 2026-07-13
role: Coordinator/Writer
type: operational_note
status: complete
---
# Predictive External BC Implementation Wave

Open first:

1. `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/README.md`
2. `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/cfd_external_boundary_dictionary.csv`
3. `work_products/2026-07/2026-07-13/2026-07-13_predictive_external_bc_implementation_wave/fluid_external_boundary_patch_plan.md`

Current state:

- CFD external-boundary rows are staged for Fluid as a dynamic boundary-table
  contract.
- The external Fluid source tree was inspected read-only; it was not edited.
- The downstream Fluid implementation should add `external_boundary_table`
  rather than overloading `external_prescribed_segment_loss`.
- HX split-aware score rows exist, but hydraulic mdot overprediction remains a
  hard guardrail.
- The forward-predictive map now links this bridge package as the external-BC
  implementation handoff.

Do not do:

- Do not add radiation on top of realized CFD `wallHeatFlux`.
- Do not treat E1/E2 wall-shell/beta results as validated wall-layer closure.
- Do not fit internal Nu/UA/HTC or sensor offsets in the next Fluid patch.
- Do not claim end-to-end prediction while forward-v0 mdot is still biased high.

Next implementation task:

Claim a writable Fluid row, then implement the exact patch plan in
`fluid_external_boundary_patch_plan.md`, starting with tests around emissivity,
`Tsur`, fixed-loss replay separation, and segment-state diagnostics.
