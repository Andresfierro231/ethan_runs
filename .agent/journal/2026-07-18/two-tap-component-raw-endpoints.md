---
provenance:
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/next_raw_postprocessing_queue.csv
  - work_products/2026-07/2026-07-17/2026-07-17_two_tap_component_repair_extractor/two_tap_component_repair_output.csv
  - work_products/2026-07/2026-07-14/2026-07-14_hydraulic_tap_length_admission_refresh/tap_centerline_length_table.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_component_raw_endpoint_plan/summary.json
tags: [pressure-ledger, two-tap, raw-endpoints, component-k, f6]
related:
  - .agent/status/2026-07-18_TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS.md
  - imports/2026-07-18_two_tap_component_raw_endpoints.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS
date: 2026-07-18
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
---
# Two-Tap Component Raw Endpoints

## Attempted

Claimed `TODO-TWO-TAP-COMPONENT-RAW-ENDPOINTS` and converted the AGENT-530
`next_raw_postprocessing_queue.csv` into a concrete raw sampling contract.
Implemented `tools/analyze/build_two_tap_component_raw_endpoint_plan.py` plus
focused tests.

## Observed

The queue contains five missing artifact classes: raw feature endpoint pressure
surfaces, final pressure/velocity basis, physically comparable straight
reference, same-window RAF/RMF/SVF, and same-QOI mesh/time uncertainty.

The exact `corner_lower_right` endpoint mapping is available from the tap-length
refresh:

- start/upstream patch `ncc_pipeleg_lower_09_fitting_end`
- end/downstream patch `ncc_pipeleg_right_01_lower_start`
- station labels `lower_leg__s04` to `right_leg__s00`
- centerline endpoint distance `0.15020855004 m`

AGENT-440 preflight supplies the same staged-copy time windows and source case
paths: Salt2 `7915`, Salt3 `7618`, Salt4 `10000`.

## Inferred

The next useful action is not another extractor over existing data. It is a
staged-copy raw sampling task that emits finite endpoint `p`/`p_rgh`, local
velocity/density/dynamic-pressure basis, same-window reverse-flow metrics, and
same-QOI uncertainty status for exactly those endpoint surfaces.

The current negative `K_local` values remain a basis/isolation failure. They
cannot be clipped or used to tune friction. This task is related to
`f6-friction-re-correction` only because pressure evidence is missing; it does
not fit F6 and does not admit component K.

## Contradictions Or Caveats

The earlier staged raw-pressure precedent sampled `left_lower_leg__s00` to
`left_upper_leg__s04`. That precedent is useful for source paths and staging
pattern, but it is the wrong feature for this contract and must not be
substituted for `corner_lower_right`.

Mesh/time UQ is still a requirement, not evidence. If the future sampler cannot
find a mesh/time family for the same pressure-loss QoI, the row must explicitly
remain diagnostic.

## Next Useful Actions

1. Claim a separate staged-copy cfd-pp row.
2. Stage read-only copies of the three source cases into a task-owned `tmp/`
   or `work_products/` path.
3. Sample `lower_leg__s04` and `right_leg__s00` surfaces for `p`, `p_rgh`, `U`,
   `T_or_rho`, flux, face area, and face normal at `7915/7618/10000`.
4. Emit RAF/RMF/SVF and same-QOI uncertainty status with the raw pressure files.
5. Build a new extractor/admission review from the raw output; do not overwrite
   AGENT-530 and do not admit F6/component K unless all gates pass.
