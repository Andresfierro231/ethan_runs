---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/summary.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_source_repair_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/mesh_uq_implication.csv
tags: [f6, coarse-repair, mesh-uq, static-pressure, no-admission]
related:
  - .agent/journal/2026-07-21/f6-coarse-path-uq-repair.md
  - imports/2026-07-21_f6_coarse_path_uq_repair.json
  - work_products/2026-07/2026-07-21/2026-07-21_f6_stage_a_harvest_qa/summary.json
task: TODO-F6-COARSE-PATH-UQ-REPAIR
date: 2026-07-21
role: cfd-pp / Mesh-GCI / Tester / Writer
type: status
status: complete
---
# TODO-F6-COARSE-PATH-UQ-REPAIR Status

## Objective

Repair or formally close the twelve blocked F6 coarse endpoint rows by tracing
retained coarse reconstruction provenance and stating the same-QOI mesh/UQ
implications without coefficient admission.

## Outcome

Complete. The stale coarse source paths are repaired to three retained OF13
reconstruction cases:

- `tmp/2026-06-30_claude_action_items/recon_salt2_of13` at time `7915`
- `tmp/2026-06-30_claude_action_items/recon_salt3_of13` at time `7618`
- `tmp/2026-06-30_claude_action_items/recon_salt4_of13` at time `10000`

All three repaired reconstructions contain `p_rgh`, `U`, `rho`, `T`, and
`system/controlDict`, so the twelve blocked endpoint rows are ready for a
future Stage B VTK/area/recirculation sampler. None contains static `p`, so
full same-QOI static-pressure mesh/UQ remains blocked.

No F6 row is admitted as `component_K`, `cluster_K`, or `section_effective`.
The only supported classification remains diagnostic until ordinary-flow and
same-QOI pressure evidence are available.

## Changes Made

- `.agent/BOARD.md`
- `.agent/status/2026-07-21_TODO-F6-COARSE-PATH-UQ-REPAIR.md`
- `.agent/journal/2026-07-21/f6-coarse-path-uq-repair.md`
- `imports/2026-07-21_f6_coarse_path_uq_repair.json`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/README.md`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/build_f6_coarse_path_uq_repair.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/test_f6_coarse_path_uq_repair.py`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_source_repair_audit.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_vtk_sampling_decision.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/mesh_uq_implication.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/summary.json`

## Validation

- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/build_f6_coarse_path_uq_repair.py` passed.
- `python3.11 -m py_compile work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/build_f6_coarse_path_uq_repair.py work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/test_f6_coarse_path_uq_repair.py` passed.
- `python3.11 work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/test_f6_coarse_path_uq_repair.py` passed with 3 tests.

## Guardrails

Native CFD/OpenFOAM outputs were not mutated. Registry/admission state was not
mutated. No scheduler action, solver/postprocessing launch, Fluid/external edit,
fitting/tuning/model selection, F6 fit, component-K admission, clipped K, hidden
global multiplier, blocker-register change, or generated-index refresh was
performed.

The next unblocking row is `TODO-F6-COARSE-VTK-SAMPLER-SUBMIT`: sample the
repaired coarse endpoint faces from available reconstructed fields and keep
static-pressure admission closed unless a valid `p` basis is produced.
