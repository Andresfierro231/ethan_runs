---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_source_repair_audit.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/coarse_vtk_sampling_decision.csv
  - work_products/2026-07/2026-07-21/2026-07-21_f6_coarse_path_uq_repair/mesh_uq_implication.csv
tags: [f6, coarse-repair, mesh-uq, retained-reconstruction, no-admission]
related:
  - .agent/status/2026-07-21_TODO-F6-COARSE-PATH-UQ-REPAIR.md
  - imports/2026-07-21_f6_coarse_path_uq_repair.json
task: TODO-F6-COARSE-PATH-UQ-REPAIR
date: 2026-07-21
role: cfd-pp / Mesh-GCI / Tester / Writer
type: journal
status: complete
---

# F6 Coarse Path UQ Repair

## Attempted

I built a reproducible coarse repair package that joins the previously blocked
coarse endpoint-face matrix to the repaired endpoint-harvest inventory and the
Stage A medium/fine QA. The package audits repaired source paths, required
retained fields, future VTK sampler readiness, existing `.xy` diagnostic status,
and whether any same-QOI mesh/UQ admission is scientifically available.

## Observed

The repair succeeded for source provenance: Salt2, Salt3, and Salt4 coarse rows
all map to retained OF13 reconstructions under
`tmp/2026-06-30_claude_action_items/`. Their retained times are present, and
the fields `p_rgh`, `U`, `rho`, and `T` are present. This is enough to stage a
future VTK face-area/recirculation sampler for all twelve coarse endpoint rows.

The repair did not recover static `p`. All twelve endpoint rows therefore carry
`same_qoi_static_pressure_status=blocked_missing_static_p`. Existing coarse
`.xy` outputs remain diagnostic only because they do not provide the same raw
face polygon/area basis as the Stage A raw-face harvest.

## Inferred

The old blocker was two-part. Stale source-path provenance is repaired, but the
static-pressure basis is not. The correct scientific state is therefore not
"coarse unavailable"; it is "coarse field/source available for Stage B
diagnostics, but full static-pressure same-QOI UQ still unavailable."

For Salt2, the medium/fine Stage A rows already fail the ordinary-flow gate, and
the repaired coarse rows lack static `p`. For Salt3 and Salt4, the retained
coarse rows are coarse-only contexts and cannot produce same-QOI mesh/GCI by
themselves. No row should be converted into `component_K`, `cluster_K`, or
`section_effective`.

## Contradictions Or Caveats

The presence of `p_rgh` does not by itself equal an admitted static-pressure
basis. A later task could reconstruct static pressure if it defines and tests
the hydrostatic/reference-pressure convention, but this row intentionally did
not invent that conversion or mutate solver outputs.

The future Stage B VTK sampler can improve recirculation/area diagnostics for
coarse rows, but it will not automatically unlock same-QOI static-pressure
admission unless the pressure basis is explicitly repaired.

## Next Useful Actions

Claim `TODO-F6-SAME-QOI-UQ-AND-ADMISSION-GATE` to combine Stage A QA and this
coarse repair result into a formal row-by-row admission table. Claim
`TODO-F6-COARSE-VTK-SAMPLER-SUBMIT` later to run the repaired coarse VTK sampler
from available fields, preserving all no-admission guardrails.
