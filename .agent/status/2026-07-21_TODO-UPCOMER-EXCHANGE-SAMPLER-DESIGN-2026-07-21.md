---
provenance:
  - tools/extract/sample_upcomer_exchange_cell.py
  - tools/extract/test_sample_upcomer_exchange_cell.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/summary.json
tags: [upcomer, recirculation, exchange-cell, sampler-design, no-solver, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-sampler-design.md
  - imports/2026-07-21_upcomer_exchange_sampler_design.json
  - work_products/2026-07/2026-07-21/2026-07-21_heatloss_upcomer_exchange_evidence_extraction/README.md
task: TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21
date: 2026-07-21
role: Implementer/Tester/Writer/Hydraulics/Thermal-modeling
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21

## Objective

Implement the sampler-design dry row for the upcomer throughflow plus
recirculation/exchange-cell path. The task was to define and fixture-test the
exchange-cell output schema without reading native solver fields, launching
OpenFOAM, fitting coefficients, or changing admission state.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design/`.

Key results:

- required schema fields: `10`;
- dry extraction plan rows: `3`;
- fixture validation rows: `2`;
- no-launch guardrail rows: `5`;
- next-agent handoff rows: `3`;
- compute execution allowed from this row: `false`;
- fit/admission/scorecard allowed now: `false`.

The new dry sampler design defines output fields for `R_mu`, `R_rho`,
`V_recirc`, `mdot_exchange`, `tau_recirc`, `T_main`, `T_recirc`,
`wall_core_delta_T`, `pressure_residual`, and `energy_residual`. Synthetic VTK
fixture tests cover volume integration, bidirectional exchange flux, residence
time, thermal weighting, pressure residuals, energy residuals, and explicit
unavailable-field status for missing viscosity.

## Changes Made

- Added `tools/extract/sample_upcomer_exchange_cell.py`.
- Added `tools/extract/test_sample_upcomer_exchange_cell.py`.
- Generated the upcomer exchange sampler-design work product.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m unittest tools.extract.test_sample_upcomer_exchange_cell`:
  passed, `6` tests.
- `python3.11 -m py_compile tools/extract/sample_upcomer_exchange_cell.py tools/extract/test_sample_upcomer_exchange_cell.py`:
  passed.
- `python3.11 tools/extract/sample_upcomer_exchange_cell.py`:
  passed; generated `10` schema rows, `3` dry plan rows, `2` fixture rows,
  `5` guardrail rows, and `3` handoff rows.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_sampler_design`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-UPCOMER-EXCHANGE-SAMPLER-DESIGN-2026-07-21`:
  passed; found status, journal, and import artifacts.

## Unresolved Blockers

- No native CFD extraction has been run with this schema.
- The compute-node execution row still must produce actual cell/interface/wall
  outputs for salt 2, salt 3, and salt 4 queued windows.
- Same-QOI UQ must still be paired to the exact exchange-state and residual
  QOIs before Phase 4B rescore.
- Phase 4B, Phase 5, and S6 remain blocked until extraction and UQ gates pass.

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
- Phase 4B rescore run: no.
- Phase 5/S6 trigger changed: no.
