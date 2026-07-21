# T8 — span centerline_labels vs wall_patches co-location audit (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162). READ-ONLY audit (the fix to the shared, codex-owned
`tools/case_analysis_profiles.py` is coordinator-gated; this documents + proposes).

## Method
For each major span, compare the MESH centroid (mean of its wall-patch PCA
centerline, from build_mesh_centerlines.py / T1) against the PROBE-CSV centroid
(mean of its `centerline_labels` coordinates from tp_tw_probe_locations.csv).
Co-location => the span's mesh patches and probe labels describe the same
physical leg. Salt 2 Jin (geometry identical across the family).

## RESULT — co-location table (mesh vs probe-label centroid)
| Span              | mesh centroid (x,y,z)  | probe-label centroid    | sep [m] | verdict |
|-------------------|------------------------|-------------------------|---------|---------|
| lower_leg (HEATER)| (+0.444,-0.123, 0)     | (+0.888,+0.229, 0)      | **0.566** | SWAPPED |
| right_leg (DOWNC.)| (+0.888,+0.229, 0)     | (+0.444,-0.123, 0)      | **0.566** | SWAPPED |
| left_lower_leg    | (0,+0.171,0)           | (0,+0.164,0)            | 0.007   | ok |
| test_section_span | (0,+0.449,0)           | (0,+0.449,0)            | 0.000   | ok |
| left_upper_leg    | (0,+0.753,0)           | (0,+0.759,0)            | 0.007   | ok |
| upper_leg (COOLER)| (+0.444,+0.827,0)      | (+0.444,+0.827,0)       | 0.000   | ok |

## Finding (confirms + quantifies the "lower<->right swap" gotcha)
The `lower_leg` probe-label centroid EQUALS the `right_leg` MESH centroid and vice
versa -> the `centerline_labels` (probe frame) for `lower_leg` and `right_leg` are
SWAPPED relative to their `wall_patches` (mesh). The probe TP/TW labels assigned to
the heater actually sit on the downcomer, and vice versa. The other four spans
co-locate to <=7 mm.

## Consequence for the closures (what is / isn't affected)
- UNAFFECTED (key results this session): everything keyed on `wall_patches` or on
  mesh centerlines -> T1 geometry, T1b friction (mesh stations), T4 HTC & Nu
  (q_w/DeltaT patch-based, D_h measured), T5 recirc, T7 K. These are CORRECT.
- AFFECTED: any quantity computed from `centerline_labels` for lower_leg/right_leg.
  Concretely, T4's segment LENGTH L_seg is built from centerline_labels, and the
  label-derived L is ALSO inflated ~1.27-1.33x vs the mesh length:
    lower_leg: label L=0.950 m vs mesh 0.712 m (x1.33)
    right_leg: label L=0.925 m vs mesh 0.732 m (x1.27)
  => T4's LENGTH-NORMALIZED quantities for the heater & downcomer -- q'_wall (=Q/L)
  and UA' (=q'/DeltaT) -- are biased LOW by ~25-33%. HTC and Nu (no length) are fine.
  (The other spans' label lengths are ~ok, small sep.)

## Recommended fixes
1. **Profile label swap — LANDED (2026-07-01, user-authorized cross-edit of the
   shared codex file):** swapped the `centerline_labels` between `lower_leg` and
   `right_leg` in tools/case_analysis_profiles.py. Verified: co-location now sep
   ~0.000-0.007 m for all spans; loop polyline still builds (n=17); full suite 196
   pass. NOTE the label polyline length remains ~1.3x the mesh length (separate
   issue), so length-normalized closures must still use mesh geometry (see fix 2).
2. **T4 tool (mine) — DONE 2026-07-01:** added `--mesh-length` (+`--mesh-stations`)
   to sample_segment_htc_uaprime.py; segment length now from the mesh centerline
   (rec `segment_length_source=mesh_centerline`). Re-ran Salt 2/3/4: heater UA'
   16.6/17.7/18.9 -> 22.1/23.6/25.2 (+33%), downcomer 3.0->3.75-3.80 (+27%), upcomer
   5.1/6.7/8.3 -> 6.6/8.7/10.8. HTC & Nu unchanged (length-free). See T4 journal.
3. Until (1)/(2) land: quote HTC and Nu (unaffected) as the trustworthy T4 thermal
   closures; treat UA'/q' for heater & downcomer as ~25-33% low pending the length fix.

## Confidence
Coordinates are mesh-PCA (authoritative) vs the schematic CSV; the 0.566 m swap and
the ~1.3x length inflation are unambiguous. Coarse mesh; single case (geometry is
mesh-identical across the family).
