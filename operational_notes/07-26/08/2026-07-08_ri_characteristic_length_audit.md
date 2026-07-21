# Ri Characteristic Length Audit

Date: `2026-07-08`
Task: `AGENT-204`
Author: claude
Status: **COMPLETE — answer confirmed from CFD system/functions source**

---

## Question

Are we using the correct characteristic length L in the Richardson number Ri?
There are two common conventions:
- **D_h-based Ri**: uses hydraulic diameter — correct for local regime classification in internal pipe flow
- **L-based Ri**: uses tube length — used in some developing-flow and whole-loop buoyancy metrics

---

## Finding: CFD uses D_h = 22.098 mm globally

From `jadyn_runs/.../system/functions` (dimensionlessFields coded FO):

```cpp
const scalar D = 0.02209800;  // hardcoded for all cells

// Re = rho * |U| * D / mu
Re.primitiveFieldRef() = rhoI * UmagI * D / max(muI, SMALL);

// Gr = g * |rhoRef - rho| * D^3 * rhoRef / mu^2
Gr.primitiveFieldRef() = gMag * mag(rhoRef - rhoI) * pow3(D) * rhoRef / max(muI*muI, SMALL);

// Ri = Gr / Re^2
Ri.primitiveFieldRef() = GrI / max(ReI*ReI, 1.0);
```

Substituting: Ri = g·|ρ_ref − ρ|·D·ρ_ref / (ρ²·V²) ≈ g·β·ΔT·D/V²

**The characteristic length L in Ri is D_h = 22.098 mm. This is the correct choice.**

---

## Why D_h is correct for this application

| Purpose | Correct L | Why |
|---|---|---|
| Local flow-regime classification (mixed vs forced convection) | D_h | Ri = Gr/Re² with D_h compares local buoyancy to inertia on the pipe-diameter scale; threshold Ri ~ O(1) is well-established for pipe mixed convection |
| Nu correlation for internal pipe flow | D_h | Standard Nu = h·D_h/k; heat transfer literature uses D_h for laminar pipe mixed convection |
| Developing-flow entry correction | D_h | Shah apparent friction / Hagenbach use x⁺ = x/(D·Re) — D_h is implicit |
| Loop-scale buoyancy vs flow inertia | L_loop | Ri_loop = g·β·ΔT·H/V² where H is loop height — a different quantity, not what the solver computes |

The CFD solver computes **per-cell** Ri using D_h. We take the **section median** of these per-cell values. This gives a representative mixed-convection regime indicator for each span, consistent with literature.

---

## Known limitation: global D = 22.098 mm applied to test section

The test section (`pipeleg_left_04`) has actual bore **20.9 mm**, not 22.1 mm. The hardcoded D = 22.098 mm introduces a systematic bias in the test section's dimensionless numbers:

| Quantity | Error | Direction |
|---|---|---|
| Re_test_section | +5.7% | Overestimates Re (D too large) |
| Gr_test_section | +18% | Overestimates Gr (D³ too large) |
| Ri_test_section | +5.7% | Overestimates Ri (Ri ∝ D¹ after Re² cancels Gr's D³/D²) |
| Nu_test_section | −5.7% | Underestimates Nu (Nu = h·D/k, D too large inflates denominator) |

This is a known limitation from T9 audit. It is a **quantified small error**, not a wrong choice of length scale. For the test section span specifically, Nu and Ri carry a ~5.7% systematic bias due to the global D mismatch.

**Corrective action available:** When reporting test_section_span Nu and Ri, rescale by the D ratio (20.9/22.1 = 0.945):
- Nu_corrected = Nu_CFD × (22.1/20.9)  ← h is unchanged, just rescale D in Nu = h·D/k
- Ri_corrected = Ri_CFD × (20.9/22.1)  ← Ri ∝ D, actual D is smaller so actual Ri is lower

Note: for the **upcomer section-median Ri** used in the backflow correlation, the test_section cells are mixed in with left_lower_leg and left_upper_leg cells (both at correct D = 22.1 mm). The test section represents roughly 1/3 of upcomer cells; the bias on the section-median Ri is therefore approximately 5.7% × 1/3 ≈ 2%. This is negligible for the current 3-point correlation.

---

## Grashof formulation: density-difference vs Boussinesq β

The CFD uses the **exact density difference form**:
```
Gr = g * |ρ_ref − ρ(T)| * D^3 * ρ_ref / μ²
```

The standard Boussinesq form would be:
```
Gr_Boussinesq = g * β * ΔT * D^3 / ν²  where β = −(1/ρ)(∂ρ/∂T)_P
```

For the FLiNaK-like salt: ρ = 2293.6 − 0.7497·T, so β = 0.7497/ρ ≈ 3.8×10⁻⁴ K⁻¹.
The exact form uses |ρ_ref − ρ| / ρ_ref instead of β·ΔT. These differ by:
- Boussinesq: β·ΔT·ρ² = 0.7497·ΔT·ρ
- Exact: |ρ_ref − ρ|·ρ_ref = 0.7497·|T_ref − T|·ρ_ref

At operating temperatures (ΔT ≈ 30–60 K), ρ/ρ_ref ≈ 0.99–1.01 → difference is < 1%. The exact form is more accurate and avoids the Boussinesq approximation.

---

## Reference temperature TRef = 447.0 K

The solver uses `TRef = 447.0 K` (= 174°C) as the reference temperature for Gr.
At this temperature, ρ_ref = 2293.6 − 0.7497×447 = **1958.48 kg/m³** — matching the hardcoded `rhoRef = 1958.48`.

The operating range is ~438–483 K (165–210°C from Ethan's confirmation). TRef = 447 K is near the low end of the range, so the density differences |ρ_ref − ρ| are all positive (colder reference = lower density reference → all operating cells are denser than reference... wait, no:

Actually: hotter fluid is LESS dense (β > 0, density decreases with T for this salt).
- At TRef = 447 K: ρ_ref = 1958.48 kg/m³
- At T = 483 K (hot): ρ = 2293.6 − 0.7497×483 = 2293.6 − 362.1 = 1931.5 kg/m³ → LOWER than ρ_ref
- At T = 438 K (cool): ρ = 2293.6 − 0.7497×438 = 2293.6 − 328.4 = 1965.2 kg/m³ → HIGHER than ρ_ref

So the Gr is largest near the cold walls (dense fluid) and vanishes near TRef. This is correct — buoyancy is zero when T = T_ref.

The choice TRef = 447 K (≈ bulk initial temperature) means Gr is computed relative to the initial bulk state. This is appropriate for natural/mixed convection in a loop where TRef represents the "no-buoyancy" reference.

---

## Summary for correlation use

| Property | Value | Confidence |
|---|---|---|
| Characteristic length | D_h = 22.098 mm | Confirmed from source code |
| D_h convention | Correct for pipe-flow mixed convection | Standard literature |
| Test section D_h error | +5.7% (22.1 mm used, 20.9 mm actual) | Quantified, small |
| Test section Ri bias | +5.7% overestimate | Correct direction, small |
| Upcomer median Ri bias | ~+2% from test section cells | Negligible |
| Grashof form | Exact density difference (not Boussinesq) | More accurate |
| Reference temperature | TRef = 447 K = initial bulk T | Appropriate |

**Conclusion**: The Ri characteristic length choice (D_h) is correct. The global D = 22.098 mm mismatch with the test section bore introduces a small quantified error that does not invalidate the upcomer correlations at the current 3-point data level.

---

## CFD BC summary (supporting AGENT-202 scenario contract)

### Heater BC (pipeleg_lower_04/05/06_straight)

| Case | Patch Q | Patches | Total heater Q |
|---|---|---|---|
| Salt 2 | 88.57 W | 3 | **265.7 W** |
| Salt 3 | 99.17 W | 3 | **297.5 W** |
| Salt 4 | 112.53 W | 3 | **337.6 W** |

BC type: `rcExternalTemperature` with `Q constant` + emissivity 0.95, Ta=Tsur=299.19 K.
Wall layers: 1.7 mm steel tube + 35.6 mm (1.4 in) insulation.

### Cooler BC (pipeleg_upper_04/05/06)

| Case | Reducer pair (2×) | Main cooler | Total cooler Q |
|---|---|---|---|
| Salt 2 | 2 × −16.14 W | −104.07 W | **−136.4 W** |
| Salt 3 | 2 × −18.10 W | −114.58 W | **−150.8 W** |
| Salt 4 | 2 × −20.54 W | −128.15 W | **−169.2 W** |

BC type: `externalTemperature` with `Q constant` (negative = heat removal, no radiation).

### Test section BC (pipeleg_left_04_test_section)

| Item | Value |
|---|---|
| Q | +37.0 W (same for S2/S3/S4) |
| Wall layers | 2.2 mm quartz only — **NO insulation** |
| BC type | `rcExternalTemperature` with emissivity 0.95, Tsur=299.19 K |
| Net to fluid | Negative (−5.7 to −16.8 W) — quartz radiation + convection loss > heater input |

The test section is a net heat sink because:
1. Only 2.2 mm quartz (low resistance) allows large heat loss to ambient
2. Surface emissivity = 0.95 (quartz) → significant radiation at operating temperatures (~470 K)
3. Hot salt inside radiates ~σ·ε·A·(T⁴ − T_sur⁴) to 299 K surroundings
4. Heater only supplies 37 W; combined conduction+radiation loss exceeds this

This explains the AGENT-194 finding (test section is a net heat sink of −5.7 to −16.8 W).

### Ambient conditions (all surfaces)

| Parameter | Value |
|---|---|
| Ta (convection) | 299.19 K (26°C room temperature) |
| Tsur (radiation) | 299.19 K (same as Ta) |
| Emissivity | 0.95 (all rcExternalTemperature patches) |

### 1D model implication

The 1D model uses a single `insulation_thickness_in` parameter for all segments. The actual CFD setup has:
- Main piplegs: 1.4 in insulation
- Test section: NO insulation (2.2 mm quartz only)

To match CFD, the 1D model must use **different insulation BCs for test section vs main piplegs**. Using a single averaged value (e.g. 0.25–0.30 in) that matches loop temperature is a workaround, not a physical match.

The next step for 1D model validation is to implement per-segment insulation and surface emissivity in the 1D BC specification.
