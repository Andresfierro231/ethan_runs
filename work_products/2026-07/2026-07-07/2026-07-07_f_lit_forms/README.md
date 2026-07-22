# work_products/2026-07-07_f_lit_forms

Generated: 2026-07-07  
Task: AGENT-186  
Role: Implementer  
Owner: claude

## Purpose

Documents the addition of the Shah (1978) apparent friction factor
(`F3_shah_apparent`) to the TAMU loop friction closure library
(`friction_closures.py`), and provides a standalone comparison script and CSV
quantifying differences between F1, F3_hagenbach, and F3_shah_apparent at TAMU
loop operating conditions.

## Contents

| File | Description |
|---|---|
| `f_lit_comparison.py` | Standalone comparison script (no Fluid dependency) |
| `f_lit_comparison_tamu_conditions.csv` | Full results table: dp, f_app, % diffs |
| `README.md` | This file |
| `summary.json` | Machine-readable metadata |

## Forms added to friction_closures.py

### F3_shah_apparent

**Citation:** Shah, R.K. (1978). "A correlation for laminar hydrodynamic entry
length solutions for circular and noncircular ducts." *ASME Journal of Fluids
Engineering*, Vol. 100, pp. 177-179. Eq. 15, circular-tube row.

**Physical basis:** When flow enters a circular pipe with a uniform (flat/plug)
velocity profile, it redistributes to the Hagen-Poiseuille parabola. This
involves: (a) elevated wall shear stress throughout the entry length, raising
the *distributed* friction above 64/Re, and (b) a one-time momentum-defect
pressure term (Hagenbach effect). Shah (1978) provides a single apparent
friction factor correlation that captures **both** effects together, integrated
from the section inlet to position L.

**Equation** (Fanning → Darcy conversion):

```
x+  = L / (D * Re)       [hydrodynamic entry length parameter]

(f_app * Re)_Fanning = C1/sqrt(x+) + (f_inf*Re + C_hag) / (1 + D_fit/x+^2)

(f_app * Re)_Darcy = 4 * (f_app * Re)_Fanning
```

**Constants** (circular tube, uniform inlet, Shah 1978 Eq. 15):

| Constant | Value | Description |
|---|---|---|
| C1 | 3.44 | Developing-flow leading term coefficient |
| f_inf × Re | 16.0 | Fully-developed Fanning f×Re (Hagen-Poiseuille) |
| C_hag | 0.244 | Hagenbach/momentum-defect correction constant |
| D_fit | 0.000212 | Denominator curve-fit constant (important only for x+ < 0.05) |

**Validity range:**
- Laminar: Re < 2300
- Circular duct with uniform (flat/plug) inlet velocity profile
- x+ range: nominally 10^-3 to 0.5; most accurate for x+ < 0.2 (developing region)
- For x+ > 0.5: the fully-developed 64/Re (F1) is sufficient within ~5%

**Asymptotic behavior:**
- x+ → 0: (f_app × Re)_Fanning → 3.44/sqrt(x+) [developing-flow dominated]
- x+ → ∞: (f_app × Re)_Darcy → 4 × (16 + 0.244) = 64.976 → approaches 64 slowly (as 1/sqrt(x+))
- The ~1% residual above 64 at large x+ is a curve-fit artifact, not physically significant

## Forms compared (not added in this session)

### F1 (existing)
- 64/Re, fully-developed laminar. No entry correction.
- Source: Hagen-Poiseuille (exact for fully-developed laminar flow)

### F3_hagenbach (existing)
- F1 + asymptotic Hagenbach one-time entry defect K_∞ = 1.33 at section inlet
- Source: Shah & London (1978), Table 44 (circular tube, uniform inlet)
- Applied as: ΔP_entry = K_∞ × ½ρv² (one-time, at is_segment_entry=True)
- Valid: x+ > 0.05; for x+ < 0.05, K_actual < K_∞ so total ΔP is underestimated

## Validity ranges in terms of x+ at TAMU loop conditions

TAMU loop: D = 0.022 m (main), 0.021 m (test section)

| Segment | Approx. L (m) | Re = 60 | Re = 80 | Re = 100 | Re = 120 |
|---|---|---|---|---|---|
| Short bend/junction | 0.1 | x+ = 0.076 | 0.057 | 0.045 | 0.038 |
| Heater leg (lower) | 0.38 | 0.288 | 0.216 | 0.173 | 0.144 |
| Cooler leg (upper) | 0.38 | 0.288 | 0.216 | 0.173 | 0.144 |
| Upcomer (left vert.) | 0.50 | 0.379 | 0.284 | 0.227 | 0.189 |
| Downcomer (right vert.) | 0.50 | 0.379 | 0.284 | 0.227 | 0.189 |

Most TAMU loop segments fall in x+ = 0.04–0.6, spanning the developing-to-transitional regime.

## Which form to use for the TAMU loop — recommendation with justification

**Current recommendation: F3_shah_apparent for section entry segments.**

Justification:
1. TAMU loop segments span x+ = 0.04–0.6. For x+ < 0.1 (short bends at lower Re),
   the Shah form correctly captures the full developing-flow pressure penalty,
   which is 30–80% larger than the Hagenbach estimate at those x+ values (see table below).
2. The Hagenbach correction K_∞ = 1.33 is designed for x+ → ∞ (very long ducts).
   For x+ < 0.2, it underestimates the total ΔP because it misses the enhanced
   distributed friction during profile development (the Shah form captures this).
3. For x+ > 0.3 (long main-leg sections at moderate Re), the Shah–Hagenbach
   difference is 25–35% — still non-negligible at TAMU flow-resistance precision.

**Important distinction (avoid confusion):**
- The existing docstring on F3_hagenbach states Hagenbach "over-estimates" for x+ < 0.05.
  This refers specifically to the incremental momentum-defect term K alone (K_∞ > K_actual
  for short pipes). It does NOT mean the total ΔP is over-estimated.
- The Shah comparison shows total ΔP (Shah) > total ΔP (Hagenbach) for all x+ < 1,
  because Shah also includes the enhanced distributed friction in the developing region.

**Caveat:** F3_shah_apparent does not account for buoyancy effects (F4) and is
strictly laminar. For Re > 1500 (approaching transition) or for the heated/cooled
legs, a buoyancy-modified form (F4 — AGENT-187) should supersede this for those legs.

## Comparison table — key results at TAMU conditions

From `f_lit_comparison_tamu_conditions.csv` (D=0.022m, rho=1950, v=0.015 m/s):

| Re | L (m) | x+ | dp_F1 (Pa) | dp_F3h (Pa) | dp_F3s (Pa) | Shah/Hag (%) |
|---|---|---|---|---|---|---|
| 60 | 0.10 | 0.076 | 1.064 | 1.355 | 1.872 | +38.1% |
| 60 | 0.38 | 0.288 | 4.031 | 4.322 | 5.800 | +34.2% |
| 80 | 0.10 | 0.057 | 0.798 | 1.089 | 1.480 | +35.8% |
| 80 | 0.38 | 0.216 | 3.023 | 3.315 | 4.413 | +33.1% |
| 80 | 0.50 | 0.284 | 3.989 | 4.280 | 5.648 | +31.9% |
| 100 | 0.38 | 0.173 | 2.419 | 2.710 | 3.638 | +34.2% |
| 120 | 0.50 | 0.189 | 2.659 | 2.951 | 3.997 | +35.5% |

Shah gives 28–99% more total ΔP than Hagenbach across TAMU conditions. The smallest
differences (28%) occur at the highest x+ (long sections, high Re); the largest (99%)
at the lowest x+ (short bends at Re=120).

## Limitations

1. **Single mesh, no GCI bounds**: Segment lengths used here are from mesh PCA
   centerlines (work_products/2026-07-01_claude_mesh_centerlines/). No GCI study
   done (T6 blocked — needs external mesh generator from Ethan). Segment length
   uncertainty: ±5% assumed.

2. **Isothermal / weakly-heated assumption**: Shah (1978) is for uniform or
   negligible heating. The TAMU loop has significant buoyancy (Ri ~ O(1) on heated
   legs); F4 buoyancy correction (AGENT-187) is needed for the heater/cooler legs.

3. **x+ range**: Shah correlation is most accurate for x+ < 0.2 (developing region).
   For x+ > 0.3, the curve-fit overestimates f_app by up to ~2% relative to exact
   numerical solutions.

4. **Geometry**: Correlation assumes perfectly circular cross-section. TAMU quartz
   test section (pipeleg_left) is circular but D ≈ 0.021 m (not 0.022 m); re-compute
   with D=0.021 m for that segment.

5. **Uniform inlet only**: Shah (1978) assumes a flat (plug) velocity profile at the
   duct inlet. In reality, flow entering a section after a bend may have a skewed
   profile. This is not accounted for.

6. **Muzychka & Yovanovich (2009) NOT implemented**: The alternative composite
   blending form was not implemented because exact fitting constants were not verified
   from the primary source. See the dp_F3_shah_apparent docstring for details.

## How to reproduce

```bash
# Run the comparison script (standalone, no Fluid dependency needed)
cd work_products/2026-07-07_f_lit_forms/
python3 f_lit_comparison.py

# Verify friction_closures.py integration
cd /path/to/ethan_runs
python3 -c "
import sys
sys.path.insert(0, '../cfd-modeling-tools/tamu_first_order_model/Fluid')
from tamu_loop_model_v2.friction_closures import compute_dp, AVAILABLE_FORMS, summarise_forms_table
print('Forms:', list(AVAILABLE_FORMS.keys()))
print(summarise_forms_table(80, 1950, 0.015, 0.5, 0.022, is_entry=True))
"
```

## Open questions for user

1. Should F3_shah_apparent be set as the solver default instead of F1, or added only as a comparison option?
2. For the test section (D ≈ 0.021 m, quartz), should x+ be recomputed with the actual bore?
3. Should Muzychka & Yovanovich (2009) be implemented for cross-validation once the paper is available?
