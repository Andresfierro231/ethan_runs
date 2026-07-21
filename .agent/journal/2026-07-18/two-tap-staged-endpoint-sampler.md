---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/pressure_surface_sampling_contract.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/research_path_matrix.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/sampler_preflight.csv
tags: [pressure-ledger, two-tap, raw-endpoints, blocker]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER.md
  - imports/2026-07-18_two_tap_staged_endpoint_sampler.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Staged Endpoint Sampler

## Attempted

Claimed a new hydraulics/cfd-pp row and implemented the first executable
roadmap path after the two-tap raw endpoint contract. The builder reads the
existing target and pressure-surface contracts, validates the exact cases,
times, labels, and fields, emits a staged mesh-station cutting-plane sampler,
and includes a strict VTK harvest parser for raw endpoint reductions.

## Observed

The three continuation source paths exist and their exact time directories
contain the required fields `p`, `p_rgh`, `U`, `rho`, and `T`.

The declared NCC endpoint patch labels are present in `constant/polyMesh`, but
they have zero boundary faces in the reconstructed mesh. The same is true for
the generated nonconformal couple/error endpoint labels inspected for Salt2.
Existing source `postProcessing` output does not already contain
`lower_leg__s04` or `right_leg__s00` endpoint plane files for the target runs.

Older section-mean pressure products are useful precedent for mesh-station
planes, but they are not substituted because the new contract requires static
`p`, `p_rgh`, `U`, `rho`/`T`, face area, normal, and recirculation metrics from
the same raw surfaces.

## Inferred

The correct implementation path is not `surfaceFieldValue` on the declared NCC
patches. It is a staged, read-only view of each continuation case with a
two-plane VTK `surfaces` function object at mesh stations `lower_leg__s04` and
`right_leg__s00`. The generated parser can then compute area-weighted pressure,
bulk velocity, density/temperature basis, mass flux, RAF, RMF, and SVF without
inventing endpoint pressure.

## Caveats

The sampler package did not submit Slurm work. `raw_endpoint_pressure_velocity.csv`
therefore contains six explicit `missing_raw_surface_file` rows and zero
sampled rows. The positive normal policy uses the opposite of the mesh-station
tangent for this corner feature, matching the prior observed sign of nominal
flow at both endpoint labels; a later pressure/velocity basis audit should
retain that policy in its provenance and not silently flip signs after seeing
K.

## Next Useful Actions

Submit the generated sbatch script on a compute node, harvest the VTK outputs
with the same builder, and then open a new task for the pressure/velocity basis
audit. Do not start straight-reference/component-isolation, same-QOI UQ, F6, or
component-K admission before six endpoint rows are `sampled`.
