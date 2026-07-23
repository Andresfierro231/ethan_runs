---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks/source_manifest.csv
tags: [journal, s13, endpoint-geometry, throughflow]
related:
  - .agent/status/2026-07-22_TODO-S13-ENDPOINT-GEOMETRY-ENRICHMENT-FOR-RELEASE-MASKS-2026-07-22.md
  - imports/2026-07-22_s13_endpoint_geometry_enrichment_for_release_masks.json
task: TODO-S13-ENDPOINT-GEOMETRY-ENRICHMENT-FOR-RELEASE-MASKS-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Writer / Reviewer / Tester
type: journal
status: complete
---
# S13 Endpoint Geometry Enrichment For Release Masks

## Attempted

Used the completed endpoint-mask derivation, throughflow enthalpy endpoint
preflight, and seeded surface-input manifest to determine whether the six
Salt2/Salt3/Salt4 candidate endpoint masks can be promoted to release-grade
open-CV throughflow endpoint masks.

## Observed

Each Salt2/Salt3/Salt4 inlet/outlet candidate mask exists and has `48` faces.
Those candidates are still not release masks. Normal-convention,
positive-mdot, retained time-window, and source-path context exist in the
surrounding manifests, but the release surface lacks the per-face geometry
needed for signed integration: area, area-vector components, and owner cell.

## Inferred

The blocker has narrowed. The problem is no longer "do endpoint candidates
exist?" The problem is "can the candidate face IDs be enriched or regenerated
with release-grade geometry and sign convention?" Until that happens, endpoint
field sampling would be premature and could lock in a sign or proxy-plane error.

## Caveats

This row did not inspect or mutate native solver output and did not run a
sampler. It intentionally preserves released endpoint masks, harvest-ready
rows, and residual value releases at `0`.

## Next Useful Actions

1. Regenerate or enrich the endpoint geometry table for all six endpoint masks
   with `face_id`, `endpoint_label`, `area_m2`, `area_vector_x_m2`,
   `area_vector_y_m2`, `area_vector_z_m2`, `owner_cell`,
   `normal_convention`, `positive_mdot_convention`, `time_window_s`, and
   `source_path`, using the existing convention/time/source context where it
   survives review.
2. After release masks exist, run a one-case endpoint sampler smoke for `rho`,
   `U`, and `T` on the released masks only.
3. Keep S13 open-CV residual values closed until endpoint harvest, cp/property,
   storage/named-loss, and mesh/GCI gates all pass.
