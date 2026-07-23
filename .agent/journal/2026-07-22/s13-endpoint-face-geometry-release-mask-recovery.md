---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/endpoint_mask_manifest.csv
tags: [s13, endpoint-mask, face-geometry]
related:
  - .agent/status/2026-07-22_TODO-S13-ENDPOINT-FACE-GEOMETRY-RELEASE-MASK-RECOVERY-2026-07-22.md
  - imports/2026-07-22_s13_endpoint_face_geometry_release_mask_recovery.json
task: TODO-S13-ENDPOINT-FACE-GEOMETRY-RELEASE-MASK-RECOVERY-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Endpoint Face-Geometry Release-Mask Recovery

Task: `TODO-S13-ENDPOINT-FACE-GEOMETRY-RELEASE-MASK-RECOVERY-2026-07-22`

Observed: six candidate endpoint masks exist across Salt2/Salt3/Salt4, each
with 48 face ids. The candidate masks do not include per-face area, area vector,
owner cell, or admitted throughflow sign convention fields.

Inferred: the masks are useful as a seed inventory but cannot support endpoint
throughflow integration, residual harvest, or same-QOI UQ.

Next useful action: regenerate endpoint masks from a mesh-aware postprocessor
that emits one row per endpoint face with area vectors, owner cells, normal
convention, positive-mdot convention, time window, and exact source path.
