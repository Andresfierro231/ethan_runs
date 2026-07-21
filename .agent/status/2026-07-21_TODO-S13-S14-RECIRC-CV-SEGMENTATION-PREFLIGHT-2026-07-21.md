---
provenance:
  - tools/extract/build_s13_s14_recirc_cv_segmentation_preflight.py
  - tools/extract/test_s13_s14_recirc_cv_segmentation_preflight.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/recirc_segmentation_case_summary.csv
tags: [upcomer, recirculation, control-volume, segmentation, s13, s14, status]
related:
  - .agent/journal/2026-07-21/s13-s14-recirc-cv-segmentation-preflight.md
  - imports/2026-07-21_s13_s14_recirc_cv_segmentation_preflight.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_geometry_contract/README.md
task: TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-S14-RECIRC-CV-SEGMENTATION-PREFLIGHT-2026-07-21

## Objective

Implement the first S13/S14 geometry unlock: use validated Salt2/Salt3/Salt4
whole-mesh cell VTK velocity fields to produce reproducible recirculation
control-volume segmentation preflight masks or fail-closed blockers, and link
the result back to S14 pressure/F6 anchor status without fitting or admitting
component `K`/F6.

## Outcome

Complete as diagnostic-mask/fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/`.

Key results:

- Salt2: `863270` right-leg ROI cells, `136140` reverse-flow candidates,
  largest component `71775` cells, largest fraction `0.527214632`.
- Salt3: `863270` right-leg ROI cells, `138382` reverse-flow candidates,
  largest component `73349` cells, largest fraction `0.530047260`.
- Salt4: `863270` right-leg ROI cells, `139994` reverse-flow candidates,
  largest component `74256` cells, largest fraction `0.530422732`.
- Candidate masks generated for all three cases under `masks/`.
- Released recirculation control volumes: `0`.
- Released exchange-interface rows: `0`.
- Released wall/core rows: `0`.
- S14 component `K`/F6 admitted rows: `0`.

The reverse-flow topology is real and reproducible, but it is fragmented under
the current VTK-only point-connectivity preflight. The largest component is
only about `53%` of reverse-flow candidates in each case, so this row does not
release a face-closed recirculation control volume. Exchange-interface,
wall/core, `Q_wall_W`, exchange harvest, and F3-vs-F6 scoring remain blocked.

## Changes Made

- Added `tools/extract/build_s13_s14_recirc_cv_segmentation_preflight.py`.
- Added `tools/extract/test_s13_s14_recirc_cv_segmentation_preflight.py`.
- Generated `recirc_segmentation_case_summary.csv`,
  `recirc_component_summary.csv`, per-case diagnostic mask CSVs,
  `exchange_interface_derivation_preflight.csv`,
  `wall_core_band_derivation_preflight.csv`, and
  `s14_pressure_anchor_recirc_linkage.csv`.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_s14_recirc_cv_segmentation_preflight.py tools/extract/test_s13_s14_recirc_cv_segmentation_preflight.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_s14_recirc_cv_segmentation_preflight`:
  passed, `3` tests.
- `python3.11 tools/extract/build_s13_s14_recirc_cv_segmentation_preflight.py`:
  passed; generated three diagnostic masks and fail-closed release decision.
- `python3.11 tools/agent/runtime_input_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight`:
  passed.
- `python3.11 tools/agent/source_property_gate.py work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight --strict`:
  passed, `candidate_rows=0`, `findings=0`.
- `python3.11 tools/agent/split_policy_lint.py work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight`:
  passed.

## Unresolved Blockers

- The current mask is not face-closed. Next work must derive face-neighbor
  topology from the mesh/cell connectivity and prove the recirculation volume
  boundary before releasing an exchange interface.
- Wall/core band and `Q_wall_W` remain blocked until the released volume is
  intersected with trusted wall-face adjacency.
- S14 pressure/F6 remains diagnostic or future-candidate only; F3 comparison
  remains `not_evaluated_no_admitted_or_ordinary_candidate`.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/surface extraction/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, component `K`, or F6 admission changed: no.
- Exchange-cell admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- S11/S15 triggered: no.
- Residual absorbed into internal `Nu`: no.
