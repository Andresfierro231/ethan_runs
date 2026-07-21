# Friction Closure: Why the Ri Correction Failed and What to Do Next

Date: `2026-07-08`
Author: claude (AGENT-204 / session)
Status: **Reference note — durable**

---

## 1. What we were trying to do (F5)

F5_ri_corrected was designed as:

```
dp_F5 = dp_F3_shah_apparent × phi(Ri_streamwise, leg_class)
phi   = max(1.0, 1.0 + c × Ri_streamwise)
```

The idea: F3_shah_apparent is our best baseline (−0.93% to +3.75% mdot error for S2–S4),
but we know each leg has buoyancy-enhanced friction (phi = f_CFD / f_F3_shah ≈ 1.5–2.7,
depending on leg class). We attempted to explain the variation in phi across the three
operating points via a linear Ri dependence.

**Result: F5 ≡ F3_shah_apparent. All three leg class fits failed (R² < 0). c = 0 for all.**

---

## 2. Root cause of failure

### 2a. Too few points, too narrow a Ri range

The entire dataset has exactly 3 operating points (Salt 2/3/4 Jin) per leg class. Within
each class:

| leg_class | Ri range             | phi range            | phi variation |
|-----------|---------------------|----------------------|---------------|
| heater    | 0.383 → 0.661 (1.7×) | 2.23 → 2.62 (17.5%) | weak          |
| cooler    | 0.593 → 1.066 (1.8×) | 1.89 → 2.20 (16.4%) | weak, WRONG direction |
| downcomer | 0.607 → 1.375 (2.3×) | 2.14 → 2.72 (26.8%) | noisy         |

With 3 points and a forced intercept, the fit has 0 degrees of freedom. R² and RMSE are
diagnostic only — they confirm the fit is not meaningful, not that the data is wrong.

### 2b. phi is nearly constant within each leg class

The dominant variation in phi is **between leg classes** (heater ~1.81, cooler ~1.54,
downcomer ~1.81), not **within a class as Ri changes**. The within-class variation (~15-27%)
is small compared to the measurement noise and is not monotonically consistent with the
Ri values.

Specifically, the cooler shows phi **decreasing** as Ri increases — the opposite direction
from physical expectation (higher buoyancy should increase friction in a buoyancy-affected
section). This is probably noise at the 3-point level, not a physical trend.

### 2c. The operating range is narrow by design

All three salts are at the same physical conditions (TAMU loop, natural circulation),
differing only in heater power: 265.7 / 297.5 / 337.6 W. This gives:
- Re variation: 62–123 (2× span)
- Ri variation per class: 1.7–2.3× (not sufficient to distinguish Ri from Re scaling)

A Ri correction would be meaningful only if Ri changes at CONSTANT Re. In the current
dataset, Ri and Re both change together (higher Q → higher mdot → higher Re, and higher
ΔT → higher Gr, with net Ri = Gr/Re² changing by roughly Ri ∝ Q^(−1/3) to ∝ Q^(+1/6)
depending on the leg).

### 2d. Circularity: CFD Ri used in a 1D solver

Even if the Ri correction worked numerically, there is a fundamental issue: the 1D solver
does not compute Ri self-consistently. It would need to:
1. Guess the temperature field
2. Compute local Ri per segment
3. Use Ri to set friction
4. Iterate to convergence

This is a coupled loop that the current 1D solver framework does not implement. Any Ri
correction in the current form requires supplying CFD-derived Ri values — which is circular
(we're using CFD to predict CFD).

### 2e. The ~2× phi offset is not Ri-driven

The dominant "excess" friction above F3_shah (phi ≈ 1.5–2.7) likely comes from:
1. **Entry/development effects** not fully captured by Shah apparent friction (the loop
   segments are short: x⁺ = x/(D·Re) ≈ 0.01–0.05, still in the entry region)
2. **Curvature/inclination effects** (heater is inclined ~21°; bends every few diameters)
3. **Buoyancy-driven secondary flow** in the heated/cooled inclined legs (enhances
   wall-normal velocity gradients → higher wall shear, independent of Ri in the
   axial-momentum equation sense)
4. **Minor losses** from the connectors and reducers (not separated out in the 1D model)

The leg-class-specific phi offset (captured by F4_leg_class) explains this offset, but
F4 is calibrated to CFD conditions and over-predicts friction at loop scale (−23% mdot).

---

## 3. What to do differently

### Near-term (available within days): wait for corrected Q-perturbation gate

Jobs 3275448/3275449/3275560 are the corrected Salt 1/2/3/4 Q-perturbation runs (±5%, ±10%
heater power relative to nominal). When they clear the AGENT-181 gate, we will have:
- 9 additional operating points per leg class (3 baseline + 2 × ±5%/±10% per baseline)
- Ri range expanded ≈ 1.3× beyond current (each ±10% Q → ±7% Ri change at fixed Re)
- **This is still not enough** — Ri variation will be ~1.5–2× per leg class with 12 points,
  still probably R² ≈ 0 for the Ri fit

**Recommendation**: after gate clears, fit phi vs Re INSTEAD of phi vs Ri. The cleaner
signal is Re-dependence: phi decreases as Re increases (all three leg classes).

### Medium-term: onset/limit CFD campaign (T13)

Design and submit a Q×insulation matrix centered on Salt 3 Jin that pushes Re to 200–400.
At Re = 300 (vs current 90), Ri decreases 11×. A 12-point dataset spanning Re 60–400
would allow:
- Separating Re-dependence from Ri-dependence
- Detecting whether phi is primarily a power law in Re (phi ∝ Re^n) or genuinely Ri-coupled
- Locating the onset of the upcomer recirculation cell shutoff

### Better functional form for the Ri correction

Rather than `phi = 1 + c × Ri` (linear, forced intercept), consider:

**Option A — power law in Re (short-term, no new physics needed):**
```
phi(Re) = a × Re^(-b)      # b > 0 means friction excess decreases as Re increases
```
Fit a, b from the 9 admitted points (S2/S3/S4) plus Q-perturbation gate results.

**Option B — Gr-based (physically motivated for buoyancy-driven secondary flow):**
```
phi = 1 + a × (Gr/Re)^n   # or phi = 1 + a × Gr^m / Re^p
```
Gr is the local Grashof number; Gr/Re = a mixed-convection parameter independent of
the velocity scale. This avoids the Re-cancellation issue in Ri = Gr/Re².

**Option C — separate entry-length from Ri (most defensible):**
1. Add minor losses (K) explicitly for bends/reducers (T7 is DONE)
2. Re-calibrate Shah apparent friction after subtracting minor losses
3. The remaining phi offset should be smaller and potentially better-correlated with Ri

**Option D — per-segment insulation BCs in 1D model (currently a known wrong assumption):**
The current 1D model uses a global insulation thickness. The CFD has:
- Main piplegs: 1.4 in insulation
- Test section: 2.2 mm quartz only (NO insulation)

Until per-segment insulation is implemented in the 1D model, the temperature-matching
(which drives the insulation sweep) is compensating for the test-section heat loss with
a globally reduced insulation value (0.25–0.30 in instead of 1.4 in). This introduces
a systematic error in the thermal state that feeds into any Ri-based correction.

### Self-consistent Ri in the 1D solver

For F5 to be a first-principles closure (not just an empirical fit to CFD), the 1D solver
needs to compute Ri from its own temperature and velocity predictions:

```
Ri_segment = (g × beta × delta_T_segment × D) / V_segment^2
```

where V_segment = mdot / (rho × A_segment) and delta_T_segment = T_wall − T_bulk.
This is a 1-line addition to the 1D solver per segment. It makes the Ri correction
self-consistent (no circularity) and allows re-fitting from just the CFD phi values.

---

## 4. Current recommended closure for production use

**F3_shah_apparent** is the recommended production closure until more operating points
are available:

| Form             | S2 err  | S3 err  | S4 err  | Notes |
|---|---|---|---|---|
| F1 (64/Re)       | +9.7%   | +16.2%  | +18.0%  | Under-predicts friction |
| F3_hagenbach     | +3.5%   | +6.7%   | +5.7%   | Better, not yet optimal |
| **F3_shah_apparent** | **−0.93%** | **+3.33%** | **+3.75%** | **Best current form** |
| F4_leg_class     | −23.2%  | −23.6%  | −24.7%  | Over-fitted to CFD dP; not for loop use |
| F5_ri_corrected  | −0.93%  | +3.33%  | +3.75%  | ≡ F3_shah (c=0, pending re-fit) |

F3_shah_apparent provides the current best predictive performance on mdot within ±4%.

---

## 5. Geometry facts to never re-discover

These were established over multiple sessions and caused repeated confusion. Document here
as a durable reference.

### Lower_leg XY cut planes

The `plane_lower_leg__s{00-04}.xy` secmeanSurfaces cut planes span the FULL loop
bottom — y up to 0.88 m, containing faces from multiple pipes. To extract the pipe-core
T_bulk from these files, use the 80th-percentile velocity mask in
`tools/extract/sample_span_endpoint_temperatures.py`:
- lower_leg flow direction: **s04 → s00** (heater inlet at s04, near x=0.8; outlet at s00, near x=0.1)
- NOT s00 → s04 as the span name might imply

### Upcomer recirculation and mixing-cup temperature

The upcomer (left_lower_leg, test_section_span, left_upper_leg) has **85–98%
recirculation** at endpoint cut planes. The standard mixing-cup temperature
T_bulk = Σ(ρ·u_n·T) / Σ(ρ·u_n) diverges to unphysical values (370–1012 K) when
the recirculation ratio > ~80%. Use T_fwd_bulk_k (forward-flow-only weighted T)
for regime characterization, and flag mixing-cup T when recirculation_ratio > 0.5.

See: `tools/extract/sample_span_endpoint_temperatures.py`

### Test section geometry

pipeleg_left_04 (test section): bore = **20.9 mm**, wall = **2.2 mm quartz** only,
no mineral insulation, emissivity = 0.95. This leg is a **net heat sink** at
operating conditions despite the 37 W electrical heater:
radiation + convection loss through the thin quartz exceeds heater input.

### Probe CSV vs mesh naming (permanent gotcha)

The schematic probe CSV `tp_tw_probe_locations.csv` swaps `lower_leg` and `right_leg`:
- `lower_leg` in CSV = downcomer (pipeleg_right) in mesh
- `right_leg` in CSV = heater (pipeleg_lower) in mesh

The XY cut-plane files from secmeanSurfaces use mesh segment names, NOT probe CSV names.
Use `SEGMENT_TO_SPANS` in `tools/extract/sample_segment_htc_uaprime.py` as the mapping.

### Ri characteristic length

CFD uses D_h = 22.098 mm globally (hardcoded in system/functions). This is correct
for internal pipe flow mixed convection (local regime classification, Ri = Gr/Re² with D_h).
Test section has 5.7% D_h mismatch → ~2% bias on upcomer median Ri. Negligible.
See: `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md`

---

## 6. Summary of immediate next steps

See MASTER_TODO for full backlog. Immediate items (ranked by value):

1. **Monitor corrected Q-perturbation gate (AGENT-181, jobs 3275448/3275449/3275560)**
   — when clear, extract phi per leg class for 9 new operating points;
   fit phi vs Re instead of phi vs Ri; re-evaluate F5.

2. **Per-segment insulation BCs in 1D model**
   — implement separate `insulation_thickness_m` per segment in ScenarioConfig;
   set test_section = 0 (quartz only), main piplegs = 1.4 in = 35.56 mm;
   this removes the biggest systematic error in the thermal state matching.

3. **Self-consistent Ri in 1D solver**
   — add Ri computation per segment from T_bulk and V_segment;
   enables F5 to be self-consistent (no CFD-derived Ri needed).

4. **Add phi vs Re as F6 candidate**
   — `phi(Re) = 1 + a / Re^b` with a, b fitted from all admitted points;
   expected to outperform F5_ri because Re-dependence is clearer than Ri-dependence
   in the current 3-point data.

5. **T13 onset/limit CFD campaign (pending T2 requalification)**
   — 5–10× wider Re range unlocks meaningful Ri-vs-Re separation.
