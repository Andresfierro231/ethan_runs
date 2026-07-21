---
provenance:
  - tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke.py
  - tools/extract/test_build_upcomer_exchange_cell_vtk_salt2_smoke.py
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/summary.json
tags: [upcomer, exchange-cell, cell-vtk, salt2, scheduler, status]
related:
  - .agent/journal/2026-07-21/upcomer-exchange-cell-vtk-salt2-smoke.md
  - imports/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke.json
  - work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_geometry_release/README.md
task: TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21

## Objective

Implement the Salt2 smoke step after geometry release: produce a task-owned
whole-mesh cell VTK for `U`, `T`, and `rho`, validate it against the existing
Salt2 cell-volume CSV, and keep exchange-interface, wall/core, `Q_wall`, sampler
harvest, fit, score, and admission lanes blocked.

## Outcome

Complete with an explicit scheduler caveat. Published
`work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/`.

Key results:

- Salt2 target time: `7915`;
- expected volume cells: `2166996`;
- produced VTK:
  `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/vtk/salt_2_cell_fields.vtk`;
- VTK size: about `426M`;
- VTK validation: `pass`;
- observed `CELL_DATA`: `2166996`;
- observed fields: `T;U;cellID;rho`;
- native output mutation: `false`.

Scheduler caveat: Slurm attempts `3308471`, `3308472`, and `3308473` are all
terminal failed. Attempt `3308472` produced and copied the valid VTK but failed
afterward because the generated validator script lacked repo-root import setup.
The validator and runner were repaired, and the package validation was rerun
successfully on the copied task-owned VTK. No further resubmission was needed.

## Changes Made

- Added `tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke.py`.
- Added `tools/extract/test_build_upcomer_exchange_cell_vtk_salt2_smoke.py`.
- Generated Salt2 package ledgers, scripts, logs, scheduler handoff, and the
  validated cell VTK under the work-product package.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_upcomer_exchange_cell_vtk_salt2_smoke.py tools/extract/test_build_upcomer_exchange_cell_vtk_salt2_smoke.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_build_upcomer_exchange_cell_vtk_salt2_smoke`:
  passed, `3` tests.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scripts/run_salt2_cell_vtk_smoke.sh`:
  passed.
- `bash -n work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scripts/submit_salt2_cell_vtk_smoke.sbatch`:
  passed.
- `work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scripts/run_salt2_cell_vtk_smoke.sh --preflight-only`:
  passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/scripts/validate_salt2_cell_vtk.py work_products/2026-07/2026-07-21/2026-07-21_upcomer_exchange_cell_vtk_salt2_smoke/vtk/salt_2_cell_fields.vtk 2166996 U T rho`:
  passed.
- `python3.11 tools/agent/runtime_input_lint.py ...`:
  passed.
- `python3.11 tools/agent/source_property_gate.py ... --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py ...`:
  passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-UPCOMER-EXCHANGE-CELL-VTK-SALT2-SMOKE-2026-07-21`:
  passed.

## Unresolved Blockers

- Salt3/Salt4 cell VTK extraction remains open; use the repaired runner pattern
  and avoid duplicate submissions.
- `exchange_interface_vtk` remains blocked until a conservative
  main/recirculation interface or internal-face exchange ledger is defined.
- `wall_vtk` and `Q_wall_W` remain blocked until the recirculation wall/core band
  is defined.
- The exchange-cell sampler remains blocked until cell, exchange, wall, and
  source/sink lanes are all populated.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: yes, task-owned Salt2 smoke attempts only.
- OpenFOAM postprocessing launched: yes, task-owned Salt2 staged case only.
- Sampler/harvest execution launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
