---
provenance:
  - tools/extract/build_s13_upcomer_exchange_topology_cv_release.py
  - tools/extract/test_s13_upcomer_exchange_topology_cv_release.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/topology_cv_case_summary.csv
tags: [upcomer, exchange-cell, topology, control-volume, s13, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-topology-cv-release.md
  - imports/2026-07-21_s13_upcomer_exchange_topology_cv_release.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_s14_recirc_cv_segmentation_preflight/README.md
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21
date: 2026-07-21
role: Hydraulics/Thermal-modeling/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-CV-RELEASE-2026-07-21

## Objective

Use the completed Salt2/Salt3/Salt4 right-leg reverse-flow diagnostic masks and
OpenFOAM `owner/neighbour` face topology to decide whether S13 can release a
face-connected recirculation control volume, trusted exchange interface,
wall/core band, and downstream surface-extraction gate.

## Outcome

Complete as face-topology fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release/`.

Key results:

- Salt2: `136140` reverse-flow candidates, `17` face-connected components,
  largest face component `71775` cells, fraction `0.527214632`, interface
  `9796` faces / `0.00845399810494 m2`, right-leg wall faces `0`, boundary
  escape faces `5694`.
- Salt3: `138382` candidates, `20` face-connected components, largest face
  component `73349` cells, fraction `0.530047260`, interface `10094` faces /
  `0.00900672987352 m2`, right-leg wall faces `0`, boundary escape faces
  `5598`.
- Salt4: `139994` candidates, `19` face-connected components, largest face
  component `74256` cells, fraction `0.530422732`, interface `10238` faces /
  `0.00895255065973 m2`, right-leg wall faces `0`, boundary escape faces
  `5736`.
- Released topology CV rows: `0`.
- Released exchange-interface rows: `0`.
- Released wall/core rows: `0`.
- Surface extraction allowed: `false`.

The selected largest face-connected components are not defensible released
recirculation control volumes. They remain fragmented below the `0.75`
dominance gate, do not touch the trusted right-leg wall patches, and instead
touch lower-leg boundary patches including `pipeleg_lower_06_straight`,
`pipeleg_lower_07_bend`, `pipeleg_lower_08_straight`,
`pipeleg_lower_09_fitting`, and `ncc_pipeleg_lower_09_fitting_end`.

## Changes Made

- Updated `tools/extract/build_s13_upcomer_exchange_topology_cv_release.py` to
  relabel reverse-flow candidates by face connectivity from OpenFOAM
  `owner/neighbour`.
- Added selected face-connected mask outputs under `masks/`.
- Added `face_connected_component_summary.csv` and
  `boundary_escape_by_patch.csv`.
- Added unit coverage for the face-component builder and release gates.
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_topology_cv_release.py tools/extract/test_s13_upcomer_exchange_topology_cv_release.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_topology_cv_release`:
  passed, `5` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_topology_cv_release.py`:
  passed; generated face-connected component masks and fail-closed topology
  package.

## Unresolved Blockers

- No face-connected component is dominant enough to release as the S13
  recirculation CV.
- The largest components touch lower-leg boundary patches, not the trusted
  right-leg wall patch set, so wall/core band and `Q_wall_W` remain blocked.
- Exchange-interface topology exists diagnostically, but it is not released
  because the enclosing CV is not released.
- Surface VTK extraction, sampler manifest release, exchange-cell harvest,
  same-window UQ execution, S11/S15/S6 triggers, and coefficient fitting remain
  blocked.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- Solver/postprocessing/surface extraction/sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, or exchange-cell admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Phase 4B/5/S6 triggered: no.
- Residual absorbed into internal `Nu`: no.
