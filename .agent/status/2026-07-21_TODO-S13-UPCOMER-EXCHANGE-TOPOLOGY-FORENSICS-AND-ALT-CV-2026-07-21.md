---
provenance:
  - tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py
  - tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/alternate_cv_case_summary.csv
tags: [s13, upcomer, exchange-cell, topology, forensics, alternate-cv, fail-closed, status]
related:
  - .agent/journal/2026-07-21/s13-upcomer-exchange-topology-forensics-alt-cv.md
  - imports/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv.json
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_cv_release
task: TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: status
status: complete
supersedes: []
superseded_by:
---
# TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21

## Objective

Diagnose why the S13 topology CV release failed and test one conservative
alternate wall-adjacent reverse-flow component selection without relaxing the
existing release gates.

## Outcome

Complete, fail-closed. Published
`work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_topology_forensics_alt_cv/`.

Key results:

- Component forensic rows: `56`.
- Released alternate CV rows: `0/3`.
- Surface extraction allowed: `false`.
- Salt2 selected alternate component: component `1`, `71775` cells,
  `0.527214632` of reverse candidates, `0` right-leg wall faces, `5694`
  boundary escape faces.
- Salt3 selected alternate component: component `12`, `10` cells,
  `7.22637337e-05` of reverse candidates, `6` right-leg wall faces, `10`
  boundary escape faces.
- Salt4 selected alternate component: component `12`, `84` cells,
  `0.000600025715` of reverse candidates, `15` right-leg wall faces, `36`
  boundary escape faces.

The alternate wall-adjacent search did not unlock the geometry gate. Salt2 has
no wall-adjacent reverse-flow component. Salt3 and Salt4 have wall-adjacent
reverse fragments, but those fragments are far below the dominance gate and
still touch unreleased boundary faces. The S13 exchange-cell path therefore
still needs a physical CV definition beyond reverse-flow components before any
surface extraction, sampler refresh, harvest, UQ, or S11/S15/S6 trigger.

## Changes Made

- Added `tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py`.
- Added `tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py`.
- Generated:
  - `component_topology_forensics.csv`
  - `alternate_cv_case_summary.csv`
  - `alternate_cv_surface_contract.csv`
  - `alternate_cv_boundary_escape_by_patch.csv`
  - `reverse_occupancy_diagnostics.csv`
  - `downstream_release_gate.csv`
  - `masks/*_selected_alternate_cv_mask.csv`
  - `summary.json`, `source_manifest.csv`, `no_mutation_guardrails.csv`, and
    `README.md`
- Added this status file, journal entry, and import manifest.
- Updated `.agent/BOARD.md` own row.

## Validation

- `python3.11 -m py_compile tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py tools/extract/test_s13_upcomer_exchange_topology_forensics_alt_cv.py`:
  passed.
- `python3.11 -m unittest tools.extract.test_s13_upcomer_exchange_topology_forensics_alt_cv`:
  passed, `5` tests.
- `python3.11 tools/extract/build_s13_upcomer_exchange_topology_forensics_alt_cv.py`:
  passed, emitted `released_alt_cv_rows=0` and
  `surface_extraction_allowed=false`.
- `python3.11 tools/agent/runtime_input_lint.py ...`:
  pending.
- `python3.11 tools/agent/source_property_gate.py ... --strict`:
  pending.
- `python3.11 tools/agent/split_policy_lint.py ...`:
  pending.
- `python3.11 tools/agent/finish_task.py --task-id TODO-S13-UPCOMER-EXCHANGE-TOPOLOGY-FORENSICS-AND-ALT-CV-2026-07-21`:
  pending.

## Unresolved Blockers

- `exchange_interface_vtk` remains blocked because no physical/topology CV was
  released.
- `wall_vtk` and `Q_wall_W` remain blocked because the selected alternate CVs
  are not released control volumes.
- Surface extraction, sampler manifest refresh, production harvest, same-QOI
  UQ, exchange-cell admission, and S11/S15/S6 remain blocked.
- Next useful unblock is a physical CV definition that is not restricted to
  reverse-flow components.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler action: no.
- OpenFOAM solver/postprocessing launched: no.
- Surface VTK extraction launched: no.
- Sampler/harvest launched: no.
- Fluid source edited: no.
- External repository edited: no.
- Fitting, tuning, model selection, threshold relaxation, proxy-interface
  admission, or closure admission changed: no.
- Blocker register changed: no.
- Generated documentation indexes refreshed: no.
- Residual absorbed into internal `Nu`: no.
