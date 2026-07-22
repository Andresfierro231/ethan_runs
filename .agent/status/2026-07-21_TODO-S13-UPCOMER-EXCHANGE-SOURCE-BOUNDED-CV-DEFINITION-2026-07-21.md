---
provenance:
  - tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py
  - tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/release_decision.csv
tags: [s13, upcomer, exchange-cell, source-bounded-cv, s12, fail-closed, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-source-bounded-cv-definition.md
  - imports/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_roi_patch_alignment_audit
task: TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-SOURCE-BOUNDED-CV-DEFINITION-2026-07-21

## Objective

Integrate the completed S13 topology release, topology-forensics alternate-CV
gate, sampler gaps, interface/wall/source recovery, and S12 thermal-shape
contract into one source-bounded CV release decision.

## Outcome

Complete, fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition/`.

Key results:

- Source-bounded CV rows released: `0/3`.
- S13 sampler ready: `false`.
- S12-HIAX1 unlocked: `false`.
- Surface extraction allowed: `false`.
- Sampler or harvest allowed: `false`.
- Salt2/Salt3/Salt4 diagnostic largest-component interface faces:
  `9796/10094/10238`.
- Salt2/Salt3/Salt4 topology wall faces: `0/0/0`.
- Salt2/Salt3/Salt4 alternate right-leg wall-contact faces: `0/6/15`.

The result does not admit a new exchange-cell CV. S12-HIAX1 remains blocked
because it still lacks released exchange-state QOIs and source-bounded same-QOI
UQ inputs.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py`.
- Added `tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py`.
- Generated:
  - `recirc_cv_cells.csv`
  - `exchange_interface_faces.csv`
  - `trusted_wall_faces.csv`
  - `wall_core_band.csv`
  - `normal_convention.csv`
  - `source_sink_boundary_ledger.csv`
  - `release_decision.csv`
  - `s12_unlock_gate.csv`
  - `next_task_queue.csv`
  - `summary.json`, `source_manifest.csv`, `no_mutation_guardrails.csv`, and
    `README.md`
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py tools/extract/test_s13_upcomer_exchange_source_bounded_cv_definition.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_source_bounded_cv_definition`:
  passed, `4` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_source_bounded_cv_definition.py`:
  passed, emitted `released_case_count=0`,
  `s13_sampler_ready=false`, and `s12_hiax1_unlocked=false`.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition --strict`:
  passed, `candidate_rows=0 findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_source_bounded_cv_definition`:
  passed.

## Unresolved Blockers

- No source-bounded S13 control volume has released across all three train
  cases.
- S13 sampler manifest refresh, surface extraction, wall/source `Q_wall_W`,
  harvest, and same-QOI UQ remain blocked.
- S12-HIAX1 implementation and freeze remain blocked because released
  exchange-state QOIs do not exist.
- Next useful unblock is a right-leg ROI/wall-patch alignment audit followed
  by a predeclared geometry-backed seed if the audit confirms misalignment.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing launched: no.
- Surface VTK extraction launched: no.
- Sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, threshold relaxation, exchange-cell
  admission, S11/S12/S13/S15/S6 trigger, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
