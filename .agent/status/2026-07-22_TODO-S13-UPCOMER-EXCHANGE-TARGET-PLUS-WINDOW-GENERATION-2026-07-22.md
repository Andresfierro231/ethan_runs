---
provenance:
  - tools/extract/build_s13_upcomer_exchange_target_plus_window_generation.py
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/job_terminal_status.csv
tags: [status, s13, upcomer-exchange, target-plus, openfoam, slurm]
related:
  - .agent/journal/2026-07-22/s13-upcomer-exchange-target-plus-window-generation.md
  - imports/2026-07-22_s13_upcomer_exchange_target_plus_window_generation.json
task: TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Scheduler / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22

## Objective

Stage minimal target-plus continuation clones for nominal Salt2/Salt3/Salt4 and
submit Slurm jobs to generate `processors64/7916`, `processors64/7619`, and
`processors64/10001` without mutating native source cases.

## Outcome

Complete. Published
`work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation/`
and staged clones under `staging/s13_target_plus_window_generation_2026-07-22/`.

Decision: `target_plus_windows_generated_ready_for_harvest_row`.

Key results:

- staged cases: `3`
- dry-run passed cases: `3`
- submitted jobs: Salt2 `3310047`, Salt3 `3310046`, Salt4 `3310048`
- terminal-success jobs: `3`
- target-plus directories present: `3`
- target-plus QOI rows harvested by this row: `0`
- same-QOI UQ executed by this row: `false`
- production harvest/admission allowed by this row: `false`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_target_plus_window_generation.py`.
- Added `tools/extract/test_s13_upcomer_exchange_target_plus_window_generation.py`.
- Created staged clones for Salt2/Salt3/Salt4 with copied restart state only.
- Patched staged `controlDict` files to run from `latestTime` to target-plus
  windows with `writeInterval 1` and `purgeWrite 0`.
- Generated sbatch scripts and submitted them from `login3` with account
  `ASC23046`.
- Generated package outputs:
  `staged_case_manifest.csv`, `sbatch_manifest.csv`, `dry_run_manifest.csv`,
  `submission_manifest.csv`, `job_terminal_status.csv`, `source_manifest.csv`,
  `no_mutation_guardrails.csv`, `summary.json`, and `README.md`.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_target_plus_window_generation.py tools/extract/test_s13_upcomer_exchange_target_plus_window_generation.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_target_plus_window_generation`:
  passed, `3` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_target_plus_window_generation.py --json`:
  passed; staged `3` clones and dry-run passed `3/3`.
- `sacct -j 3310046,3310047,3310048 --format JobID,JobName,State,ExitCode,Elapsed,End`:
  passed; all three jobs `COMPLETED` with `0:0`.
- Target-plus field presence check:
  `processors64/7916`, `processors64/7619`, and `processors64/10001` exist
  with `U`, `T`, `rho`, and `wallHeatFlux`.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-22/2026-07-22_s13_upcomer_exchange_target_plus_window_generation`:
  passed.
- `python3.11 -m json.tool imports/2026-07-22_s13_upcomer_exchange_target_plus_window_generation.json`:
  passed.
- `python3.11 tools/docs/build_repo_index.py --check`:
  passed, `blocker register OK (15 entries)`.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-TARGET-PLUS-WINDOW-GENERATION-2026-07-22`:
  passed.

## Unresolved Blockers

This row only generated target-plus windows. It did not harvest target-plus QOI
values, execute same-QOI neighbor UQ, run mesh/GCI UQ, run production harvest,
or admit an exchange coefficient. The next row should harvest the four exact
same-label QOIs from staged target-plus outputs and join them to the existing
target-minus/target evidence.

## Guardrails

- Native CFD/OpenFOAM source outputs: read-only, not mutated.
- Staged clone writes: confined to `staging/s13_target_plus_window_generation_2026-07-22/**`.
- Registry/admission state: not mutated.
- Scheduler action: limited to task-owned staged Slurm jobs `3310047`,
  `3310046`, and `3310048`.
- Production harvest, same-QOI UQ, mesh/GCI UQ, coefficient admission, and
  S11/S12/S13/S15/S6 triggers: not performed.
- Thesis current files, Fluid/external repositories, blocker register, and
  generated docs index: not edited by this row before closeout.
- Residual absorption into internal Nu: not allowed.
