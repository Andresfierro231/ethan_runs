# T1 — Mesh-true centerlines: geometry re-extraction (paper notes)

Date: 2026-07-01
Owner: claude
Task: T1 (master TODO `operational_notes/07-26/01/2026-07-01_MASTER_TODO_1d_closures.md`)
Status: geometry extraction DONE + validated; extractor wiring NEXT.

## Motivation (for the paper: Methods / provenance-correction)
The hydraulic extractors placed cut planes at station points read from
`tp_tw_probe_locations.csv`. That file is a **schematic**, not mesh geometry, and
it (a) treats the inclined heater as if vertical and (b) spatially swaps
`lower_leg` <-> `right_leg`. Consequences: cut planes not perpendicular to the
true flow axis (wrong area / D_h / dynamic head) and friction/recirculation
attributed to the wrong physical leg. Fix: derive geometry from the mesh
`wall_patches`, which are physically unambiguous (`pipeleg_lower_*` = heater).

## Method
New tool `tools/extract/build_mesh_centerlines.py`:
1. For each major span, dump wall-patch face centers via a raw `surfaces` FO
   (`type patch`) — same OF mechanism the cut-plane tools use (OF13 env,
   `foamPostProcess`, field `p_rgh`).
2. Per span: PCA (SVD) of the face-center cloud -> principal axis; project onto
   axis for arc-length order; split into N=5 equal-arc bins; station center =
   bin centroid (rides the curved centerline, not the straight PCA axis).
3. Local tangent (= cut-plane normal) = normalized finite difference of
   consecutive station centroids. Bore = 2 x median radial distance of bin
   points from the station center in the plane perpendicular to the tangent.
4. Emit `mesh_stations.json`: per station {label, span, x,y,z, nx,ny,nz, bore_m,
   n_faces}. This is consumed by the extractors via a new
   `--centerline-source mesh --mesh-stations <json>` option (WIRING PENDING).

Run: `python3` (system, numpy/scipy 1.21) — NOT python3.11 (no numpy).
Inputs: `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13` @ t=7915.
Outputs: `work_products/2026-07-01_claude_mesh_centerlines/<source_id>/mesh_stations.json`.

## RESULT — mesh geometry (identical across Salt 2/3/4 Jin; same mesh)
Per-span mean inclination-from-horizontal and median bore:

| Span              | Physical leg | Incl (leg mean) | Incl (straight middle) | Bore |
|-------------------|--------------|-----------------|------------------------|------|
| lower_leg         | HEATER       | 19.0 deg        | **21.5 deg** (s02)     | 22.1 mm |
| upper_leg         | COOLER       | 18.9 deg        | **21.5 deg** (s02)     | 22.1 mm |
| right_leg         | DOWNCOMER    | 90.0 deg        | 90.0 deg               | 22.1 mm |
| left_lower_leg    | upcomer(low) | 90.0 deg        | 90.0 deg               | 22.1 mm |
| test_section_span | TEST SECTION | 90.0 deg        | 90.0 deg               | **20.9 mm** |
| left_upper_leg    | upcomer(up)  | 90.0 deg        | 90.0 deg               | 22.1 mm |

## Validation against independent mesh-PCA truth (all PASS)
- Heater/cooler straight middle = **21.5 deg** == the ~21-22 deg mesh-PCA value in
  `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md`. The
  schematic CSV would have cut these ~vertical -> this is the core correction.
- Downcomer + test section VERTICAL (90 deg) -> matches mesh truth.
- Test-section bore **20.9 mm** (smaller quartz) vs 22.1 mm elsewhere -> matches
  the measured design bores exactly (design: TS 20.9, others ~22.0).

## Known artifacts / confidence boundaries (disclose in paper)
- **Endpoint stations (s00/s04) of the inclined legs read incl 17.2 deg and bore
  ~26.4 mm.** These land on the FITTING/BEND terminations: (a) the finite-diff
  tangent is one-sided there, and (b) the fittings genuinely widen. => For
  friction, use INTERIOR stations (s01-s03); flag/trim the leg-end fitting
  stations. Follow-up: mark end stations `is_fitting_end=true` in the JSON.
- Face CENTERS sit ~half a cell inside the wall -> bore is an O(cell) estimate;
  use design bores (20.9 / 22.0 mm) as the sanity gate, not exact truth. The
  22.1 mm read is within ~0.1 mm of design, so bias is small on this mesh.
- Vertical legs read exactly 90 deg; heater/cooler straights within 0.5 deg of
  the 21 deg reference => tangent method is sound.

## Delta vs the probe-CSV geometry (the bug this fixes)
- Heater cut normal was effectively vertical (probe frame) -> now 21.5 deg
  (perpendicular to true axis). Any prior heater friction / dynamic head cut
  through the leg at a slant and is INVALID; must be recomputed (next step).
- lower_leg <-> right_leg were swapped in the probe frame; the mesh path keys on
  `wall_patches`, so labels now match physical legs.

## Extractor wiring DONE + re-run results (2026-07-01)
Wired `--centerline-source mesh --mesh-stations` into `sample_section_mean_pressure.py`
(default now `mesh`); `derive_segment_friction.py` gained `--drop-fitting-ends`
(drops `is_fitting_end` stations; leg-end fittings carry minor-loss jumps). No
wiring needed in the friction tool's geometry (it consumes the section JSON).
Re-ran section-pressure + friction on recon_salt{2,3,4}_of13, interior stations
only (3 of 5 per leg), `--auto-mu-jin` for Re.

### KEY OUTCOME 1 — geometry fix landed in the data
Heater (`lower_leg`) + downcomer (`right_leg`) cut planes now show flow
alignment **0.99–1.00** (perpendicular to true axis). Under the schematic probe
CSV the heater was cut ~vertical -> its section was a slant through the leg.

### KEY OUTCOME 2 — apparent Darcy f/f_lam per leg (interior stations, total-p)
| Leg | Salt2 (Re) | Salt3 (Re) | Salt4 (Re) | Interpretation |
|-----|-----------|-----------|-----------|----------------|
| lower_leg (HEATER)   | -0.83 (68) | -0.74 (90) | -0.91 (123) | negative -> buoyancy source in p_rgh |
| upper_leg (COOLER)   | -10.9 (63) | -10.7 (84) | -10.5 (115) | strongly negative (cooler buoyancy sink) |
| right_leg (DOWNCOMER)| -1.74 (61) | -2.39 (85) | -3.03 (118) | negative -> residual thermal/buoyancy |
| test_section         | -0.67 (69) | -0.43 (91) | -0.33 (124) | mildly negative |
| left_lower (UPCOMER) | **+2.02 (71)** | **+2.23 (97)** | **+2.67 (135)** | positive, ISOTHERMAL leg |
| left_upper (UPCOMER) | **+2.26 (67)** | **+2.12 (88)** | **+2.21 (120)** | positive, ISOTHERMAL leg |

### FINDING (paper-worthy) — single-leg p_rgh gradient != friction on non-isothermal legs
The heated/cooled legs return NEGATIVE apparent f. This is not noise: in a
buoyancy-driven loop the `p_rgh` field has only a REFERENCE-density hydrostatic
removed, so on legs where local rho != rho_ref (heater, cooler, and the
still-thermally-stratified downcomer/test-section) the streamwise `p_rgh`
gradient carries the buoyancy SOURCE term that drives the loop, which exceeds and
flips the frictional sign. Only the ISOTHERMAL upcomer legs give a clean
friction: f/f_lam ~ **2.0–2.7**, stable across the Re 67–135 envelope. This is
the trustworthy mesh-corrected hydraulic closure result.
=> To get straight friction on the heated/cooled legs, decompose the streamwise
momentum budget and subtract the buoyancy source (rho' g . s_hat) before taking
the gradient. NEW SUB-TASK (T1b / feeds T7, T11).

Tests: `tools/extract/test_build_mesh_centerlines.py` (3, synthetic cylinders
recover incl+bore) + existing 33 extract/analyze tests = 36 pass.

## NEXT (remaining T1)
1. Add `is_fitting_end` flag + optionally trim end stations in the tool.
2. Wire `--centerline-source mesh --mesh-stations` into:
   - `tools/extract/sample_section_mean_pressure.py` (build_loop_polyline swap)
   - `tools/analyze/derive_segment_friction.py`
   - `tools/extract/sample_upcomer_convection_cell.py`
3. Re-run section-pressure + friction on recon_salt{2,3,4}_of13 with mesh
   geometry; tabulate f_heater (now correct), f_downcomer, and deltas vs the old
   probe-based numbers (lower_leg f was ~2.7-3.1; expect a real change now that
   the heater is cut perpendicular).
4. Add a pytest for `stations_from_points` (synthetic inclined cylinder ->
   recovers incl + bore).
5. Then T4/T5/T7 unblock (they consume corrected D_h/geometry).
