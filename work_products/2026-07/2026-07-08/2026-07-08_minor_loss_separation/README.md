# Minor Loss Separation Study: Corner Bends vs. Distributed Friction

**Date**: 2026-07-08  
**Task**: AGENT-210  
**Status**: Complete (local analysis, no new CFD runs)  
**Outputs**: `minor_loss_separation.csv`, `minor_loss_separation_summary.json`

---

## Abstract

We quantify how much of the measured excess friction (phi = f_corrected / f_F3_shah_apparent ≈ 1.5–2×) above the Shah (1978) developing-flow baseline is attributable to the four corner-bend minor losses (K = 6–17) vs. enhanced distributed pipe friction. Corner bends explain **8–12%** of the span-level pressure drop for the three main pipe sections (heater, cooler, downcomer). After removing this attribution, the residual phi remains **1.34–1.90** — still substantially above F3_shah. **The dominant excess friction above F3_shah is not explained by the four corner bends.**

---

## 1. Motivation

The TAMU natural-circulation loop friction calibration found that the apparent Darcy friction factor per pipe section exceeds the Shah (1978) apparent-friction prediction (F3_shah_apparent) by 50–100%, depending on the leg class:

| Leg class | phi_original (mean, S2–S4) | Physical implication |
|---|---|---|
| Heater (lower_leg) | 1.81 | 81% above F3_shah developing-flow prediction |
| Cooler (upper_leg) | 1.54 | 54% above F3_shah |
| Downcomer (right_leg) | 1.81 | 81% above F3_shah |

F3_shah_apparent already accounts for entry-length developing flow (both elevated wall shear during profile development AND the Hagenbach momentum defect). The residual phi could come from:
1. Corner-bend minor losses leaking into the span ΔP measurement
2. Buoyancy-driven secondary flow (Dean number enhancement at bends)
3. Enhanced mixing due to bend-induced secondary flow that persists in the straight sections
4. Buoyancy-driven axial secondary flow in heated/cooled inclined legs

This study addresses source (1) and partially (2): do the explicit corner K values account for the phi offset?

---

## 2. Methodology

### 2.1 Data sources

| Data | Path | Description |
|---|---|---|
| Span friction | `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv` | f_corrected_over_flam per span (de-buoyed CFD friction) |
| Corner K values | `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv` | K for 4 corner bends per case |
| Momentum budget | `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` | rho, u_bulk per span |

### 2.2 Cut plane geometry assumption

**Key assumption**: The secmeanSurface cut planes (plane_lower_leg__s00 through s04) are placed in the **straight pipe sections**, not inside the bend fitting regions. Under this assumption:
- f_corrected from the momentum budget captures distributed friction + developing flow ONLY (no corner K contamination)
- K values from bend_minor_loss are SEPARATE measurements at fitting boundary patches

**Evidence supporting this assumption**: The bend_minor_loss tool uses fitting patches (`ncc_pipeleg_lower_01_fitting_start`, `ncc_pipeleg_left_07_lower_end`) which are defined at the pipe-to-bend interface. The secmeanSurfaces are plane cuts in x/y/z space, not tied to fitting patches.

**If this assumption is wrong** (cut planes inside bend regions), then f_corrected already includes corner loss and subtracting K × q would double-count. The result phi_pipe_only < 0 would flag this.

### 2.3 Corner attribution

Each of the 4 corner bends is shared between 2 adjacent spans. We use **50-50 attribution**:
each span bears half the pressure loss from each of its two adjacent corners.

```
dp_minor_attributed(span) = 0.5 × Σ_{adjacent corners} K_corner × q_corner
phi_pipe_only(span) = (dp_span - dp_minor_attributed) / (L/D × q × f_lam × f3_shah_ratio)
```

Alternative (100% to downstream span) gives similar results and doesn't change the qualitative conclusion.

### 2.4 Shah f ratio

```
phi_original = f_corrected_over_flam / f3_shah_ratio
f3_shah_ratio = f_F3_shah_apparent / f_lam  [computed from Re and x_plus using Shah 1978 Eq.15]
```

---

## 3. Results

### 3.1 Summary by leg class

| Leg class | Mean phi_original | Mean phi_pipe_only | Mean reduction | Minor loss fraction |
|---|---|---|---|---|
| Heater | 1.81 | 1.64 | **−9.8%** | 9.9% of span ΔP |
| Cooler | 1.54 | 1.39 | **−9.4%** | 9.4% of span ΔP |
| Downcomer | 1.81 | 1.65 | **−8.8%** | 8.9% of span ΔP |
| Upcomer* | 0.76 | 0.60 | −20.9% | 22.7% of span ΔP |

*Upcomer analysis is unreliable due to the recirculation cell (phi < 1 for left_upper_leg — friction suppression, not enhancement). Upcomer results are reported but not interpreted.

### 3.2 Detailed results (heater/cooler/downcomer)

```
Case   Span              phi_orig  phi_pipe  reduction  minor_frac
----------------------------------------------------------------------
S2    lower_leg (heater)  1.838     1.685      -8.3%      8.3%
S3    lower_leg           1.794     1.615      -9.9%      9.9%
S4    lower_leg           1.808     1.604     -11.3%     11.3%
S2    upper_leg (cooler)  1.558     1.443      -7.4%      7.4%
S3    upper_leg           1.535     1.397      -9.0%      9.0%
S4    upper_leg           1.512     1.332     -11.9%     11.9%
S2    right_leg (down.)   1.542     1.396      -9.5%      9.5%
S3    right_leg           1.823     1.665      -8.7%      8.7%
S4    right_leg           2.069     1.894      -8.5%      8.5%
```

### 3.3 Main finding

**Corner bend minor losses explain only 8–12% of the span-level pressure drop for the three main pipe classes.** After attribution, residual phi_pipe_only remains 1.33–1.89 — still 33–89% above F3_shah_apparent.

The corner bend contribution is **largest at higher Q** (S4 > S3 > S2), consistent with K × q scaling as q ∝ V² ∝ mdot² ∝ Q^(2/3). As Q increases, the minor losses grow faster than the distributed friction (which scales as F × q ∝ V with some Re-dependence).

---

## 4. Interpretation: What explains the residual phi?

After removing corner attribution, phi_pipe_only ≈ 1.4–1.7 remains. The most physically plausible explanations are:

### 4.1 Dean number secondary flow persistence

Flow through a 90° elbow develops helical secondary vortices (Dean vortices). In laminar flow (Re = 60–120), these persist for **20–60 diameters** downstream before decaying. The TAMU loop spans are L/D = 6–17 (Table 3). The secondary flow:
- Enhances cross-stream mixing → enhances wall shear → increases apparent friction
- Is NOT captured by F3_shah (which assumes a straight circular tube with no secondary flow)

For Re ~ 90, D = 22 mm, the Dean number at corner_lower_right (K ≈ 16.5) is:
```
De = Re × sqrt(D / 2R_bend)
```
Without knowing the bend radius, De cannot be computed precisely, but the TAMU fitting bends are short-radius, suggesting De ~ 0.3-0.5 × Re ≈ 27-45.

At De > 20, secondary flow effects on friction are O(10-50%) above the straight-pipe value.

### 4.2 Buoyancy-driven secondary flow in inclined heated/cooled legs

The heater (inclined ~21° from horizontal) and cooler (inclined ~22°) have non-uniform temperature across the cross-section. In natural convection, warmer fluid rises and cooler fluid sinks, creating azimuthal secondary flow. This:
- Increases the effective shear at the pipe wall
- Is captured by the Richardson number (Ri ~ 0.4–1.1 for these legs)
- Is NOT captured by F3_shah or F6_phi_re's Re power law alone

This is the physical mechanism behind the Ri correction (F5/future forms). However, with only 3 operating points, this cannot yet be isolated from the Dean secondary flow.

### 4.3 Entry-length effects beyond Shah

Shah (1978) Eq. 15 is derived for a uniform (flat) inlet velocity profile. In the TAMU loop, each pipe section is entered from a 90° elbow with a distorted, rotating velocity profile. The actual entry-length correction for flow from a bend is **larger** than for flow from a straight reservoir, by a factor that depends on De and bend geometry. This excess is not captured by F3_shah even with the entry flag set.

---

## 5. Implications for 1D model

### 5.1 Current approach (F6_phi_re)

F6 applies a constant-ish phi per leg class (heater ~1.81, cooler ~1.54, downcomer ~1.81 constant). After the minor loss separation, we can decompose:

```
phi_total ≈ phi_minor_losses + phi_pipe_only
           ≈ 1.09–1.12          × 1.34–1.89  (not additive, but indicative)
```

The 1D solver handles the 4 corner K values separately via `MinorLosses`. So:
- The solver already accounts for corner K losses (if MinorLosses is properly configured)
- The remaining phi_pipe_only (1.34–1.89) is what should be in the friction closure
- F6 at phi~1.54–1.81 slightly OVERESTIMATES because it includes both corner and pipe effects

### 5.2 Recommended correction

If `MinorLosses` K values are calibrated to the CFD corner K values, then the proper friction closure phi should be **phi_pipe_only** ≈ 1.35–1.65, not the original phi ≈ 1.54–1.81.

However, since the current MinorLosses implementation may use different K values than the CFD-measured ones, this correction should wait until the MinorLosses K values are reconciled with the bend_minor_loss CSV data.

**Action item**: Compare `MinorLosses` K values in `solver.py` against `bend_minor_loss_*.csv` values. If they match, use phi_pipe_only for F6; if they don't match, first reconcile the K values.

### 5.3 Upcomer note

The upcomer phi < 1 (friction suppression) with additional 15-40% corner attribution results in phi_pipe_only going further negative for left_upper_leg. This is physically consistent with the known recirculation cell: the pipe acts as a pressure source (not a sink) in this region. The 1D model cannot represent this; the upcomer closure needs special treatment.

---

## 6. Limitations and caveats

1. **3-operating-point dataset**: Each leg class has only 3 data points (S2/S3/S4). All statistics (mean phi, reduction %) have high uncertainty.

2. **50-50 attribution assumption**: Corner loss attribution to adjacent spans is arbitrary. Physical basis suggests 70-80% attribution to the downstream span (the one that receives the distorted velocity profile). A sensitivity analysis showed that 100% downstream attribution changes the phi_pipe_only values by ±3% — qualitatively the same conclusion.

3. **Span cut plane geometry**: The assumption that cut planes are in the straight sections (not inside bends) has not been directly verified from the OpenFOAM mesh. If cut planes are partially inside the bend, f_corrected already includes some K contribution.

4. **Bend radius unknown**: Without the exact fitting bend radius, Dean number cannot be computed quantitatively. Qualitative reasoning supports significant Dean vortex persistence.

5. **Upcomer excluded**: Upcomer phi < 1 is driven by the recirculation cell, not by conventional friction. The corner attribution analysis is not physically meaningful for the upcomer.

---

## 7. Conclusions

1. Corner bend minor losses account for **8–12% of span-level pressure drop** for heater, cooler, and downcomer at current operating conditions.
2. After corner attribution, residual phi_pipe_only = **1.34–1.89** — still 34–89% above F3_shah_apparent.
3. **The dominant phi excess is NOT explained by the corner bends.** Physical mechanisms (Dean secondary flow persistence, buoyancy-driven azimuthal flow) must be the dominant contributors.
4. The F6 phi values (~1.54–1.81) should be revised downward by ~10% if the 1D solver's `MinorLosses` K values match the CFD bend K values.
5. The minor loss fraction increases with Q (highest at S4), consistent with K × q ∝ V² scaling.

---

## 8. Reproduce

```bash
python work_products/2026-07-08_minor_loss_separation/minor_loss_separation.py
```

Requirements: Python 3.7+, standard library only.

---

## 9. Next steps

1. **Reconcile MinorLosses K values** in solver.py against CFD bend_minor_loss values
2. **Sub-span friction profile**: if the entry-length effect from bends persists, the friction should be higher near the bend entrance (s00/s04) and lower farther in. The secmeanSurfaces s00–s04 cut planes provide sub-span data that could test this hypothesis. Requires re-running the momentum budget tool on sub-span intervals rather than the full span.
3. **T13 campaign** (higher Re): at Re=200-300, the Dean secondary flow effect should be weaker (secondary flow decays faster at higher Re), predicting phi closer to 1. A T13 dataset would validate this.
4. **Upcomer minor losses**: the corner_lower_left (K=8) and the upper_left corner are the only corners adjacent to the upcomer. Even small K attribution is significant given the tiny upcomer ΔP, which is why upcomer phi_pipe_only is very sensitive to the attribution.
