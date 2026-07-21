# TAMU Natural-Circulation Loop: Authoritative Geometry and Naming Reference

**Status**: Authoritative — verified from mesh PCA centerlines (AGENT-162) and CFD case files  
**Last updated**: 2026-07-08  
**Source verification**: `work_products/2026-07-01_claude_mesh_centerlines/`, `jadyn_runs/modern_runs/.../0/T`

This file is the canonical geometry reference for all Claude and Codex agents.  
Before asking geometry questions, check here first.

---

## 1. Segment naming: mesh vs. probe CSV vs. span names

The probe CSV `tp_tw_probe_locations.csv` uses **SCHEMATIC names that are SWAPPED**
relative to the mesh. NEVER use probe CSV names for spatial orientation.

| Probe CSV name | Mesh segment name | Physical description |
|---|---|---|
| `lower_leg` | `pipeleg_right` / `right_leg` in spans | **Downcomer** (right side, cold, vertical descent) |
| `right_leg` | `pipeleg_lower` / `lower_leg` in spans | **Heater** (bottom, inclined ~21° from horizontal) |
| `upper_leg` | `pipeleg_upper` / `upper_leg` in spans | **Cooler** (inclined ~22° from horizontal) |
| `left_leg` | `pipeleg_left` / `left_lower/upper_leg` | **Upcomer** (left side, upward flow) |

**Use mesh/span names always.** The probe CSV is a schematic artifact.

Span names used in secmeanSurfaces and work_products:
- `lower_leg` = heater (BOTTOM horizontal-ish pipe, inclined ~21°)
- `right_leg` = downcomer (RIGHT vertical cold pipe)
- `upper_leg` = cooler (TOP horizontal-ish pipe, inclined ~22°)
- `left_lower_leg` = lower upcomer section
- `test_section_span` = test section (pipeleg_left_04)
- `left_upper_leg` = upper upcomer section

---

## 2. Flow direction

**Loop flow direction** (natural circulation, buoyancy-driven):
```
heater (lower_leg) → upcomer (left_lower_leg → test_section → left_upper_leg) →
cooler (upper_leg) → downcomer (right_leg) → heater (back)
```

**Lower_leg (heater) cut plane ordering**:
- Fluid flows from **s04 → s00** (IMPORTANT: not s00 → s04)
- s04 is near x ≈ 0.8 m (downcomer junction, heater INLET — cooler fluid from downcomer)
- s00 is near x ≈ 0.1 m (upcomer junction, heater OUTLET — hot fluid entering upcomer)
- This means: T(s00) > T(s04). Delta_T = T(s00) - T(s04) > 0 for all cases.

**Right_leg (downcomer) flow direction**: top (x≈0.8 m) to bottom (x≈0.1 m),
i.e., s00 (near upper corner) to s04 (near lower corner).

---

## 3. Key geometric dimensions (mesh PCA results, AGENT-162)

| Segment | Inner diameter | Inclination | Segment length |
|---|---|---|---|
| lower_leg (heater) | 30 mm (1.18 in) | ~21° from horizontal | 0.357 m |
| right_leg (downcomer) | 30 mm | ~0° (vertical) | 0.366 m |
| upper_leg (cooler) | 30 mm | ~22° from horizontal | 0.357 m |
| left_lower_leg (upcomer) | 30 mm | ~0° (vertical) | 0.121 m |
| test_section_span | 20.9 mm | ~0° (vertical) | 0.082 m |
| left_upper_leg (upcomer) | 30 mm | ~0° (vertical) | 0.145 m |

**Hydraulic diameter**: D_h = 22.098 mm (used by CFD in system/functions for Ri computation;
applies globally to all cells including the test section where true bore = 20.9 mm → 5.7% error)

**Loop height** (relevant for buoyancy): ~0.035 m (35 mm) total Δz from heater midpoint
to cooler midpoint.

---

## 4. Upcomer: recirculation cell

The upcomer has a **persistent, physically real recirculation cell** in all mainline cases:

| Case | Backflow area fraction at endpoints | Note |
|---|---|---|
| Salt 2 (S2) | 85–98% at left_lower_leg s04 | near-total backflow at the s04 cut plane |
| Salt 3 (S3) | similar | |
| Salt 4 (S4) | similar | |

**Consequence for T extraction**: The standard mixing-cup temperature
T_bulk = Σ(ρ·u_n·T) / Σ(ρ·u_n) diverges to unphysical values (370–1012 K)
when recirculation ratio > ~80%. Use T_fwd_bulk_k (forward-flow-only) instead.
See `tools/extract/sample_span_endpoint_temperatures.py`.

---

## 5. Test section: pipeleg_left_04

**This section is a net heat sink in all mainline cases.**

| Parameter | Value |
|---|---|
| Bore (inner diameter) | 20.9 mm (NOT 30 mm like other sections) |
| Wall thickness | 2.2 mm fused quartz |
| Quartz thermal conductivity | 1.38 W/m·K |
| Emissivity | 0.95 (no reflective coating; bare quartz) |
| Mineral insulation | NONE |
| Electrical heater power | 37 W |
| Net Q to fluid (S2/S3/S4) | −5.7 / −10.2 / −16.8 W (sink, not source) |

The net heat is **negative** because radiation + natural convection through bare quartz
at 0.95 emissivity exceeds the 37 W heater input at all three operating points.

---

## 6. Insulation: physical CFD values vs. 1D model tuning

**See `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md` for full
instructions. Summary:**

| Location | Physical CFD insulation | 1D model global value |
|---|---|---|
| Main piplegs | **1.4 in = 35.56 mm Calzite** | 0.25–0.30 in (temperature-matching value) |
| Test section | **NONE** (2.2 mm quartz only) | NOT separately modeled |

The 1D global value 0.25–0.30 in is a **compensating error** that matches loop temperature
at the cost of misrepresenting the test section heat loss.  
**Never use 1.4 in as the global 1D insulation value without per-section correction.**

---

## 7. Richardson number: characteristic length

The CFD computes Ri = Gr/Re² using **D_h = 22.098 mm globally** (hardcoded in
`jadyn_runs/.../system/functions`). This is the correct choice for internal pipe mixed
convection (Dittus-Boelter / Gnielinski mixed convection regime characterization).

- All probe-based Ri values use this global D_h
- The test section has a 5.7% D_h overestimate (22.098 vs 20.9 mm), giving ~2% Ri bias
- Reference temperature: T_ref = 447 K, rho_ref = 1958.48 kg/m³ (consistent with Jin EOS)

See: `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`

---

## 8. Corner bends: K values (CFD-measured)

From `work_products/2026-07-01_claude_bend_minor_loss/`:

| Corner | Adjacent spans | K (S2) | K (S3) | K (S4) |
|---|---|---|---|---|
| corner_lower_left | left_lower_leg ↔ lower_leg | 8.21 | 8.30 | 8.29 |
| corner_lower_right | lower_leg ↔ right_leg | 16.50 | 13.81 | 10.73 |
| corner_upper_right | right_leg ↔ upper_leg | 15.92 | 14.33 | 13.58 |
| corner_upper_left | upper_leg ↔ left_upper_leg | 6.25 | 6.22 | 6.68 |

Note: corner_lower_right has the largest K and shows the strongest Re-dependence
(K decreasing from 16.5 to 10.7 as Re increases from S2 to S4). The other corners
show mild Re-dependence.

Corner minor losses account for **8–12%** of span-level pressure drop for the main
pipe sections. The dominant phi offset (~1.4–1.8×) is NOT explained by corner K values.
See: `work_products/2026-07-08_minor_loss_separation/`

---

## 9. Lower_leg cut plane geometry: multi-pipe spanning

The secmeanSurface cut planes `plane_lower_leg__s{00-04}.xy` span **up to 0.88 m in y**
(the full loop bottom width), intersecting faces from multiple pipe sections. To extract
the correct pipe-core T_bulk, use 80th-percentile velocity masking:

```python
# In sample_span_endpoint_temperatures.py:
v_threshold = np.percentile(u_normal, 80)
mask = u_normal >= v_threshold
center_y = np.mean(y[mask])
center_z = np.mean(z[mask])
# Apply radius mask from this center
```

A naive centroid of all faces gives a center that is not inside any pipe.

---

## 10. Operating points: mainline Salt cases

| Case | Q_heater (W) | Re_heater | Re_cooler | Re_downcomer | mdot (kg/s) |
|---|---|---|---|---|---|
| Salt 2 Jin | 265.7 | 68.0 | 62.7 | 61.2 | ~0.0117 |
| Salt 3 Jin | 297.5 | 90.2 | 83.9 | 84.7 | ~0.0143 |
| Salt 4 Jin | 337.6 | 122.6 | 114.9 | 118.0 | ~0.0185 |

Salt 1 Jin: weakly converged; use with caution (held at AGENT-181 gate).

---

## Source provenance

| Fact | Source | Date |
|---|---|---|
| Segment names, flow direction | Mesh PCA centerlines, AGENT-162 | 2026-07-01 |
| Cut plane directions (lower_leg s04→s00) | sample_span_endpoint_temperatures, AGENT-203 | 2026-07-08 |
| Test section geometry, insulation | CFD 0/T audit, AGENT-202/204 | 2026-07-08 |
| Corner K values | sample_bend_minor_loss, AGENT-162 | 2026-07-01 |
| Upcomer recirculation | secmeanSurfaces XY extraction, AGENT-203 | 2026-07-08 |
| Ri D_h = 22.098 mm | system/functions inspection, AGENT-204 | 2026-07-08 |
| Minor loss separation | AGENT-210 local analysis | 2026-07-08 |
