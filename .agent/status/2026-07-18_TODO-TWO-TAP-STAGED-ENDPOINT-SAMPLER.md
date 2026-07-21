---
provenance:
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/target_feature_taps.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_blocker_roadmap/next_step_queue.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/summary.json
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/journal/2026-07-18/two-tap-staged-endpoint-sampler.md
  - imports/2026-07-18_two_tap_staged_endpoint_sampler.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
---
# TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER Status

## Objective

Implement the next research path for the `corner_lower_right` two-tap raw
endpoint contract: validate exact Salt2/Salt3/Salt4 target times and labels,
identify blockers, prepare staged compute-node sampling, and emit strict raw
pressure/velocity/recirculation harvest artifacts without fitting F6 or
admitting component K.

## Outcome

Complete as a sampler/research package. The package validates:

- Salt2 `7915`, Salt3 `7618`, Salt4 `10000`.
- `lower_leg__s04` upstream and `right_leg__s00` downstream labels.
- Required source fields `p`, `p_rgh`, `U`, `rho`, and `T` exist at all three
  time directories.
- Direct sampling from declared NCC patch names is blocked because both
  endpoint patches have `nFaces=0` in the reconstructed boundary files.
- The viable implementation path is mesh-station VTK cutting planes, with
  strict parsing of face area, pressure, velocity, density, temperature, mass
  flux, RAF, RMF, and SVF.

No raw endpoint samples were harvested in this task; all six raw rows remain
`missing_raw_surface_file` until the generated Slurm script is submitted.

## Changes Made

- `tools/analyze/build_two_tap_staged_endpoint_sampler.py`
- `tools/analyze/test_two_tap_staged_endpoint_sampler.py`
- `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/**`
- `operational_notes/maps/pressure-and-momentum-budget.md`
- `.agent/BOARD.md`
- `.agent/status/2026-07-18_TODO-TWO-TAP-STAGED-ENDPOINT-SAMPLER.md`
- `.agent/journal/2026-07-18/two-tap-staged-endpoint-sampler.md`
- `imports/2026-07-18_two_tap_staged_endpoint_sampler.json`

## Validation

- `python3.11 tools/analyze/build_two_tap_staged_endpoint_sampler.py` passed.
- `python3.11 -m unittest tools.analyze.test_two_tap_staged_endpoint_sampler`
  passed: 6 tests.

## Unresolved Blockers

- Raw VTK surfaces have not been generated; submit
  `work_products/2026-07/2026-07-18/2026-07-18_two_tap_staged_endpoint_sampler/scripts/submit_two_tap_staged_endpoint_sampling.sbatch`
  on Slurm and then run the builder with `--harvest`.
- Direct NCC patch sampling is not viable for these reconstructed cases because
  declared endpoint patch boundary entries have zero faces.
- Pressure/velocity basis audit, straight-reference/component isolation,
  recirculation admission, same-QOI UQ, F6 governance, and component-K admission
  remain future tasks after six sampled raw endpoint rows exist.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated; no job was submitted. Fluid and
external repositories were not edited. Generated docs index files were not
refreshed. No F6 fit, component-K admission, model selection, or endpoint
pressure invention was performed.
