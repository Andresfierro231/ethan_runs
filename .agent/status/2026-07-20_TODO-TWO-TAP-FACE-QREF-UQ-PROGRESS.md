---
provenance:
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/summary.json
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/face_level_qref_flux_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/residual_uq_progress.csv
tags: [pressure-ledger, two-tap, q-ref, same-qoi-uq, f6]
related:
  - .agent/journal/2026-07-20/two-tap-face-qref-uq-progress.md
  - imports/2026-07-20_two_tap_face_qref_uq_progress.json
  - operational_notes/maps/pressure-and-momentum-budget.md
task: TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS
date: 2026-07-20
role: Hydraulics/cfd-pp/Writer
type: status
status: complete
---
# TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS Status

## Objective

Advance the pressure/F6/two-tap frontier by extracting face-level `q_ref`
diagnostics from the existing two-tap VTK surfaces and carrying forward the
same-QOI residual UQ gate.

## Outcome

Complete. The package parses all six harvested `corner_lower_right` VTK
endpoint surfaces and computes face-level positive, negative, absolute, and net
mass flux plus diagnostic `q_ref` values. This is progress over area-mean
endpoint summaries, but the current rows still show material reverse flow, so
the evidence remains diagnostic-only. Same-QOI mesh/time UQ is still missing,
component isolation remains blocked, and no F6 or component-K admission is
allowed.

## Changes Made

- `work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/**`
- `.agent/BOARD.md`
- `.agent/status/2026-07-20_TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS.md`
- `.agent/journal/2026-07-20/two-tap-face-qref-uq-progress.md`
- `imports/2026-07-20_two_tap_face_qref_uq_progress.json`
- `operational_notes/maps/pressure-and-momentum-budget.md`

## Validation

- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/build_two_tap_face_qref_uq_progress.py`
  passed.
- `python3.11 work_products/2026-07/2026-07-20/2026-07-20_two_tap_face_qref_uq_progress/test_two_tap_face_qref_uq_progress.py`
  passed: 5 tests.
- `python3.11 tools/docs/build_repo_index.py --check`
  passed.
- `python3.11 tools/agent/preflight_task.py --task-id TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS`
  passed: no conflicts detected.
- `python3.11 tools/agent/finish_task.py --task-id TODO-TWO-TAP-FACE-QREF-UQ-PROGRESS`
  passed.

## Unresolved Blockers

- Same-QOI mesh/time UQ for the residual remains missing.
- Material reverse flow still blocks ordinary `q_ref`, component `K`, and F6.
- Component isolation remains apparent/cluster-only.
- A future non-recirculating same-topology anchor is still needed for ordinary
  `K` contrast.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. Scheduler state was not mutated. Fluid and external repositories were
not edited. No solver/postprocessing launch, F6 fit, component-K admission,
ordinary-K promotion, hidden global multiplier, clipped K, model selection, or
endpoint-pressure invention was performed.
