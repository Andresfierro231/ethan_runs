---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/classified_cap_face_inventory.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/endpoint_mask_manifest.csv
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_enthalpy_endpoint_preflight/next_action_queue.csv
tags: [journal, s13, throughflow, endpoint-mask, open-cv, blocker]
related:
  - .agent/status/2026-07-22_TODO-S13-THROUGHFLOW-ENDPOINT-MASK-DERIVATION-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_s13_throughflow_endpoint_mask_derivation/README.md
  - imports/2026-07-22_s13_throughflow_endpoint_mask_derivation.json
task: TODO-S13-THROUGHFLOW-ENDPOINT-MASK-DERIVATION-2026-07-22
date: 2026-07-22
role: Thermal-modeling / Hydraulics / cfd-pp / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# S13 Throughflow Endpoint Mask Derivation

## Attempted

I opened the seeded surface-input manifest and the classified cap-face CSVs for
Salt2/Salt3/Salt4, then built a reusable derivation package for the next
throughflow enthalpy residual blocker. The script split `*_start` and `*_end`
seed cap patches into per-case diagnostic candidate inlet/outlet mask files.

## Observed

Each case has 96 classified seed cap faces: 48 on
`ncc_pipeleg_right_01_lower_start` and 48 on
`ncc_pipeleg_right_03_upper_end`. The rows include `case_id`, `boundary_lane`,
`patch_name`, `face_id`, release flags, classification, blocking reason, and
source path. They do not include area, area-vector components, owner cells,
normal convention, positive-mdot convention, or terminal-window fields.

The package therefore writes candidate masks but keeps
`released_endpoint_masks=0`, `harvest_allowed_rows=0`, and
`residual_value_release_rows=0`.

## Inferred

The existing seeded cap IDs are useful geometry evidence and are the right
starting point for the endpoint-mask blocker. They are not enough to support
`mdot_throughflow_kg_s`, `T_in_bulk_K`, `T_out_bulk_K`, or
`H_throughflow_net_W`, because those require signed face-area geometry and an
audited normal convention. Using the face IDs alone as released endpoints would
be a proxy substitution.

## Caveats

The start/end labels are diagnostic candidates based on patch-name suffixes,
not an admitted inlet/outlet sign convention. No OpenFOAM field sampling,
surface integration, same-QOI UQ, mesh/GCI disposition, or source/property
release occurred.

## Next Useful Actions

1. Enrich or regenerate the open-CV endpoint geometry table with face IDs,
   `area_m2`, area-vector components, owner cells, endpoint labels, normal
   convention, positive-mdot convention, time window, and source path.
2. Run a Salt2 endpoint sampler smoke only after release-grade masks exist.
3. Run the all-case same-window endpoint harvest after the smoke test passes.
4. Keep residual values and model-form claims blocked until cp/source-property,
   storage/named-loss owner lanes, same-QOI UQ, and mesh/GCI evidence exist.
