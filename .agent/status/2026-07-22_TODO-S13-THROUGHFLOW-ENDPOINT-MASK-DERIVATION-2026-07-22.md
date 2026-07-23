---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/endpoint_mask_derivation_gate.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_upcomer_exchange_surface_input_manifest_from_seeded_cv/seeded_surface_input_manifest.csv
tags: [status, s13, throughflow, endpoint-mask, open-cv, fail-closed]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/README.md
  - .agent/journal/2026-07-22/s13-throughflow-endpoint-mask-derivation.md
  - imports/2026-07-22_s13_throughflow_endpoint_mask_derivation.json
task: TODO-S13-THROUGHFLOW-ENDPOINT-MASK-DERIVATION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-S13-THROUGHFLOW-ENDPOINT-MASK-DERIVATION-2026-07-22

## Objective

Address the next S13 open-CV residual blocker by deriving or failing closed on
throughflow endpoint face masks from the trusted seeded cap-face artifacts.

## Outcome

Decision:
`s13_throughflow_endpoint_masks_fail_closed_candidate_seed_cap_masks_only`.

The seeded cap-face files exist for Salt2/Salt3/Salt4 and split cleanly into
start/end candidate cap groups. Six diagnostic candidate mask files were
written, each with 48 face IDs. None were released as throughflow endpoint
masks because the source rows lack area vectors, normals, owner cells, and an
admitted positive-mdot convention for the open-CV throughflow endpoints.

Current release state:

- Candidate endpoint masks written: `6`.
- Released endpoint masks: `0`.
- Harvest-ready rows: `0`.
- Residual value releases: `0`.

## Changes Made

- Added reproducible builder:
  `tools/analyze/build_s13_throughflow_endpoint_mask_derivation.py`.
- Added tests:
  `tools/analyze/test_s13_throughflow_endpoint_mask_derivation.py`.
- Published work product:
  `work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/`.
- Published cap-face inventory, endpoint-mask manifest, fail-closed release
  gate, candidate face masks, exact unblock contract, source manifest, and
  summary.

## Validation

- `python3.11 tools/analyze/build_s13_throughflow_endpoint_mask_derivation.py`: passed.
- `python3.11 -m py_compile tools/analyze/build_s13_throughflow_endpoint_mask_derivation.py tools/analyze/test_s13_throughflow_endpoint_mask_derivation.py`: passed.
- `python3.11 -m unittest tools.analyze.test_s13_throughflow_endpoint_mask_derivation`: `7` tests passed.

## Remaining Blockers

- Release-grade endpoint geometry is still missing: `area_m2`,
  `area_vector_x_m2`, `area_vector_y_m2`, `area_vector_z_m2`, `owner_cell`,
  `normal_convention`, `positive_mdot_convention`, `time_window_s`, and
  `source_path`.
- No same-window endpoint sampler has run on released masks.
- `mdot_throughflow_kg_s`, `T_in_bulk_K`, `T_out_bulk_K`, and
  `H_throughflow_net_W` remain unavailable.
- Row-specific `cp_J_kg_K`, storage, and named loss/source-owner lanes remain
  later gates.

## Guardrails

No native-output mutation, registry/admission mutation, scheduler action,
solver/postprocessing/sampler/harvest/UQ launch, Fluid/external edit, thesis
edit, source/property or Qwall release, residual value release, coefficient
fitting/admission, validation/holdout/external-test scoring, candidate freeze,
final-score claim, S11/S12/S13/S15/S6 trigger, hidden multiplier, residual
absorption into internal Nu, endpoint proxy substitution, or runtime-leakage
relaxation occurred.
