---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/endpoint_pair_pressure_deltas.csv
tags: [pressure-ledger, f6, endpoint-pairs, same-qoi-uq]
related:
  - .agent/journal/2026-07-20/f6-endpoint-pair-same-qoi-uq-preflight.md
  - imports/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight.json
task: TODO-F6-ENDPOINT-PAIR-SAME-QOI-UQ-PREFLIGHT
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-F6-ENDPOINT-PAIR-SAME-QOI-UQ-PREFLIGHT

## Objective

Perform the feasible endpoint-pair and same-QOI UQ preflight for the non-upcomer F6 branches without admitting F6 or component K.

## Outcome

- status: complete
- output: work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight
- endpoint_pair_rows: 6
- diagnostic_mesh_spread_rows: 2
- f6_fit_admission: none

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-F6-ENDPOINT-PAIR-SAME-QOI-UQ-PREFLIGHT.md`
- `.agent/journal/2026-07-20/f6-endpoint-pair-same-qoi-uq-preflight.md`
- `imports/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight.json`
- `work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/**`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/build_f6_endpoint_pair_same_qoi_uq_preflight.py` passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight/test_f6_endpoint_pair_same_qoi_uq_preflight.py` passed: 6 tests.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_pair_same_qoi_uq_preflight --warn` passed with `candidate_rows=0 findings=0`.
- `python3.11 tools/docs/build_repo_index.py --check` and `finish_task.py` are run during closeout.

## Remaining Blockers

- Raw face-level RAF/RMF reverse-flow metrics are still missing for the selected endpoint planes.
- Same-QOI time-window sensitivity is still missing for all six branch rows.
- Salt2 mesh spread is diagnostic only until mesh-ratio/order and retained-window provenance support a GCI-style claim.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not mutated. Scheduler state was not mutated. No solver/postprocessing launch, F6 fit, component-K admission, hidden global multiplier, clipped K, or endpoint-pressure invention was performed.
