---
provenance:
  - tools/extract/build_s13_right_leg_geometry_seed.py
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed/geometry_seed_case_summary.csv
  - work_products/2026-07/2026-07-21/2026-07-21_s13_right_leg_geometry_seed/downstream_release_gate.csv
tags: [s13, upcomer, right-leg, geometry-seed, s12, journal]
related:
  - .agent/status/2026-07-21_TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21.md
  - imports/2026-07-21_s13_right_leg_geometry_seed.json
task: TODO-S13-RIGHT-LEG-GEOMETRY-SEED-2026-07-21
date: 2026-07-21
role: Hydraulics/cfd-pp/Implementer/Tester/Writer
type: journal
status: complete
supersedes: []
superseded_by:
---
# S13 Right-Leg Geometry Seed

## Attempted

Built a task-owned geometry seed package from trusted right-leg wall patches.
The implementation parses each Salt2/Salt3/Salt4 `polyMesh` read-only, selects
owner cells on the trusted wall patches, classifies their boundary/internal
face lanes, joins existing cell volumes, and reports reverse-flow occupancy as
diagnostic support only.

## Observed

- All three cases have the same geometry seed size: `38880` cells and
  `1.19084663056e-05 m3`.
- Trusted wall area is positive and identical across cases:
  `0.063435001093 m2`.
- Internal seed/core interface area is positive:
  `0.0623473180949 m2`.
- Two NCC cap patches are classified in each case with `96` total cap faces.
- Untrusted boundary escape count is `0` in all three cases.
- Reverse-flow overlap is small: Salt2 `0`, Salt3 `6`, Salt4 `15` cells.

## Inferred

The prior velocity-only ROI failure can now be separated from the geometry
anchor. A trusted wall-adjacent right-leg seed exists in all train cases and is
ready for a source-bounded CV rerun. That rerun must still decide whether this
seed can support released exchange-interface, wall/core, normal, source, and
same-QOI lanes.

## Contradictions and Caveats

- This row does not claim S13 production readiness. It only releases the
  geometry seed as input to the next release gate.
- Reverse-flow occupancy is intentionally tiny and diagnostic-only; it does not
  invalidate the seed because the seed is wall-geometry anchored.
- No surface extraction, sampler, harvest, UQ, S12 implementation, or Fluid
  edit was performed.

## Next Useful Actions

1. Claim a new source-bounded CV rerun row that consumes
   `geometry_seed_case_summary.csv`, `geometry_seed_cells.csv`, and
   `geometry_seed_face_lanes.csv`.
2. In that row, decide whether the seed releases exchange-interface,
   wall/core, normal, `Q_wall_W`, and source/sink lanes.
3. Only if the source-bounded rerun releases `3/3`, rerun sampler manifest,
   surface extraction, harvest, same-QOI UQ, and S12-HIAX1 implementation.
