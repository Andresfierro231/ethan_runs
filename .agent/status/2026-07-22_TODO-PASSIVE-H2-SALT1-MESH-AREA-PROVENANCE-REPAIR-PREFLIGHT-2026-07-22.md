---
provenance:
  generated_by: codex
  task_id: TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22
  date: 2026-07-22
tags:
  - passive-h2
  - salt1
  - mesh-area
  - source-property
  - no-release
related:
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight
  - work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_junction_setup_row_recovery_background
  - imports/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight.json
task: TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22
date: 2026-07-22
role: Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---

# TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22

## Objective

Compute Salt1 PASSIVE-H2 family areas directly from setup mesh geometry and
compare them against the recovered five-family operator rows, with no
source/property release, scoring, freeze, or Fluid/runtime edits.

## Outcome

Completed. Decision:
`salt1_mesh_area_provenance_fail_closed_no_release_no_score`.

Observed facts:

- Needed setup patches: `39`
- Missing boundary patches: `0`
- Points read from setup mesh: `2268735`
- Family rows checked: `5`
- Family area tolerance pass rows: `4`
- Mesh-area-backed operator rows emitted: `4`
- Five-family mesh-area-backed operator ready: `False`
- Maximum absolute family area delta: `9.533941464717754e-06 m2`
- Maximum relative family area delta: `0.00022444002113082377`
- Source/property release: `False`
- Candidate freeze: `False`
- Score values emitted: `0`

Interpretation: the area-provenance part of the Salt1 PASSIVE-H2 operator is
now setup-mesh backed for `cooling_branch`, `downcomer`, `lower_leg`, and
`upcomer`. The `junction` family fails the predeclared area reconciliation
gate, so the five-family operator remains diagnostic-only and no S11/S15
release is opened from this row.

## Changes Made

- `tools/analyze/build_passive_h2_salt1_mesh_area_provenance_repair_preflight.py`
- `tools/analyze/test_passive_h2_salt1_mesh_area_provenance_repair_preflight.py`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/summary.json`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/patch_mesh_area_evidence.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/family_area_reconciliation.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/mesh_area_backed_operator_candidate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/release_preflight_gate.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight/no_mutation_guardrails.csv`
- `.agent/status/2026-07-22_TODO-PASSIVE-H2-SALT1-MESH-AREA-PROVENANCE-REPAIR-PREFLIGHT-2026-07-22.md`
- `.agent/journal/2026-07-22/passive-h2-salt1-mesh-area-provenance-repair-preflight.md`
- `imports/2026-07-22_passive_h2_salt1_mesh_area_provenance_repair_preflight.json`
- `operational_notes/07-26/22/2026-07-22_PASSIVE_H2_SALT1_MESH_AREA_PROVENANCE_REPAIR_PREFLIGHT.md`

## Validation

- `python3.11 tools/analyze/build_passive_h2_salt1_mesh_area_provenance_repair_preflight.py`
- `python3.11 -m unittest tools.analyze.test_passive_h2_salt1_mesh_area_provenance_repair_preflight`
- `python3.11 -m py_compile tools/analyze/build_passive_h2_salt1_mesh_area_provenance_repair_preflight.py tools/analyze/test_passive_h2_salt1_mesh_area_provenance_repair_preflight.py`

All passed.

## Unresolved Blockers

- `junction` fails family-area reconciliation, so the complete five-family
  PASSIVE-H2 candidate is not release-ready.
- Source/property release rows remain zero.
- Same-QOI release UQ remains unavailable for this candidate.
- No validation, holdout, external-test, freeze, final score, or coefficient
  admission is allowed from this package.

## Guardrails

No native CFD/OpenFOAM outputs, registry/admission state, scheduler state,
Fluid source, external repo, thesis current/LaTeX file, protected-row score,
validation/holdout/external score, fitting, tuning, model selection,
source/property release, Qwall/numeric q-loss release, candidate freeze,
coefficient admission, runtime wallHeatFlux use, hidden multiplier,
runtime-leakage relaxation, or residual absorption into internal Nu was
changed.
