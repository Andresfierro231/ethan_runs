---
provenance:
  - tools/extract/build_upcomer_exchange_sampler_compute_execution.py
  - tools/extract/test_build_upcomer_exchange_sampler_compute_execution.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/summary.json
tags: [upcomer, recirculation, exchange-cell, sampler, compute-gate, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-sampler-compute-execution.md
  - imports/2026-07-21_upcomer_exchange_sampler_compute_execution.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/README.md
task: TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-SAMPLER-COMPUTE-EXECUTION-2026-07-21

## Objective

Implement the compute-execution gate after the dry upcomer exchange-cell sampler
design. The task was to inspect queued Salt2/Salt3/Salt4 source windows,
determine whether a compute-node sampler launch is scientifically justified,
and publish a no-submit package if prerequisites are incomplete.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/`.

Key results:

- queued windows checked: `3`;
- primary-field-ready windows: `3`;
- field-gap rows: `39`;
- blocking diagnostic gap: `cellVolume`;
- submission decision: `not_submitted_blocked`;
- scheduler action: `false`;
- solver/postprocessing/sampler launched: `false`;
- fit/admission changed: `false`.

All three queued windows have `U`, `T`, `rho`, `p_rgh`, `Re`, `Pr`, `Ri`,
`Gr`, and `Ra`. They do not expose a trusted `cellVolume` field for the same
cell VTK path required by `V_recirc`, `tau_recirc`, and volume-weighted thermal
state. `mu` is optional and should fail soft through `R_mu_status`; a
recirculation mask can fall back to `U dot n`; wall heat-flux evidence remains
diagnostic/support-only and compute-node-only.

## Changes Made

- Added `tools/extract/build_upcomer_exchange_sampler_compute_execution.py`.
- Added `tools/extract/test_build_upcomer_exchange_sampler_compute_execution.py`.
- Generated the compute-execution gate package and future no-submit scaffold.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_sampler_compute_execution.py tools/extract/test_build_upcomer_exchange_sampler_compute_execution.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_sampler_compute_execution`:
  passed, `4` tests.
- `python3.11 tools/extract/build_upcomer_exchange_sampler_compute_execution.py`:
  passed; generated `3` readiness rows and `39` field-gap rows.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/scripts/run_upcomer_exchange_sampler_compute.sh`:
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution/scripts/submit_upcomer_exchange_sampler_compute.sbatch`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_compute_execution`:
  passed.

## Unresolved Blockers

- A trusted cell-volume export or tested mesh-volume parser is still required
  before `V_recirc` can be sampled.
- The future compute script is intentionally a no-submit scaffold that exits
  before OpenFOAM work.
- Same-QOI UQ, Phase 4B rescore, Phase 5, and S6 remain blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/sampler execution launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
