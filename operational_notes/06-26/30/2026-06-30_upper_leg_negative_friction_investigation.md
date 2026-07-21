# Investigation: NEGATIVE apparent Darcy f on `upper_leg` (Salt 2/3/4 Jin)

> **RECONCILED (2026-06-30, user direction):** the negative f is NOT merely a
> hydrostatic-removal artifact — it reflects a REAL buoyancy-driven recirculation
> / convection cell in the upcomer (confirmed: 15–33% backflow area, Ri≈64–300≫1).
> The buoyancy term this note identified is the *mechanism* of that real cell. The
> upcomer is therefore modeled with a convection-cell + natural-circulation
> closure (NOT a friction factor). See
> `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md` and
> `tools/extract/sample_upcomer_convection_cell.py`. Retained below for the
> pressure-decomposition evidence.

Date: `2026-06-30` · Owner: claude · Type: read-only diagnostic (no code/files edited)

## Summary / conclusion

The negative apparent Darcy friction (f ≈ −11 / −8 / −6 for Salt 2/3/4 Jin) on
the cooled top leg `upper_leg` is **NOT a flow-direction sign error and NOT real
flow pressure recovery.** It is a **hydrostatic / buoyancy residual artifact**:

- The `upper_leg` is **not horizontal** in the gravity frame. Gravity is
  `(0, −9.81, 0)`, and the leg DESCENDS in y (TW11 y=0.890 m → TW9 y=0.763 m,
  Δy = −0.127 m). It is a downhill leg in the buoyancy sense.
- Because the fluid is being **cooled** in this leg, ρ rises along the flow
  (~+0.2 %). The reported `p_rgh = p − ρ·g·x` removes hydrostatic head using the
  **local** section-mean ρ against an **absolute** elevation `y` (the ρ·g·y term
  is ≈ 17 000 Pa). A density change of only ~0.2 % therefore leaves a residual of
  order `Δρ·g·⟨y⟩ ≈ 4.6 × 9.81 × 0.83 ≈ +37 Pa` in `p_rgh`.
- That residual (+28 Pa observed) appears as a `p_rgh`/total-pressure RISE in the
  flow direction and **swamps the true frictional drop**, which at these
  velocities is only `f·(L/D)·½ρu² ≈ O(0.1 Pa)`. The friction tool correctly
  negates the signed gradient, so a spurious rise → spurious negative f.

**Ranked cause: Hypothesis 3 (buoyancy/elevation hydrostatic residual on a
cooled descending leg) — strongly supported. Hypotheses 1, 2, 4 refuted or minor.**

Do NOT feed the `upper_leg` apparent f to the 1D model. See "Recommended fix".

## Observed numbers (mainline continuation; flow order TW11 → TW10 → TW9)

Flow order is TW11 → TW10 → TW9 (verified below). p in Pa, ρ in kg/m³.

| Case | station | section_mean p_rgh | total p | ρ | y (m) |
| --- | --- | ---: | ---: | ---: | ---: |
| Salt 2 | TW11 | −14.03 | −13.86 | 1955.32 | 0.8902 |
| Salt 2 | TW10 |  13.96 |  14.14 | 1959.08 | 0.8268 |
| Salt 2 | TW9  |  16.83 |  17.01 | 1959.95 | 0.7634 |
| Salt 3 | TW11 |  −8.22 |  −8.00 | 1945.93 | 0.8902 |
| Salt 3 | TW10 |  19.34 |  19.57 | 1949.63 | 0.8268 |
| Salt 3 | TW9  |  21.24 |  21.48 | 1950.39 | 0.7634 |
| Salt 4 | TW11 |  −5.34 |  −5.05 | 1934.65 | 0.8902 |
| Salt 4 | TW10 |  22.40 |  22.71 | 1938.38 | 0.8268 |
| Salt 4 | TW9  |  22.56 |  22.87 | 1938.93 | 0.7634 |

Implied total-pressure change and density change, flow order:

| Case | dptot TW11→TW10 | dptot TW10→TW9 | dptot endpoint | dρ total | endpoint dp/ds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Salt 2 | +28.00 | +2.87 | +30.86 | +4.63 (+0.24 %) | +89.2 Pa/m |
| Salt 3 | +27.57 | +1.90 | +29.48 | +4.46 (+0.23 %) | +85.2 Pa/m |
| Salt 4 | +27.76 | +0.16 | +27.92 | +4.28 (+0.22 %) | +80.7 Pa/m |

Notes: all three stations sit at z=0; the elevation change is in **y**
(Δy = −0.127 m over the segment). The total-pressure rise is concentrated in the
TW11→TW10 step. Dynamic head is ~0.17 Pa, negligible (static and total methods
agree to <1 %).

## Ranked hypotheses with evidence

### H1 — Flow-direction / arc-length sign flip — REFUTED

The mean velocity VECTOR on the masked faces (recovered from the raw `.xy`
plane dumps) and the station-ordering tangent point the **same** way:

| Case | mean U at TW11 | ordering tangent TW11→TW9 | dot/|·| |
| --- | --- | --- | --- |
| Salt 2 | (+0.0122, −0.0050, 0) | (+0.930, −0.367, 0) | ≈ +1.0 |
| Salt 3 | (+0.0140, −0.0057, 0) | (+0.930, −0.367, 0) | ≈ +1.0 |
| Salt 4 | (+0.0162, −0.0065, 0) | (+0.930, −0.367, 0) | ≈ +1.0 |

The flow physically moves toward increasing arc length (TW11→TW10→TW9), which is
consistent with the LOCKED circulation (upcomer/TP6 at x=0 → top leg toward the
downcomer on the right, i.e. +x). Station alignment is ~0.99–1.00 on all three
upper_leg stations. **The ordering is correct; the sign convention in the tool is
correct.** The pressure genuinely rises in the true flow direction — so the cause
must be physical/numerical, not a sign bug.

### H2 — Genuine pressure recovery from cooling (density rise) — REFUTED (magnitude)

ρ rises only ~0.2 % across the leg. Quantified contributions to total pressure in
a leg that is horizontal *in the no-gravity sense*:
- inertial (continuity) term ρ·u·du ≈ 0.008 Pa (u changes ~2 %),
- dynamic-head term ½ρu² ≈ 0.17 Pa.

Neither is within two orders of magnitude of the observed +28 Pa. A genuine
mechanical-energy recovery of +28 Pa with no elevation term and no work input is
thermodynamically impossible here. **Cooling-induced recovery cannot explain the
magnitude.**

### H3 — Buoyancy / elevation hydrostatic residual — STRONGLY SUPPORTED (root cause)

`constant/g = (0, −9.81, 0)`; the leg descends Δy = −0.127 m. Reconstructing the
true static pressure `p = p_rgh − ρ·g·y` (with g·x = −9.81·y, so p_rgh = p + ρ·9.81·y):

| Case | true Δp_static TW11→TW9 | ⟨ρ⟩·g·Δy (const-ρ hydrostatic) |
| --- | ---: | ---: |
| Salt 2 | +2428 Pa | −2435 Pa (drop expected if rising; here y drops → p rises) |
| Salt 3 | +2417 Pa | (same scale) |
| Salt 4 | +2402 Pa | (same scale) |

The true static pressure rises ~+2.4 kPa as the fluid descends 0.127 m — exactly
the hydrostatic gain `ρgΔh`, which is real and correctly large. `p_rgh` is meant
to remove precisely this term. The leftover ~+28 Pa in `p_rgh` is the
**variable-density residual** of that removal: `p_rgh` removes `ρ_local·g·y` with
the local cooled ρ at each station, but the physical hydrostatic integral runs
over the ρ(s) profile. The residual scale is `Δρ·g·⟨y⟩ ≈ 4.6·9.81·0.83 ≈ +37 Pa`
— same sign and same order as the observed +28 Pa. Because the absolute ρgy term
is ~17 kPa, even a 0.2 % density change leaves tens of Pa, dwarfing the ~0.1 Pa
true friction. **This is the dominant mechanism.**

### H4 — Mesh / averaging noise near the cooler — CONTRIBUTING, NOT DOMINANT

The within-plane `p_rgh` scatter is large (std ≈ 23–49 Pa, with outlier faces up
to ~+180 Pa near the cooler), i.e. comparable to the 28 Pa signal — so the
section means are differences of noisy distributions and are not closure-grade.
However the rise is **robust**: using the median instead of the mean still gives
+22 to +24 Pa, and tightening the mask to one bore radius (18 mm) leaves the means
unchanged. So noise inflates uncertainty but does NOT create the sign; the
underlying driver is H3.

## Recommended fix / follow-up

1. **Exclude `upper_leg` apparent f from the 1D closure** until reworked. The
   negative value is a hydrostatic-removal artifact, not a friction factor.
2. **Compute friction on this leg from the TOTAL HEAD in the gravity frame**, i.e.
   form the gradient of `p_rgh` using a CONSISTENT (segment-mean or upstream)
   reference density rather than per-station local ρ, OR work from the true static
   pressure with the buoyancy term carried explicitly as `∫ρ(s) g·ds`. This
   removes the Δρ·g·y residual. Equivalently, reference elevation to the leg inlet
   (`y − y_TW11`) so the absolute ~17 kPa ρgy term cannot leak a residual.
3. **Velocity is too low for a clean friction signal here** (u ~ 0.013 m/s →
   true friction ~0.1 Pa, below the section-mean noise floor of ~20 Pa). Even after
   the buoyancy fix, the `upper_leg` f from this method will be low-confidence on
   the coarse mesh. Prefer the wall-shear route, or a finer mesh + area-weighted
   means, for this leg specifically.
4. Sanity-check the other legs that have elevation change for the same residual
   (the heated `lower_leg` and the risers); they did not flip sign because their
   true friction signal is larger and/or their Δρ·g·Δy residual is smaller, but
   the same bias is present at the few-Pa level.

## NEEDS MORE ANALYSIS

- The +28 Pa is consistent with the `Δρ·g·⟨y⟩ ≈ +37 Pa` residual scale in sign and
  order of magnitude, but the two do not match exactly (the simple scale estimate
  ignores the ρ(s) path integral and the per-station y in the removal). A rigorous
  confirmation requires re-deriving f with elevation referenced to the leg inlet
  and an explicit `∫ρ g·ds` buoyancy term, then checking that the residual f
  becomes small/positive. That re-derivation was NOT performed here (read-only
  task). **Until that rerun confirms a small positive f, treat the `upper_leg`
  friction as UNRESOLVED for closure.**
- Section-mean p_rgh noise (~20–50 Pa std) exceeds the true friction signal at
  these velocities; closure-grade `upper_leg` friction is likely unattainable on
  the current coarse mesh regardless of the buoyancy fix.

## Provenance

- Section means: `work_products/2026-06-30_claude_continuation_section_mean/section_mean_pressure_viscosity_screening_salt_test_{2,3,4}_jin_coarse_mesh.json`
- Friction: `work_products/2026-06-30_claude_segment_friction/segment_friction.{json,csv}`
- Raw plane velocity vectors (for H1): `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_jin_continuation/postProcessing/secmeanSurfaces/<t>/plane_TW{11,10,9}.xy`
- Gravity: `tmp/2026-06-30_claude_action_items/recon_salt2_jin_continuation/constant/g` = `(0 −9.81 0)`
- Segment map / circulation: `operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md`
- Tools: `tools/extract/sample_section_mean_pressure.py`, `tools/analyze/derive_segment_friction.py`
