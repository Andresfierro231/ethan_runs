---
task: AGENT-294
date: 2026-07-13
role: Writer
type: map
status: reference
tags: [geometry, mesh-truth, provenance]
related:
  - operational_notes/maps/README.md
  - operational_notes/maps/pressure-and-momentum-budget.md
  - operational_notes/maps/cfd-runs-and-admission.md
---
# Geometry & Mesh Truth — Map of Content

Tags: #geometry #mesh-truth #provenance

## What this covers

The canonical geometry of the TAMU natural-circulation loop and its provenance:
where segment axes, inclinations, bores, and centerlines come from, why the probe
CSV cannot be trusted for spatial layout, and how the mesh-truth fix propagated
into every downstream hydraulic/thermal extraction. Start here before asking any
"which leg / what angle / how long" question.

## Current status

Geometry is **settled and authoritative from the mesh** (PCA of `pipeleg_*` wall
patches on the OF13-reconstructed salt2 case), consolidated into
`reference/geometry_reference.md`. The one durable trap — the probe CSV
`tp_tw_probe_locations.csv` is a schematic whose `lower_leg`/`right_leg` are
spatially SWAPPED vs the mesh (probe `lower` = mesh downcomer, probe `right` =
mesh heater) — is documented, and the label swap + length fixes have landed in the
extraction tools (T1, T8). The only open geometry question is a residual
CFD-vs-rig gravity-orientation discrepancy for the heater/downcomer that needs an
Ethan/mesh audit; the empirical recirculation result is frame-independent and is
unaffected either way.

2026-07-16 AGENT-455 downstream taxonomy check:
`work_products/2026-07/2026-07-16/2026-07-16_closure_qoi_mesh_gci_resolution/`
re-applied the owner-locked map to Internal-Nu admission. The test section is
not a separate leg for ordinary-pipe/Internal-Nu fitting: `test_section_span`
belongs to `upcomer_left_vertical`, alongside `left_lower_leg` and
`left_upper_leg`. Any table that lists `test_section` separately must treat it
as an upcomer subspan unless a later geometry package explicitly overturns this
map.

## Trusted results

- **Probe CSV ≠ mesh (provenance rule).** `tp_tw_probe_locations.csv` is a 2-D
  schematic that does NOT spatially correspond to the mesh. In the probe frame,
  `lower_leg` traces the mesh **downcomer** and `right_leg` traces the mesh
  **heater** (lower↔right swapped, ~0.566 m separation). Get inclination, bore,
  and centerlines from the MESH, never the CSV. →
  `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
- **Mesh PCA centerlines (T1).** Heater `pipeleg_lower` ~21° from horizontal
  (long leg, 2 bends); cooler `pipeleg_upper` ~22°; test section `pipeleg_left`
  vertical with smaller bore **20.9 mm** (quartz); other legs ~22.0–22.1 mm;
  downcomer `pipeleg_right` vertical. CFD gravity g=(0,−9.81,0) matches the rig. →
  `tools/extract/build_mesh_centerlines.py`,
  `work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/`
- **Span↔patch mapping audit (T8, DONE).** Proved lower↔right centerline labels
  swapped (0.566 m separation) and labels ~1.3× too long. Fixes landed:
  label swap in `tools/case_analysis_profiles.py` drove co-location to ~0, and a
  `--mesh-length` correction propagated to UA'/q' (+27–33%; HTC/Nu unchanged). →
  MASTER TODO §T8 in
  `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`
- **Owner-locked segment map.** lower_leg = heater (heated_incline);
  upcomer = left_lower_leg + test_section_span + left_upper_leg (upward flow,
  recirculation cell, LEFT side, `pipeleg_left`); downcomer = right_leg
  (`pipeleg_right`); cooler = upper. Operating T confirmed by Ethan 165–210 °C. →
  `reference/geometry_reference.md`

## Open / in-progress / blocked

- **OPEN — CFD gravity-orientation vs rig audit.** Heat-flux-identified CFD
  orientation makes the heater appear ~vertical and the downcomer ~horizontal,
  vs the rig's heater/cooler at ~20° from horizontal. The inclination-based
  "downcomer transverse buoyancy" explanation was **RETRACTED**; the discrepancy
  needs an Ethan / mesh-audit resolution. Empirical recirculation is
  frame-independent and stands regardless. →
  `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md` (§5b)

## Research avenues tried (outcome + provenance)

- **Probe-CSV-derived inclinations/diameters** — WRONG (schematic mismatch);
  superseded by mesh PCA. →
  `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
- **Mesh PCA of `pipeleg_*` patches for axis/bore** — WORKED; now authoritative. →
  `tools/extract/build_mesh_centerlines.py`,
  `work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/`
- **Span↔patch label/length audit** — WORKED; swap + `--mesh-length` fixes landed,
  UA'/q' corrected +27–33%. →
  `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md` (§T8)
- **Inclination "downcomer transverse buoyancy" interpretation** — RETRACTED
  pending CFD-vs-rig orientation audit. →
  `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md` (§5b)

## Key artifacts (canonical)

- `reference/geometry_reference.md` — canonical geometry, naming, flow directions,
  dimensions, insulation, corner K values, operating points.
- `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`
  — the probe-CSV mismatch finding (the provenance rule).
- `tools/extract/build_mesh_centerlines.py` (+ `test_build_mesh_centerlines.py`)
  — mesh PCA centerline/tangent/bore extraction.
- `work_products/2026-07/2026-07-01/2026-07-01_claude_mesh_centerlines/` —
  extracted per-leg centerlines (salt 1–4 Jin).
- `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md` — §T1/§T8
  geometry task context, method, acceptance.
- `imports/2026-07-01_mesh_centerlines_and_closures.json` — intake manifest
  (AGENT-162) linking the geometry fix to downstream tools/products.

## Related

- `operational_notes/maps/README.md` — index of all topic maps.
- `operational_notes/maps/pressure-and-momentum-budget.md` — consumes the
  mesh-true centerlines for perpendicular cut-plane friction extraction.
- `operational_notes/maps/cfd-runs-and-admission.md` — the CFD cases the geometry
  was measured from.
- `operational_notes/maps/thermal-closures-and-internal-nu.md` — UA'/q' values
  corrected by the `--mesh-length` geometry fix.
