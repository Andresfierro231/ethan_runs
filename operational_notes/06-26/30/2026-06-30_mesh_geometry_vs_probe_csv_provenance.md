# Mesh geometry is authoritative; the probe CSV is a schematic that MISMATCHES it

Date: `2026-06-30` · Owner: claude (AGENT-156) · Priority: HIGH (affects geometry of all cut-plane extractions)

## Finding

Inclinations/diameters computed from `jadyn_runs/salt2/.../tp_tw_probe_locations.csv`
were WRONG. That CSV is a schematic 2-D layout that does NOT spatially correspond
to the actual mesh. The truth, measured by PCA on the real wall patches of the
OF13-reconstructed salt2 case (`tmp/.../recon_salt2_of13`, t=7915), CONFIRMS the
rig description (Ethan) and that CFD gravity g=(0,-9.81,0) matches the rig:

| Physical role | mesh patch | true axis | angle from gravity | bore (cross-extent) |
| --- | --- | --- | --- | --- |
| HEATER (long, bends) | pipeleg_lower_05_straight | (0.93,-0.37,0) | **69° (21° from horizontal)** | 22.0 mm |
| HEATER (other segment) | pipeleg_lower_02_straight | (1,0,0) | 90° (horizontal) | 22.0 mm |
| COOLER | pipeleg_upper_05_cooler | (-0.93,0.37,0) | 68° (22° from horizontal) | 22.0 mm |
| TEST SECTION (quartz) | pipeleg_left_04_test_section | (0,-1,0) | **0° (vertical)** | **20.9 mm (smaller)** |
| DOWNCOMER | pipeleg_right_02_middle | (0,1,0) | **0° (vertical)** | 22.0 mm |

The long heater (`pipeleg_lower`, 9 segments + 2 bends `03_bend`/`07_bend`) is the
inclined bottom leg; its segments vary in orientation (02 horizontal, 05 at 21°).
Test section is vertical and ~5% smaller bore (quartz) — both as Ethan stated.

## The deeper problem: probe-CSV ↔ mesh-patch SPATIAL MISMATCH

The probe CSV and the mesh patches are in inconsistent layouts. Spatially:
- probe `lower_leg` centerline (x≈0.888, vertical) actually traces the DOWNCOMER
  location (mesh `pipeleg_right` is the vertical pipe at x≈0.89).
- probe `right_leg` (bottom diagonal) actually traces the HEATER location
  (mesh `pipeleg_lower` inclined bottom leg at x≈0.34-0.55).
i.e. probe `lower`↔mesh downcomer and probe `right`↔mesh heater are SWAPPED.
The upcomer/test-section (left, x≈0) and cooler (upper) DO match between frames.

`case_analysis_profiles` pairs probe-CSV centerline_labels with mesh wall_patches
inside each span. Because the two frames disagree for lower/right, a span can pair
a centerline in one physical leg with wall patches in another.

## Consequence for results already produced

- THERMAL (HTC/UA'/Nu): used wall PATCHES (pipeleg_*) → these are tied to the
  correct physical leg. The heater data (q_w>0 on pipeleg_lower) IS the real
  inclined heater. **Thermal results stand** (modulo coarse mesh etc.).
- SECTION PRESSURE / FRICTION / RECIRCULATION: used probe CENTERLINES for plane
  placement AND normals. Therefore:
  * planes on the inclined heater were cut with a (near-vertical) probe normal,
    NOT perpendicular to the true 21° axis → oblique cut → inflated area, biased
    u_bulk, biased f. **Heater/downcomer friction & section values are mislabeled
    and mis-oriented — DO NOT TRUST by label until re-extracted.**
  * the UPCOMER (left side) probe centerline ≈ mesh left → **the upcomer
    recirculation finding (15-33% backflow) is on the correct leg and stands**;
    its stations are vertical in both frames.
- INCLINATION-BASED interpretation (the §6c table): the probe-derived version was
  wrong; the mesh-measured table above is authoritative.

## Fix (rework geometry from the mesh, not the CSV)

1. Build per-leg centerlines + local tangents from the MESH (PCA of each
   pipeleg_* patch, or a skeleton of the cell centroids), giving true axis and
   true bore per leg.
2. Re-place cut planes PERPENDICULAR to the true local axis; re-run section
   pressure / friction / recirculation. Expect the heater (now correctly cut at
   21°) and downcomer (vertical) values to change; upcomer likely little.
3. Re-audit the `case_analysis_profiles` span definitions so centerline geometry
   and wall patches refer to the SAME physical leg; fix the probe↔patch swap.
4. Re-evaluate the inclination/Ri_streamwise using the mesh axis (heater is
   streamwise-buoyant along a 21° incline; downcomer & test section are vertical).

## What remains TRUE / robust

- CFD gravity matches the rig (heater inclined ~21°). No gravity/setup error.
- Thermal closures (HTC/UA'/Nu) are patch-based → correct legs.
- Empirical upcomer recirculation (left side) is real and on the right leg.
- Property/T, convergence (mainline), B1 unlock — all unaffected.
