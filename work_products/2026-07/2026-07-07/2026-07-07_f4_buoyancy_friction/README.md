# F4 Buoyancy-Friction Calibration

**Task:** AGENT-187  
**Date:** 2026-07-07  
**Role:** Implementer  
**Owner:** claude

---

## Purpose

Build a data-driven leg-class friction multiplier (F4) for the TAMU 1D loop
model.  The goal is to close the gap between the F1/F3 predictions and the
de-buoyed CFD friction factors from the mainline Salt 2/3/4 Jin momentum budget.

This is a first-pass data-driven closure.  A Ri-corrected form (buoyancy-modified
friction for heated/cooled inclined legs) is left for a future task.

---

## Physical Motivation

F1 (64/Re) and F3 (Hagenbach entry correction) cannot explain the factor-2 to
3× excess de-buoyed friction observed in the CFD momentum budget:

| Leg class | Span(s) | f/f_lam range | F3h range | Residual |
|---|---|---|---|---|
| heater | lower_leg | 2.67–2.88 | 1.09–1.16 | ~2.4–2.5× |
| cooler | upper_leg | 2.23–2.38 | 1.08–1.15 | ~2.1× |
| downcomer | right_leg | 2.19–3.26 | 1.08–1.15 | ~2.0–2.8× |
| upcomer | left_lower_leg + test + left_upper | 0.82–2.21 | 1.21–1.54 | 0.6–1.5× |

The heater and cooler are inclined (~21–22° from horizontal) and thermally
active.  In laminar mixed convection on inclined tubes, the velocity profile
is distorted by buoyancy-induced secondary flows (Richardson-number effect),
increasing effective friction by factors of 2–5 relative to the isothermal
fully-developed value.  This is the primary suspected physical mechanism.

The downcomer shows a strongly Re-dependent excess (b ≈ -134 in the a+b/Re
fit), which may reflect entrance effects from the upper elbow or a different
mechanism; further investigation is needed.

The upcomer behavior is complex due to the recirculation cell: left_upper_leg
has f/f_lam < 1 (friction suppressed by backflow), while left_lower_leg shows
enhancement.  A single "upcomer" coefficient is a poor approximation (R²=0.02).

---

## What Was Available

**Data used:**
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`  
  (de-buoyed per-leg friction factors, Salt 2/3/4 Jin mainline continuations)
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`  
  (segment arc lengths per span)

**Admission policy:**
- Salt 2/3/4 Jin mainline continuations: **ADMITTED** (3 cases, 6 legs each)
- Salt 1 Jin: **EXCLUDED** — weakly converged
- Corrected Salt Q perturbations (jobs 3275448–3275451): **EXCLUDED** — not yet
  requalified; formal gate (`operating_point_verdict=requalified`) not yet issued

**What was NOT available:**
- Wall temperature per leg (required for Ri = g β ΔT D / ν² per section)
- Ri data: cannot be extracted without running the thermal HTC extraction tool
  per leg (`sample_segment_htc_uaprime.py`) AND comparing wall vs. bulk T
- Corrected Q perturbation steady-state data (would add ~12 more Re points)
- GCI bounds (mesh-independence not yet established; T6 blocked)

---

## Fit Model

    f_corrected / f_lam = a + b / Re        (linear in 1/Re, OLS)

    where  f_lam = 64/Re  (Hagen-Poiseuille)

This form captures the Re-dependence within the Salt 2–4 operating band
(Re ≈ 60–135).  It is NOT a Ri-corrected closure.

### Fitted Coefficients (from run_f4_calibration.py)

| Leg class | a | b | R² | RMSE | n | Re range |
|---|---|---|---|---|---|---|
| heater | 3.113 | -31.82 | 0.876 | 0.032 | 3 | 68–123 |
| cooler | 2.549 | -20.12 | 0.981 | 0.008 | 3 | 63–115 |
| downcomer | 4.361 | -134.05 | 0.991 | 0.041 | 3 | 61–118 |
| upcomer | 1.548 | -19.62 | 0.015 | 0.431 | 9 | 67–135 |

**Key findings:**
- heater/cooler: reasonable fits, excess consistent with mixed-convection
  velocity-profile distortion; Ri correction expected to improve R²
- downcomer: excellent fit (R²=0.99), large |b| implies strong Re-dependence;
  mechanism not yet physically interpreted
- upcomer: R²=0.02 (nearly zero predictive value as a single class); the
  three sub-legs have physically distinct behavior and should NOT be merged
  into a single correlation

---

## Comparison: F1 vs F3h vs F4 vs CFD

(Sample at Re=90, Salt 3 operating point, using segment-mean conditions)

| Form | f/f_lam (heater) | f/f_lam (cooler) | f/f_lam (downcomer) |
|---|---|---|---|
| F1 | 1.000 | 1.000 | 1.000 |
| F3_hagenbach | ~1.11 | ~1.11 | ~1.11 |
| F4_leg_class | 2.76 | 2.33 | 2.87 |
| CFD target | 2.72 | 2.30 | 2.72 |

F4 reproduces the CFD heater/cooler well; downcomer has slight overprediction
at Re=90 (fit is exact at the training points).

---

## Implementation

The F4_leg_class closure was added to:
```
../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py
```

Usage:
```python
from tamu_loop_model_v2.friction_closures import compute_dp

bd = compute_dp("F4_leg_class", Re=90.0, rho=1950.0, v=0.016,
                L_m=0.36, D_m=0.022, leg_class="heater")
print(bd.dp_total_Pa)   # total pressure drop [Pa]
print(bd.f_D_fd)        # effective Darcy friction factor
```

Solver default remains `friction_form="F1"` (unchanged).

---

## Limitations

1. Only 3 data points per class (n_points=3 for heater/cooler/downcomer)
2. No Ri correction; wall-bulk ΔT not extracted; expected to matter most for
   heater/cooler (inclined, thermally active legs)
3. Upcomer class is physically ambiguous; R²=0.02 means the fit has no
   predictive value within the upcomer class
4. No GCI bounds (coarse mesh only; T6 blocked pending external mesh generator)
5. Driver-side thermal mismatch (~60 K overprediction found in AGENT-journal
   2026-07-02) means mdot improvement from F4 alone is expected to be limited
6. Extrapolation beyond Re=135 is unreliable; form is valid only in Salt 2–4
   operating range

---

## Path to Ri-Corrected F4

To implement a physics-based Ri-corrected form (Petukhov, Jackson, ASHRAE, etc.):

1. Run `tools/extract/sample_segment_htc_uaprime.py` on mainline Salt 2/3/4 Jin
   (OF13 env required; libRCWallBC.so)
2. From HTC and Q_wall per leg, compute: ΔT_wall_bulk = Q_wall / (HTC × A_wall)
3. Compute Ri = g β ΔT D / ν² per leg (use section-MEDIAN Ri, not mean — see
   AGENTS.md / CLAUDE.md gotcha #4)
4. Project by streamwise gravity: Ri_streamwise = Ri × cos(θ) for inclined legs
5. Re-fit: f/f_lam = f3h_ratio × (1 + C_leg × max(Ri_streamwise, 0)^n)
6. Open a new Implementer task to add this form to friction_closures.py

---

## Reproduction

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python3 work_products/2026-07-07_f4_buoyancy_friction/run_f4_calibration.py
```

Outputs:
- `f4_calibration_dataset.csv` — 18 rows (3 cases × 6 legs), all computed quantities
- `f4_fit_summary.json` — fitted (a, b, R², RMSE) per leg class, machine-readable
- `f4_fit_summary.csv` — same, CSV form
