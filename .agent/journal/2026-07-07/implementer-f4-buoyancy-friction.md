# F4 Buoyancy-Friction Calibration

Date: 2026-07-07  
Task: AGENT-187  
Role: Implementer  
Owner: claude

---

## Files Inspected (Read-Only)

- `AGENTS.md` — workspace rules, non-negotiable protocol
- `.agent/BOARD.md` — confirmed AGENT-187 row and scope
- `.agent/FILE_OWNERSHIP.md` — ownership rules
- `.agent/ROLES.md` — role definitions
- `work_products/2026-07-07_pressure_decomposition_f4_queue/README.md` — AGENT-184
  attack plan; read before any implementation decisions
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json` — per-leg
  de-buoyed friction factors for Salt 2/3/4 Jin
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv` — segment
  arc lengths, used for x_plus and F3h ratio computation
- `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv` — F3h ratio
  values for cross-check (confirmed match with computed values)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — existing F1/F3/F3_shah_apparent forms; AGENT-186 had already added F3_shah_apparent

## Files Changed

- `work_products/2026-07-07_f4_buoyancy_friction/run_f4_calibration.py` (NEW)
- `work_products/2026-07-07_f4_buoyancy_friction/f4_calibration_dataset.csv` (NEW, generated)
- `work_products/2026-07-07_f4_buoyancy_friction/f4_fit_summary.json` (NEW, generated)
- `work_products/2026-07-07_f4_buoyancy_friction/f4_fit_summary.csv` (NEW, generated)
- `work_products/2026-07-07_f4_buoyancy_friction/README.md` (NEW)
- `work_products/2026-07-07_f4_buoyancy_friction/summary.json` (NEW)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (EDITED — added F4_LEG_CLASS_FITS, dp_F4_leg_class, updated registry/compute_dp)
- `.agent/status/2026-07-07_AGENT-187.md` (NEW)
- `.agent/journal/2026-07-07/implementer-f4-buoyancy-friction.md` (THIS FILE)

## Commands Run

```bash
# Run calibration script (from ethan_runs repo root)
python3 work_products/2026-07-07_f4_buoyancy_friction/run_f4_calibration.py

# Verify F4_leg_class registration and correctness
python3 -c "
import sys; sys.path.insert(0, '../cfd-modeling-tools/tamu_first_order_model/Fluid')
from tamu_loop_model_v2.friction_closures import AVAILABLE_FORMS, compute_dp
print('Available forms:', list(AVAILABLE_FORMS.keys()))
assert 'F4_leg_class' in AVAILABLE_FORMS
# test each leg class
for lc in ['heater', 'cooler', 'downcomer', 'upcomer']:
    bd = compute_dp('F4_leg_class', Re=90.0, rho=1950.0, v=0.016, L_m=0.36, D_m=0.022, leg_class=lc)
    print(lc, bd.dp_total_Pa, bd.f_D_fd)
"

# Run full test suite
python3 -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q
```

## Results

**Calibration table (18 rows, 3 cases × 6 legs):**

```
salt     span                   leg_class         Re  f/f_lam   f3h_r  f4_res
salt_2   lower_leg              heater          68.0   2.6656  1.0864  2.4536
salt_2   right_leg              downcomer       61.2   2.1941  1.0758  2.0395
salt_2   left_lower_leg         upcomer         71.1   1.5512  1.2645  1.2268
salt_2   test_section_span      upcomer         68.8   1.4628  1.3016  1.1238
salt_2   left_upper_leg         upcomer         66.6   1.0369  1.2112  0.8561
salt_2   upper_leg              cooler          62.7   2.2334  1.0797  2.0686
salt_3   lower_leg              heater          90.2   2.7154  1.1146  2.4361
salt_3   right_leg              downcomer       84.7   2.7217  1.1050  2.4630
salt_3   left_lower_leg         upcomer         96.8   1.7872  1.3598  1.3143
salt_3   test_section_span      upcomer         91.1   1.1930  1.3992  0.8526
salt_3   left_upper_leg         upcomer         88.4   0.9056  1.2802  0.7074
salt_3   upper_leg              cooler          83.9   2.2975  1.1066  2.0762
salt_4   lower_leg              heater         122.6   2.8788  1.1558  2.4907
salt_4   right_leg              downcomer      118.0   3.2589  1.1462  2.8431
salt_4   left_lower_leg         upcomer        134.9   2.2092  1.5015  1.4713
salt_4   test_section_span      upcomer        123.7   1.0031  1.5422  0.6504
salt_4   left_upper_leg         upcomer        119.8   0.8209  1.3797  0.5950
salt_4   upper_leg              cooler         114.9   2.3804  1.1460  2.0772
```

**OLS fit results (f/f_lam = a + b/Re):**

```
leg_class           a          b      R2     RMSE    n       Re range
heater         3.1133     -31.82  0.8764  0.03201    3  68.0–122.6
cooler         2.5491     -20.12  0.9812  0.00826    3  62.7–114.9
downcomer      4.3614    -134.05  0.9910  0.04119    3  61.2–118.0
upcomer        1.5481     -19.62  0.0151  0.43125    9  66.6–134.9
```

**Test suite:** 217 tests passed, 0 failures.

## Observations

### Heater and Cooler (f/f_lam ~2.3–2.9)
Both heated/cooled inclined legs show f/f_lam consistently ~2.3–2.9 above the
laminar reference, after buoyancy decomposition.  F3h explains only ~5–16%.
This is the expected signature of laminar mixed-convection velocity-profile
distortion (Richardson-number effect).  The moderate R² for heater (0.88)
and excellent R² for cooler (0.98) suggest the Re-dependence alone explains
most of the variation, but Ri correction would reduce scatter further.

### Downcomer (f/f_lam 2.19–3.26, strongly Re-dependent)
The downcomer shows a large R²=0.99 fit with a very large negative b=-134.
This means at low Re (salt 2, Re~61) the excess is moderate (2.19), but at
higher Re (salt 4, Re~118) it climbs to 3.26.  This pattern is unusual for
a cold vertical leg where buoyancy effects should be small (isothermal-like).
Possible causes: (1) entry effects from the upper elbow are Re-dependent,
(2) the momentum budget has residual buoyancy in the downcomer not fully
removed by the decomposition.  This needs further physical scrutiny.

### Upcomer (R²=0.015 — essentially zero fit quality)
The three upcomer sub-legs have very different behavior:
- left_lower_leg: f/f_lam = 1.55, 1.79, 2.21 (strong enhancement)
- test_section_span: f/f_lam = 1.46, 1.19, 1.00 (decreasing with Re, near-laminar)
- left_upper_leg: f/f_lam = 1.04, 0.91, 0.82 (BELOW laminar, suppressed by backflow)

The recirculation cell (confirmed backflow 15–33% in AGENT-162) suppresses
left_upper_leg friction while enhancing left_lower_leg through local 3D effects.
Averaging these three into one "upcomer" class is physically indefensible.
Sub-leg resolution would require 9 points per sub-leg (only 3 per sub-leg here).
The F4_leg_class upcomer form is documented as a poor-quality average only.

### F3h Contribution
The F3h ratio ranges from 1.08 to 1.54 (8–54% above F1).  After removing F3h,
the residual (f4_residual column) is still 0.6–2.8×.  F3 is a minor correction
relative to the total excess — the bulk of the unexplained friction is the F4 target.

## Incomplete Lines of Investigation

- Ri extraction: requires running sample_segment_htc_uaprime.py on mainline
  continuations (OF13 env, libRCWallBC.so) → was out of scope for this task
- Sub-leg upcomer coefficients: would need more admitted data points (corrected
  Q perturbations not yet requalified); deferred
- Downcomer excess physical mechanism: unclear; not resolved here
- Wiring F4_leg_class into solver.py: not done; solver.py ScenarioConfig needs
  a `leg_class` mapping from segment_config; separate task

## Next Steps

1. Extract wall-bulk ΔT per leg: run sample_segment_htc_uaprime.py on Salt 2/3/4 Jin
   under OF13 env; derive ΔT = Q_wall / (HTC × A_wall) per span
2. Compute section-median Ri per leg (CRITICAL: use MEDIAN not mean — the mean is
   ~100× larger due to near-zero velocity cells; see CLAUDE.md gotcha #4)
3. Second fitting round: f/f_lam = f3h_ratio × (1 + C × Ri_streamwise^n) with
   streamwise projection cos(θ) for inclined legs
4. Wire F4_leg_class into solver.py (separate Implementer task)
5. Add corrected Q perturbation rows once formal gate issues requalified verdict
   (adds ~12 points for heater/cooler correlation at different Q levels)
