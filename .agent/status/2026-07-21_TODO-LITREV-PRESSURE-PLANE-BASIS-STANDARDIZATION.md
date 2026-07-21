---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/next_extraction_queue.csv
tags: [cfd-postprocessing, pressure-ledger, pressure-basis, litrev-contract]
related:
  - .agent/journal/2026-07-21/litrev-pressure-plane-basis-standardization.md
  - imports/2026-07-21_litrev_pressure_plane_basis_standardization.json
task: TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: status
status: complete
---
# TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION Status

## Objective

Standardize existing pressure plane and basis metadata for current station,
branch, two-tap, F6 endpoint, and upcomer matched-plane sources without new
postprocessing or native-output mutation.

## Outcome

Completed the pressure plane/basis standardization package:

- `pressure_plane_basis_standardization.csv`: 460 rows.
- `next_extraction_queue.csv`: 6 actionable follow-up rows.
- `source_manifest.csv`: 15 read-only source references, all present.
- `summary.json`, `README.md`, package builder, and package-local tests.

Row coverage:

- 330 streamwise station pressure-map rows.
- 66 pressure-ladder branch screen rows.
- 18 pressure-term span rows.
- 3 two-tap raw endpoint pair rows.
- 6 two-tap face-level q-ref/flux rows.
- 3 pressure-corner recovery rows.
- 20 F6 planned endpoint rows.
- 12 PM10/upcomer matched-plane target rows.
- 2 live/terminal-gated caveat rows for corrected-Q `3307441` and high-heat
  `3299610`/`3299620`.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION.md`
- `.agent/journal/2026-07-21/litrev-pressure-plane-basis-standardization.md`
- `imports/2026-07-21_litrev_pressure_plane_basis_standardization.json`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/build_litrev_pressure_plane_basis_standardization.py`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/test_litrev_pressure_plane_basis_standardization.py`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/pressure_plane_basis_standardization.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/next_extraction_queue.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/source_manifest.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/summary.json`

## Validation

Commands run:

```bash
python3.11 work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/build_litrev_pressure_plane_basis_standardization.py
python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/build_litrev_pressure_plane_basis_standardization.py work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/test_litrev_pressure_plane_basis_standardization.py
python3.11 work_products/2026-07/2026-07-21/2026-07-21_litrev_pressure_plane_basis_standardization/test_litrev_pressure_plane_basis_standardization.py
python3.11 -c "import json, pathlib; json.loads(pathlib.Path('imports/2026-07-21_litrev_pressure_plane_basis_standardization.json').read_text())"
python3.11 tools/agent/preflight_task.py --task-id TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION
python3.11 tools/agent/finish_task.py --task-id TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION
```

Results:

- Builder completed.
- `py_compile` passed.
- Unit test result: `Ran 4 tests ... OK`.
- Import manifest JSON parse passed.
- `preflight_task.py` passed.
- `finish_task.py` passed.

Note: one earlier parallel validation attempt failed because the test read the
CSV while the builder was rewriting it. Sequential rebuild plus test passed.

## Guardrails

- Native CFD/OpenFOAM outputs: not mutated.
- Registry/admission state: not mutated.
- Scheduler state: not inspected or mutated from this task.
- Solver/postprocessing launch: none.
- Fluid/external repos: not mutated.
- Generated docs index: not refreshed because the active board row forbids
  generated-index edits unless separately claimed.

## Remaining Blockers / Next Useful Action

Immediate next task: claim `TODO-LITREV-SAME-QOI-UQ-EXECUTION` and use
`pressure_plane_basis_standardization.csv` as the pressure-source index.

High-impact blockers:

- Unit normals are not standardized for the broad station map.
- Signed/absolute face flux is absent for broad station/upcomer sources.
- Same-QOI UQ is still missing for current two-tap/F6/upcomer pressure rows.
- F6 endpoint rows require a separate sampler row before evidence exists.
- Latest corrected-Q `3307441` and high-heat `3299610`/`3299620` remain
  terminal-gated for latest/high-heat promotion.
