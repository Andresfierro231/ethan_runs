---
provenance:
  - tools/analyze/build_s13_upcomer_exchange_qwall_neighbor_window_sampling.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/same_qoi_uq_matrix.csv
tags: [status, s13, upcomer-exchange, qwall, neighbor-window, same-qoi-uq, fail-closed]
related:
  - .agent/journal/2026-07-22/s13-upcomer-exchange-qwall-neighbor-window-sampling.md
  - imports/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling.json
task: TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22

## Objective

Locate or generate from existing read-only fields exact same-label
target-minus / target / target-plus rows for `Q_wall_W`,
`mdot_exchange_positive_outward_proxy_kg_s`, `tau_recirc_proxy_s`, and
`wall_core_bulk_temperature_contrast_K`.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling/`.

Decision: `target_minus_sampled_target_plus_missing_fail_closed`.

Key results:

- cases sampled: `3`
- requested QOI labels: `4`
- target rows ready: `12`
- target-minus rows sampled: `12`
- target-plus rows sampled: `0`
- same-QOI neighbor UQ-ready labels: `0`
- move to mesh/GCI UQ allowed now: `false`
- production harvest allowed now: `false`
- admission/S11/S12/S13/S15/S6 trigger: `false`

The row partially unblocks the previous evidence gap: target-minus values now
exist for all requested case/QOI combinations. The remaining blocker is
target-plus. Salt2 target `7915`, Salt3 target `7618`, and Salt4 target `10000`
are the latest stored native `processors64` time directories, so no later
same-label window exists in the current source tree.

## Changes Made

- Added `tools/analyze/build_s13_upcomer_exchange_qwall_neighbor_window_sampling.py`.
- Added `tools/analyze/test_s13_upcomer_exchange_qwall_neighbor_window_sampling.py`.
- Generated package outputs:
  `neighbor_time_selection.csv`, `native_window_sampling_summary.csv`,
  `same_qoi_neighbor_window_rows.csv`, `same_qoi_uq_matrix.csv`,
  `production_readiness_gate.csv`, `source_manifest.csv`,
  `no_mutation_guardrails.csv`, `summary.json`, and `README.md`.
- Added this status file, journal entry, and import manifest.

## Validation

- `python3.11 tools/analyze/build_s13_upcomer_exchange_qwall_neighbor_window_sampling.py`:
  passed.
- `python3.11 -m py_compile tools/analyze/build_s13_upcomer_exchange_qwall_neighbor_window_sampling.py tools/analyze/test_s13_upcomer_exchange_qwall_neighbor_window_sampling.py`:
  passed.
- `python3.11 -m unittest tools.analyze.test_s13_upcomer_exchange_qwall_neighbor_window_sampling`:
  passed, `3` tests.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling`:
  passed.
- `python3.11 -m json.tool imports/2026-07-22_s13_upcomer_exchange_qwall_neighbor_window_sampling.json`:
  passed.
- `python3.11 tools/docs/build_repo_index.py --check`:
  passed, `blocker register OK (15 entries)`.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-QWALL-NEIGHBOR-WINDOW-SAMPLING-2026-07-22`:
  passed.

## Unresolved Blockers

S13 same-QOI UQ remains blocked until later target-plus rows exist with the same
QOI labels, formulas, sign conventions, and geometry basis. Mesh/GCI UQ is not
reached. Production harvest and coefficient admission remain closed.

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, not mutated.
- Registry/admission state: not mutated.
- Scheduler/solver/postprocessing/sampler/harvest/UQ: not launched.
- `Q_wall_W`: target-minus sampled for this package only; no production release
  or re-release.
- Source/property release: not changed.
- Source-side heat flow: not relabeled as `Q_wall_W`.
- Coefficient admission and S11/S12/S13/S15/S6 triggers: not allowed.
- Thesis current files, Fluid/external repositories, and blocker register: not
  edited.
- Residual absorption into internal Nu: not allowed.
