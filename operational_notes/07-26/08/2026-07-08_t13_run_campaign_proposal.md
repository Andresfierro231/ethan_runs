# T13 CFD Campaign Proposal: Onset/Limit Re Sweep for Natural Circulation

Date: `2026-07-08`
Author: claude (AGENT-210)
Status: **Proposal — pending T2 requalification gate (AGENT-181)**

---

## 1. Motivation

The current TAMU loop Salt mainline data covers only 3 operating points
(S2/S3/S4 Jin, Re ≈ 68/90/123). With 3 points per leg class:

1. Phi vs Re fits have 1 degree of freedom (heater, cooler) or are unreliable
   (downcomer — Ri-driven anomaly)
2. Ri vs Re are collinear: can't separate buoyancy effects from Re-dependent
   entry-length/development effects
3. No information on onset or limit of the upcomer recirculation cell

This campaign pushes Re to 150–300 by increasing heater power Q in CFD (no geometry
change; Q is a boundary condition that can be set freely in the simulation).

---

## 2. Scaling analysis: Re vs Q for natural circulation

For natural circulation, mdot ∝ Q^(1/3) approximately (energy balance + momentum balance
for turbulent/laminar resistance-dominated flow). Viscosity also decreases with T:
at higher Q, the loop runs hotter → μ decreases → Re increases faster than Q^(1/3).

Anchor: Salt 3 Jin, Q = 297.5 W, Re_heater = 90.

| Q (W) | Q/Q_S3 | mdot factor | T increase | μ factor | Re estimate |
|---|---|---|---|---|---|
| 297.5 (S3) | 1.0 | 1.00 | baseline | 1.00 | 90 |
| 595 | 2.0 | 1.26 | +30 K | ×1.06 | ~107 |
| 1190 | 4.0 | 1.59 | +70 K | ×1.13 | ~161 |
| 2380 | 8.0 | 2.00 | +130 K | ×1.23 | ~221 |
| 4760 | 16.0 | 2.52 | +220 K | ×1.35 | ~305 |
| 9520 | 32.0 | 3.17 | +350 K | ×1.50 | ~428 |

The viscosity multiplier (μ_S3 / μ_hot) is estimated from a 10%/100 K viscosity
reduction for molten fluoride salt (approximate; exact value from Jin model).

**To reach Re = 200**: Q ≈ 2000–2500 W (7–8× S3). Feasible in CFD.  
**To reach Re = 300**: Q ≈ 4000–5000 W (13–17× S3). Aggressive but feasible.  
**To reach Re = 400**: Q ≈ 10 kW. Challenging for convergence.

---

## 3. Proposed campaign design

**Anchor case**: Salt 3 Jin (accepted mainline case, Re=90).

**Series A — Q sweep at standard insulation (1.4 in main piplegs)**:

| Run ID | Q_heater (W) | Expected Re | Notes |
|---|---|---|---|
| T13-A1 | 595 | ~107 | 2× S3 Q |
| T13-A2 | 1190 | ~161 | 4× S3 Q |
| T13-A3 | 2380 | ~221 | 8× S3 Q; upcomer recirculation may weaken |
| T13-A4 | 4760 | ~305 | 16× S3 Q; push through upcomer onset |
| T13-A5 | 9520 | ~428 | 32× S3 Q; optional, convergence-risk |

Start each run from the previous converged solution (temperature restart). Use
the same corrected BC structure as 2026-07-04 corrected perturbation runs.

**Do not run T13-A4/A5 before T13-A3 is converged and the upcomer onset is located
in the A1/A2/A3 data.** The onset might be at Re~150-180 (based on recirculation
strength extrapolation from S2/S3/S4).

---

## 4. What to diagnose in each run

For each converged case:

1. **mdot**: has it moved vs previous case? Convergence check.
2. **Upcomer recirculation fraction** (backflow_area_fraction at left_lower_leg and
   left_upper_leg endpoints): does it decrease from the current 85–98% level?
3. **phi per leg class** (f_corrected / f_F3_shah): does phi decrease with Re as F6
   predicts? Or does it flatten/increase?
4. **Ri per leg class** (from secmeanSurfaces dimensionlessFields): does Ri decrease
   with Re as expected (Ri ∝ ΔT/V² → lower Ri at higher Re)?
5. **Loop temperature distribution**: does it remain physically realistic?
   (T_max < 700 K, no localized boiling-point artifacts)

---

## 5. OpenFOAM BC changes required

In `0/T`, change `pipeleg_lower_01` (and subsequent lower_leg patches) heater
`fixedGradient` or `wallHeatFlux` to the new Q value:

```
// Increase Q_heater from 297.5 W to new value
// Ensure that Q_heater is distributed proportionally across heater patches
// The wallHeatFlux BC already handles this — just change heater_power_W in case_config.yaml
```

Verify: `case_config.yaml` → `heater_power_W: 595.0` (or appropriate value).
All other BCs unchanged.

---

## 6. Admission criteria

Runs are admitted to the closure calibration pool when:

1. Solver time has advanced ≥ 3× the expected thermal time scale
   (estimated as loop length / mdot velocity ≈ 2.0 m / 0.02 m/s = 100 s)
2. mdot variation < 1% over last 1000 solver time steps
3. No `convergenceMonitor` fatal stop
4. The corrected Q perturbation runs (AGENT-181 gate) are requalified first

---

## 7. Dependencies

- **T2** (AGENT-181 gate): corrected Salt Q perturbation runs must clear the gate
  before T13 runs are submitted (to avoid contaminating the operating band with
  unqualified data)
- **T13 is independent of T6** (GCI/mesh independence): T13 uses the same coarse mesh
  as the mainline cases; GCI bounds are a separate quality metric

---

## 8. Expected scientific value

With 5 additional operating points spanning Re 90–300:
- phi vs Re fit upgrades from 1 DOF (3 pts) to 6 DOF (8 pts)
- phi vs Ri fit becomes separable from phi vs Re (Ri and Re no longer collinear
  once Q varies 16× independently)
- Upcomer recirculation onset Re is located experimentally
- F5 Ri correction can be meaningfully re-fit

---

**Prerequisites to start T13:**
1. AGENT-181 gate cleared (T2)
2. Codex coordinator approval of run plan
3. Ethan confirmation that high-Q BCs are physically acceptable for the CFD study
