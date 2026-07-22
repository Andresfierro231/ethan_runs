---
task: TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Hydraulics / cfd-pp / Implementer / Tester / Writer
type: work_product
status: complete_fail_closed_diagnostic_masks
tags: [upcomer, recirculation, control-volume, segmentation, s13, s14, no-admission]
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s14_pressure_f6_nonrecirc_anchor_evidence
---
# S13/S14 Recirculation Control-Volume Segmentation Preflight

This package implements the first recovery step after the geometry contract
failed closed. It reads the validated whole-mesh cell VTKs, builds right-leg
velocity-topology reverse-flow candidate masks, and decides whether those masks
are strong enough to release the exchange interface and wall/core lanes.

## Decision

- cases processed: `3`
- candidate masks generated: `3`
- released recirculation control volumes: `0`
- exchange-interface rows released: `0`
- wall/core rows released: `0`
- S14 F6/component-K admissions: `0`
- surface extraction launched: `false`
- exchange-cell harvest launched: `false`

The masks are useful diagnostic starting points, but they are not released as
face-closed recirculation control volumes. A future row must derive face
neighbors/internal faces from mesh topology before `mdot_exchange`, `Q_wall_W`,
or wall/core thermal contrast can be computed.

## Outputs

- `recirc_segmentation_case_summary.csv`
- `recirc_component_summary.csv`
- `masks/*_right_leg_reverse_flow_candidate_mask.csv`
- `exchange_interface_derivation_preflight.csv`
- `wall_core_band_derivation_preflight.csv`
- `s14_pressure_anchor_recirc_linkage.csv`
- `no_mutation_guardrails.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

No native solver outputs, registry/admission state, scheduler state, Fluid or
external source, surface VTK extraction, sampler/harvest, fitting, component
`K`, F6 admission, S11/S15 trigger, or residual absorption into internal `Nu`
is changed by this package.
