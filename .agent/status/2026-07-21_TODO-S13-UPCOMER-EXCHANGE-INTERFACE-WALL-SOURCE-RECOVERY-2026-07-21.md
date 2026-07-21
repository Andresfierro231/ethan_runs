---
provenance:
  generated_by: codex
  generated_at: 2026-07-21
tags:
  - s13
  - upcomer-exchange
  - interface-wall-source
  - fail-closed
related:
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery/interface_wall_source_release_gate.csv
---

# Task TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21

Task: `TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21`

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_interface_wall_source_recovery.py`.
- Added `tools/extract/test_s13_upcomer_exchange_interface_wall_source_recovery.py`.
- Published `work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery/`.
- Output result: `3` case rows, `7` source-evidence rows, `3` ready `cell_vtk` rows, `0` released recirculation CV/interface/wall/normal/`Q_wall_W`/source/UQ rows, `0` sampler-ready rows, and `production_harvest_allowed=false`.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_interface_wall_source_recovery.py tools/extract/test_s13_upcomer_exchange_interface_wall_source_recovery.py` passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_interface_wall_source_recovery` passed: `Ran 4 tests`.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_topology_cv_release tools.extract.test_s13_upcomer_exchange_interface_wall_source_recovery` passed: `Ran 9 tests`.
- `python3.11 tools/extract/build_s13_upcomer_exchange_interface_wall_source_recovery.py` passed.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery` passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery --strict` passed.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_interface_wall_source_recovery` passed.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-INTERFACE-WALL-SOURCE-RECOVERY-2026-07-21` passed.
- `python3.11 tools/docs/build_repo_index.py --check` passed: blocker register OK.

## Guardrails

- Native solver outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver, postprocessing, surface extraction, sampler, or harvest launched: no.
- Fluid or external repo mutated: no.
- Fitting, model selection, S11/S15/S6 trigger, or exchange-cell admission: no.
- Blocker register or generated index mutated: no.
- Residual absorption into internal Nu: no.

## Outcome

Complete fail-closed recovery package. Existing evidence cannot yet unblock S13
production harvest because the diagnostic reverse-flow masks are not released
face-closed recirculation control volumes, and the trusted exchange-interface
VTK, wall/core VTK, normals, `Q_wall_W` or source-side thermal release,
same-window thermal fields, and same-QOI UQ remain missing.
