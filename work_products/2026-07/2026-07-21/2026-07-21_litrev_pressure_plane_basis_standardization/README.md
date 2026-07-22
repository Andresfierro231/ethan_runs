---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/cfd_postprocessing_schema_gap_audit.csv
  - work_products/2026-07/2026-07-16/2026-07-16_postprocessed_cfd_streamwise_pressure_1d_maps/all_streamwise_pressure_1d_map.csv
  - work_products/2026-07/2026-07-16/2026-07-16_pressure_ladder_harvest_admission_table/branch_orientation_straight_loss_recirc_admission.csv
  - work_products/2026-07/2026-07-18/2026-07-18_two_tap_pressure_basis_recirc_audit/pressure_velocity_basis_audit.csv
  - work_products/2026-07/2026-07-20/2026-07-20_f6_endpoint_face_uq_execution/endpoint_face_sampling_matrix.csv
  - work_products/2026-07/2026-07-20/2026-07-20_pm10_same_window_residual_targets/pm10_plane_pressure_targets.csv
tags: [cfd-postprocessing, pressure-ledger, pressure-basis, litrev-contract]
related:
  - operational_notes/maps/pressure-and-momentum-budget.md
  - work_products/2026-07/2026-07-21/2026-07-21_litrev_cfd_postprocessing_schema_gap/README.md
task: TODO-LITREV-PRESSURE-PLANE-BASIS-STANDARDIZATION
date: 2026-07-21
role: cfd-pp/Hydraulics/Tester/Writer
type: work_product
status: complete
---
# LitRev Pressure Plane/Basis Standardization

This package standardizes current CFD pressure plane and basis metadata from
existing repo artifacts only. It does not mutate native CFD/OpenFOAM outputs,
registry/admission state, scheduler state, Fluid code, or external repos, and it
does not launch solver or postprocessing work.

## Open First

- `pressure_plane_basis_standardization.csv`
- `next_extraction_queue.csv`
- `source_manifest.csv`
- `summary.json`

## Output Contract

`pressure_plane_basis_standardization.csv` contains one row for each current
pressure source row carried into the LitRev CFD contract lane:

- 330 streamwise station pressure-map rows.
- 66 pressure-ladder branch screen rows.
- 18 pressure-term span momentum rows.
- 3 two-tap raw endpoint pair rows.
- 6 two-tap face-level q-ref/flux rows.
- 3 pressure-corner recovery rows.
- 20 F6 planned endpoint candidate rows.
- 12 PM10/upcomer matched-plane target rows.
- 2 terminal-gated live-run caveat rows for corrected-Q `3307441` and high-heat
  `3299610`/`3299620`.

Each row records case/time, branch or span, station or endpoint label, plane
path when available, unit-normal status, averaging basis, pressure basis,
hydrostatic basis, kinetic/total-pressure basis, velocity/q-ref basis, density
basis, recirculation basis, missing basis fields, use label, admission status,
next extraction task, and exact source paths.

## Main Findings

- The broad station map is the largest source family and already carries `p`,
  `p_rgh`, `mean_un`, density, and RAF proxy fields, but unit normals,
  signed/absolute face flux, same-QOI UQ, and pairwise hydrostatic/kinetic
  corrections are not standardized.
- Branch pressure-ladder rows are useful admission screens, but they remain
  aggregate diagnostics until joined back to station rows and pressure-term
  geometry/density evidence.
- Current `corner_lower_right` two-tap rows are the best-resolved pressure-basis
  rows, with static, `p_rgh`, hydrostatic, kinetic, density, and face-flux
  evidence. They remain `section_effective`/diagnostic because material reverse
  flow, same-QOI UQ, trusted ordinary q-ref, recovery-plane sweeps, and component
  isolation are not admitted.
- F6 endpoint rows are candidates only. They still need a separately claimed
  sampler row before RAF/RMF/q-ref/time-window/GCI evidence can exist.
- PM10/upcomer matched-plane targets preserve `p_rgh`, density, speed, and
  dynamic-pressure targets, but not static pressure, unit normals, signed/abs
  mdot, RAF/RMF/SVF, or same-window pressure/thermal residuals. The newer
  corrected-Q continuation `3307441` is terminal-gated and must not be collapsed
  into the older timeout-harvest PM10 evidence.

## Next Task Sequence

1. Run `TODO-LITREV-SAME-QOI-UQ-EXECUTION` using the standardized row IDs here
   as the pressure-source index.
2. For metadata-only repairs, recover unit normals and plane definitions from
   existing sampler/controlDict metadata where possible.
3. For current two-tap rows, compute same-QOI UQ from existing endpoint faces
   first; queue new downstream recovery planes only under a separate sampler row.
4. For F6 and PM10/upcomer rows, wait for separately claimed sampler or
   terminal-gated harvest rows. Do not launch from this package.

## Guardrails

- No native-output mutation.
- No scheduler action.
- No solver or postprocessing launch.
- No registry/admission mutation.
- No F6 fit, component-K admission, clipped negative K, or hidden global
  multiplier.
