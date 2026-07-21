# Upcomer Mixed-Convection Reversal Criterion — Independent Hand Estimate (Route B)

Date: `2026-06-30` · Owner: claude · Lane U2
Task: Route B of `2026-06-30_next_scope_branch_closures_and_cfd_design.md` §4 —
an INDEPENDENT, literature-based desk estimate of when the upcomer convection
cell (mixed-convection recirculation) turns on/off, to bracket the Route-A data
extrapolation (lower-upcomer shutoff Re≈240–260).
Companion model note: `2026-06-30_upcomer_convection_cell_model.md`.
Reusable calc: `tools/analyze/mixed_convection_reversal.py`
(+ `test_mixed_convection_reversal.py`, 6 tests pass under system python).

> **THIS IS AN ORDER-OF-MAGNITUDE DESK ESTIMATE.** It is intentionally
> independent of the solver's Ri/Ra fields (which are NEEDS-AUDIT, see §5). All
> assumptions are disclosed. Treat the resulting Re_crit as a BRACKET, not a
> closure-grade number.

---

## 0. Bottom line

Using the classical laminar mixed-convection screens evaluated from first
principles (salt properties at bulk T, Lc = D_h ≈ 21.8 mm, a plausible wall–core
ΔT of ~5–10 K), the lower-upcomer cell is expected to SHUT OFF in the band

> **Re_crit ≈ 100 – 235** (Ri_crit ≈ O(1); Gr_T/Re ≈ O(100)).

The Route-A data extrapolation (Re_crit ≈ 240–260) sits at the **upper edge / just
above** this independent band. **The two estimates are mutually consistent to
order of magnitude** (they agree within the wide ΔT uncertainty), which is a
defensible cross-check even before the onset/limit CFD lands. They do NOT
contradict each other; if anything the literature criterion suggests the cell may
turn off slightly EARLIER (lower Re) than the data extrapolation implies, but the
ranges overlap.

---

## 1. Classical flow-reversal criteria for mixed convection in a vertical pipe

The upcomer is a heated, near-vertical leg (y = 0 → 0.95 m, gravity = (0,−9.81,0)),
so the loop flow ascends against gravity = **buoyancy-AIDED** forced convection in
the heated core, while cooled near-wall fluid tends to SINK = a locally
**buoyancy-OPPOSED** near-wall layer. That radial wall–core buoyancy contrast is
exactly what rolls a counter-rotating transverse cell. The relevant published
groups:

### (a) Richardson screen  Ri = Gr/Re²  (primary, LitRev ch.14)
- **Gr is the ΔT-based Grashof** Gr_T = g·β·ΔT·Lc³/ν²; Re = ρU Lc/μ = U Lc/ν.
- Then **Ri = Gr_T/Re² = g·β·ΔT·Lc/U²** — a buoyancy-vs-inertia ratio that
  (usefully) keeps only ONE power of Lc and drops ν entirely.
- Threshold (textbook, e.g. Incropera; the LitRev "Ri screen"):
  forced-dominated Ri ≪ 1, free-dominated Ri ≫ 1, mixed Ri ~ 1. **Recirculation
  is expected for Ri ≳ O(1); the cell turns OFF as Ri falls through ~1.**

### (b) Laminar near-wall velocity reversal  Gr_T/Re ~ O(100–300)
- In fully developed laminar mixed convection in a vertical pipe the axial
  profile distorts; past a buoyancy threshold the near-wall (opposed) region or
  the centreline (aided) reverses. The controlling group is **Gr_T/Re ( = Ri·Re )**.
- The commonly quoted laminar onset of flow reversal in a vertical pipe is at
  **Gr_T/Re ~ O(10²)** (a few hundred for the aided centreline case). We use the
  band **Gr_T/Re|crit ≈ 100–300**. (Exact value depends on near-wall vs
  centreline reversal and on the CWT vs CHF boundary condition — hence a band.)

### (c) Jackson–Cotton–Axcell (1989) buoyancy parameter — physics only, NOT the number
- Jackson, Cotton & Axcell, *Studies of mixed convection in vertical tubes*,
  Int. J. Heat & Fluid Flow **10**(1), 2–15 (1989): the buoyancy influence on
  TURBULENT mixed convection is governed by a Gr/Reⁿ group,
  **Bo\* = Gr_q\*/(Re^3.425·Pr^0.8)** with **Gr_q\* = g·β·q″·D⁴/(k·ν²)** a
  HEAT-FLUX Grashof, onset of significant buoyancy effect at Bo\* ~ 6×10⁻⁷.
- **This is a TURBULENT correlation (Re^3.425).** Our upcomer is LAMINAR
  (Re ≈ 50–150), so the turbulent exponent does NOT apply quantitatively. We cite
  it for the PHYSICS — a Gr/Reⁿ buoyancy parameter with a reversal/impairment
  threshold and a buoyancy-aided/-opposed distinction — and use the laminar
  Ri (n = 2) screen and Gr_T/Re group for the actual numbers. Note it also uses a
  **different Gr (Gr_q heat-flux, Lc = D, ΔT implicit in q″)** than our Gr_T.

---

## 2. Evaluation at Salt 2/3/4 Jin upcomer conditions

**Properties** from `tools/analyze/salt_properties.py` (Jin µ, salt ρ/k/cp) at
the confirmed bulk T; β = 0.7497/ρ from the linear EoS. **Lc = D_h = 21.8 mm**
(the cell is transverse, driven by wall–core ΔT across the pipe diameter — the
pipe length 0.95 m would describe a different, axial/loop-scale buoyancy and is
NOT the cell length). **ΔT = wall–core (radial) ΔT** — the physical driver of the
cell — which we do not have measured, so we PARAMETERISE it (2–20 K; ~5–10 K is
the plausible modestly-insulated upcomer value).

| Salt | T_bulk | ρ (kg/m³) | µ (mPa·s) | ν (×10⁻⁶ m²/s) | β (×10⁻⁴/K) | Pr |
| --- | --- | --- | --- | --- | --- | --- |
| Salt2 | 446 K (173 °C) | 1959 | 9.44 | 4.82 | 3.83 | 24.9 |
| Salt3 | 459 K (186 °C) | 1950 | 7.98 | 4.10 | 3.85 | 20.9 |
| Salt4 | 474 K (201 °C) | 1938 | 6.70 | 3.46 | 3.87 | 17.4 |

(My Pr ≈ 17–25 from props vs solver Pr ≈ 16–23 — consistent. My Re from
U_bulk≈0.0166 m/s gives 75–105 vs solver Re_mean 86–153; same order, see §5.)

**Re_crit for cell SHUTOFF** (Re where the screen drops to threshold for a FIXED
Gr i.e. fixed ΔT, via Re = √(Gr/Ri_crit) and Re = Gr/(Gr/Re)_crit):

| ΔT (K) | Re(Ri=1) S2/S3/S4 | Re(Gr/Re=100) S2/S3/S4 | Re(Gr/Re=300) S2/S3/S4 |
| --- | --- | --- | --- |
| 2  | 58 / 68 / 81  | 34 / 47 / 66   | 11 / 16 / 22  |
| 5  | 92 / 108 / 128 | 84 / 117 / 164 | 28 / 39 / 55  |
| 10 | 129 / 153 / 181 | 168 / 233 / 329 | 56 / 78 / 110 |
| 20 | 183 / 216 / 256 | 335 / 466 / 657 | 112 / 155 / 219 |

**Current operating point (Salt3, lower-upcomer Re≈112):** at ΔT = 5 K,
Ri = Gr/Re² ≈ 0.9 and Gr/Re ≈ 104; at ΔT = 10 K, Ri ≈ 1.85, Gr/Re ≈ 208. So at
the present operating Re the system sits right at Ri ~ O(1) and Gr/Re ~ O(100) —
**consistent with a cell that is present but near its onset/shutoff boundary**,
which matches the CFD observation (backflow 0.15–0.33, decreasing with Re).

---

## 3. Bracket against the data extrapolation (Route A)

| Estimate | Lower-upcomer cell-OFF Re_crit |
| --- | --- |
| **Route A** (data extrapolation, bf→0, 3 coupled points) | **240–260** |
| **Route B / Ri=O(1) screen** (this note, ΔT 5–20 K) | **~90–256** |
| **Route B / Gr_T/Re ≈ 100** (this note, ΔT 5–20 K) | **~84–657** |
| **Route B central estimate** (ΔT ≈ 5–10 K, both screens) | **~100–235** |

**Verdict: they BRACKET / agree.** Route A (240–260) lands at the top of the
Route-B Ri-screen band and inside the Gr/Re-screen spread. Both routes
independently place lower-upcomer cell shutoff at **Re of order a few hundred**,
i.e. roughly 1.5–2.5× above the current max CFD Re (~150). This is a genuine
independent confirmation of the §3 CFD target (push a well-insulated, high-Q case
to Re ≳ 250 to observe backflow → 0).

**Uncertainty:** dominated by (i) the unmeasured wall–core ΔT — a factor ~2 in ΔT
moves Re_crit by ~√2 (Ri screen) to ~2× (Gr/Re screen); (ii) the reversal
threshold itself is a band (Ri_crit ~ 0.5–2; Gr/Re_crit ~ 100–300). Net: Re_crit
is good to roughly a FACTOR OF 2. The agreement with Route A is therefore "same
order, overlapping ranges," not a tight match.

---

## 4. Spatial caveat (upper upcomer / top)

Route A found the UPPER upcomer (Re_crit ≈ 550) and the TOP (TP6, slope ≈ 0,
"not Re-controlled") much more persistent. The hand criterion is consistent: TP6
has the lowest local U (≈0.006 m/s) and highest Ri, so its Gr/Re and Ri stay
above threshold even as the loop Re rises — a cooler/junction-pinned cell that a
single bulk-Re screen will not collapse. The hand estimate here is for the
LOWER upcomer (TW7/TP4), where the screens and the data both behave.

---

## 5. CRITICAL honesty — definitional mismatches & assumptions (NEEDS-AUDIT)

1. **Solver Ri/Ra ≠ this note's Ri/Ra.** The solver section-MEAN Ri is ~64–300
   while the section-MEDIAN Ri in the SAME JSON is ~2–8 (e.g. Salt3 TW7:
   Ri_mean=210 vs Ri_median=2.4). That ~100× mean/median gap means the
   section-mean Ri is dominated by a few cells (low-U denominator → huge local
   Gr/Re²) and is NOT a characteristic group. **My hand Ri (≈1–4 at ΔT 5–20 K) is
   far closer to the solver MEDIAN than to the solver MEAN.** Do NOT compare my
   numbers to the solver's section-MEAN Ri. The solver's Lc and reference ΔT are
   unaudited (the model note flags this); my groups use an explicit Lc = D_h and
   an explicit wall–core ΔT, stated above. This definitional mismatch is the
   single biggest reason to treat both as order-of-magnitude.

2. **ΔT choice is an assumption, not a measurement.** I used a parameterised
   wall–core ΔT (2–20 K), central 5–10 K. The actual upcomer radial ΔT depends on
   insulation/wall heat loss and is unknown here; it should be extracted from the
   CFD wall-vs-core T (a clean follow-up) to pin Re_crit within the band.

3. **Lc = D_h is a modelling choice** (transverse cell length). Using the leg
   length would give a loop-scale buoyancy, not the cell — reported only as a
   sensitivity, not used.

4. **Jackson–Cotton–Axcell Bo\* is turbulent** (Re^3.425, heat-flux Gr_q\*); our
   flow is laminar (Re ~ 50–150). I used it for the PHYSICS/citation only and the
   laminar Ri (n=2) and Gr_T/Re screens for the numbers. The published Bo\*
   threshold (~6×10⁻⁷) is NOT applicable quantitatively here.

5. **Laminar reversal threshold is a band, not a point** (Ri_crit ~ 0.5–2;
   Gr_T/Re_crit ~ 100–300) — depends on aided/opposed and CWT/CHF.

6. **Property/Re provenance.** Props are the Jin replicas (themselves transcribed,
   not independently validated — see salt_properties.py uncertainty note). My
   Re-from-U (75–105) and solver Re_mean (86–153) differ by ~15–40%, consistent
   with the section-mean caveats. Coarse mesh, laminar, single time everywhere.

7. **The LitRev chapter file cited in the task
   (`papers/LitRev-.../chapters/14_Jun18_bigger_lit_rev_pot_overlap.tex`) was NOT
   found on disk** at the given path during this work; the Jackson–Cotton–Axcell
   and Ri-screen criteria above are cited from the primary literature
   (JCA 1989) and standard mixed-convection textbooks, consistent with how the
   model note summarises ch.14. Re-link to the chapter when it is located.

---

## 6. Recommendation

- Use Re_crit ≈ **100–235 (central ~150–250)** for the lower-upcomer cell-OFF
  TARGET; it agrees with Route A's 240–260 to within the (factor-~2) uncertainty.
- The §3 CFD plan (push a well-insulated/high-Q case to Re ≳ 250) is the right
  experiment to convert this bracket into a measured Ri_crit.
- FIRST cheap refinement: extract the actual upcomer wall–core ΔT from existing
  CFD to collapse the ΔT spread and the mean/median Ri ambiguity — that single
  number would tighten Re_crit from a factor-2 band to ~±30%.
