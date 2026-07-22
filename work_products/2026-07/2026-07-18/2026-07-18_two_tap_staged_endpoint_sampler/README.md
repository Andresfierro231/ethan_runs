---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/target_feature_taps.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/pressure_surface_sampling_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/next_step_queue.csv
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER.md
  - .agent/journal/2026-07-18/two-tap-staged-endpoint-sampler.md
task: TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: work_product
status: complete
---
# Two-Tap Staged Endpoint Sampler

Generated: `2026-07-18T20:27:14.426062+00:00`

## Result

This package implements the first executable research path from the blocker
roadmap: staged raw endpoint sampling for Salt2/Salt3/Salt4
`corner_lower_right`. The declared NCC patch names are preserved as provenance,
but direct patch sampling is blocked because the reconstructed boundary entries
have zero faces. The runnable path is therefore mesh-station cutting planes at
`lower_leg__s04` and `right_leg__s00`, with VTK output so face area, normals,
velocity, pressure, density, temperature, and reverse-flow metrics can be
computed from the same raw surfaces.

The sampler package is complete and raw endpoint evidence has been harvested from staged VTK surfaces. The harvest recorded job `3302464` when provided. These rows are raw diagnostic evidence only; they do not admit component K or fit F6.

## Outputs

- `case_sampling_plan.csv`
- `sampler_preflight.csv`
- `endpoint_surface_target_manifest.csv`
- `raw_endpoint_surface_file_manifest.csv`
- `raw_endpoint_pressure_velocity.csv`
- `sampler_readiness_or_failure.csv`
- `scripts_manifest.csv`
- `source_manifest.csv`
- `summary.json`

## Current Counts

- Target cases: `3`
- Endpoint surfaces: `6`
- Preflight failures: `0`
- Raw sampled rows: `6`
- Raw missing rows: `0`
- Direct NCC patch sampling viable rows: `0`
- Scheduler jobs submitted by this package: `0`

## How To Advance

Open a separate pressure/velocity basis audit task before computing loss terms. Do not run F6 fitting or component-K admission directly from this sampler package.

## Guardrails

No native CFD/OpenFOAM output was mutated. No registry, admission state, Fluid
source, F6 fit, component-K admission, or generated documentation index was
changed. This package does not infer endpoint pressure from older proxy rows.
