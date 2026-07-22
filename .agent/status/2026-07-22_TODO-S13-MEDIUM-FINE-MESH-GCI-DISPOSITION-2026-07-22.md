---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/qoi_mesh_disposition_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/formal_gci_blocker_table.csv
tags: [status, s13, recirculation, exchange-cell, medium-fine, mesh-gci]
related:
  - .agent/journal/2026-07-22/s13-medium-fine-mesh-gci-disposition.md
  - imports/2026-07-22_s13_medium_fine_mesh_gci_disposition.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_exact_label_split_rerun/README.md
task: TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22
date: 2026-07-22
role: Hydraulics / Thermal-modeling / cfd-pp / Mesh-GCI / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-MEDIUM-FINE-MESH-GCI-DISPOSITION-2026-07-22

## Objective

Use the completed S13 exact-label medium/fine split rerun to quantify
medium/fine mesh sensitivity for the four exchange-cell QOIs and decide whether
formal GCI, production harvest, or model-form admission can proceed.

## Outcome

Complete. The package decision is
`medium_fine_mesh_disposition_complete_formal_gci_fail_closed_no_admission`.

The split rerun produced enough evidence for a two-level diagnostic
medium/fine spread report, but not enough for formal three-grid GCI. The same
label coarse member is absent from this evidence family, so Richardson/GCI,
production harvest, source/property or Qwall release, coefficient fitting, and
S11/S13/S15/S6 downstream triggers remain closed.

Key quantified results:

- `Q_wall_W`: maximum medium/fine spread `0.5029174998089355%` versus fine;
  diagnostic low-spread only, not release/admission.
- `mdot_exchange_positive_outward_proxy_kg_s`: maximum medium/fine spread
  `95.49934289848039%`; large fail-closed mesh sensitivity.
- `tau_recirc_proxy_s`: maximum medium/fine spread `24.149197428447152%`;
  large fail-closed mesh sensitivity.
- `wall_core_bulk_temperature_contrast_K`: maximum medium/fine spread
  `52.908053682355224%`; large fail-closed mesh sensitivity.

## Changes Made

- Added reusable builder:
  `tools/analyze/build_s13_medium_fine_mesh_gci_disposition.py`.
- Added tests:
  `tools/analyze/test_s13_medium_fine_mesh_gci_disposition.py`.
- Generated work-product package:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_medium_fine_mesh_gci_disposition/`.
- Generated:
  `case_qoi_medium_fine_spread.csv`,
  `qoi_mesh_disposition_summary.csv`,
  `formal_gci_blocker_table.csv`,
  `production_admission_gate.csv`,
  `source_manifest.csv`,
  `summary.json`, and `README.md`.
- Updated this status, matching journal, import manifest, and own board row.
- Regenerated generated documentation index files at closeout:
  `.agent/STATE.md`, `.agent/catalog.json`, `.agent/catalog.csv`, and
  `.agent/BLOCKERS.md`.

## Validation

- `python3.11 -m pytest tools/analyze/test_s13_medium_fine_mesh_gci_disposition.py`:
  passed, `5` tests.
- `python3.11 -m py_compile tools/analyze/build_s13_medium_fine_mesh_gci_disposition.py tools/analyze/test_s13_medium_fine_mesh_gci_disposition.py`:
  passed.
- `python3.11 tools/analyze/build_s13_medium_fine_mesh_gci_disposition.py`:
  passed and regenerated the package outputs.
- `python3 tools/docs/build_repo_index.py`:
  passed; indexed `2961` docs, `11` board rows, and `15` blockers.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: `false`.
- Registry/admission state mutated: `false`.
- Scheduler action: `false`.
- Solver/OpenFOAM postProcess/sampler launched: `false`.
- Formal GCI run/admitted: `false`.
- Production harvest/admission: `false`.
- Source/property or Qwall release: `false`.
- Coefficient fitting/admission: `false`.
- Validation/holdout/external-test scoring: `false`.
- S11/S12/S13/S15/S6 trigger: `false`.
- Fluid/external/thesis body mutation: `false`.
- Generated docs index refreshed at closeout: `true`.

## Next Useful Action

The highest-value next step is not coefficient fitting. It is to resolve the
missing same-label coarse basis or write a defensible equivalence contract that
can be reviewed against the existing coarse S13 evidence. If that fails, the
model-form switch should continue to route the recirculating upcomer to a
guarded signed-flow or diagnostic exchange-cell lane without admitted
coefficients.
