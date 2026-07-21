# Coordinator/Implementer: Pressure-Drop Decomposition + Friction Closure Library

**Date:** 2026-07-04  
**Session type:** Architecture + implementation  
**Status:** Phase 1 complete; solver wired; comparison script operational

---

## 1. User request

> "Not everything that happens is due to friction factor. We need to correct your model so
> that it considers buoyancy, thermal development, hydraulic development, minor losses,
> major losses, etc separately. We can start slowly, but ultimately, that is the end goal.
> Also, we don't just want friction as a function of Re, we want friction in the function
> forms we had shown in the past from the lit review. We want to compare many friction forms."

---

## 2. Physics decomposition (LitRev ch04)

The LitRev defines three physically distinct loss terms:

```
ΔP_loss = Σ_i  f_D,fd,i(T) × (L_i/D_i) × ½ρv²    [F1: distributed friction]
         + Σ_j  K_j × ½ρv²_ref,j                   [F2: local K losses — MinorLosses]
         + Σ_k  ΔP_dev,k                             [F3: entry-length correction]
```

**Buoyancy is already a SEPARATE term in `buoyancy_pressure()` — correct as-is.**

---

## 3. Files created / changed

### New file: `friction_closures.py`

Location: `cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`

Contains:
- `SegmentDpBreakdown` dataclass: `dp_fd_Pa`, `dp_entry_Pa`, `dp_total_Pa`, `f_D_fd`, `f_D_apparent`, `Re`, `x_plus`, `closure_form`
- `dp_F1(Re, rho, v, L, D)` — 64/Re fully-developed
- `dp_F3_hagenbach(Re, rho, v, L, D, is_segment_entry)` — 64/Re + Hagenbach K_∞=1.33 at segment entry
- `dp_F3_hagenbach_always(...)` — forces entry correction at every segment
- `AVAILABLE_FORMS` registry, `compute_dp()` factory
- `summarise_forms_table()` for quick at-a-glance comparison

**Hagenbach physics:**
```
ΔP_entry = K_∞ × ½ρv²   (once per physical segment inlet, K_∞ = 1.33)
f_D_app  = f_D_fd + K_∞ × D/L
```
Validity: K_∞ is the asymptotic limit (x⁺ → ∞). For x⁺ < 0.05 (flow still developing),
the formula OVER-estimates — a warning is issued.

### Updated: `solver.py`

Changes:
1. Import: `from .friction_closures import AVAILABLE_FORMS as _FRICTION_FORMS, compute_dp as _compute_segment_dp`
2. New field on `ScenarioConfig`:
   ```python
   friction_form: str = "F1"  # "F1", "F3_hagenbach", "F3_hagenbach_always"
   ```
   Default = `"F1"` — fully backward-compatible.
3. `distributed_and_minor_losses()` now:
   - Reads `scenario.friction_form`
   - For each segment: `is_entry = abs(seg.parent_start_fraction) < 1e-6`
   - Calls `_compute_segment_dp(friction_form, Re, rho, v, L, D, is_entry)`
   - Reports `f_D_apparent × friction_mult` as `main_f`

### New file: `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py`

Comparison script. Loads:
- CFD f_corr from `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`
- Segment arc lengths from `work_products/2026-07-01_claude_segment_friction/segment_friction.csv`
- Salt 1 data from `work_products/2026-07-04_salt1_friction/` when available

Outputs: `friction_forms_comparison.csv`, console table.

---

## 4. Key findings

### 4.1 Hagenbach correction magnitude (F3h vs F1)

| Segment type | Re range | F3h/F1 enhancement | F3h explains of CFD excess |
|---|---|---|---|
| lower_leg (heater) | 45-123 | +5 to +16% | ~4-8% |
| right_leg (downcomer) | 38-118 | +5 to +15% | ~6-9% |
| left_lower_leg (upcomer) | 44-135 | +16 to +50% | ~42-79% |
| test_section_span | 45-124 | +20 to +54% | varies |
| upper_leg (cooler) | 41-115 | +5 to +15% | ~5-11% |

Key: the entry correction is most significant for SHORT segments.
- `left_lower_leg` (L=0.122m): **42-79% of excess explained by Hagenbach**
- `lower_leg` (L=0.357m): **only 4-8% explained**

### 4.2 Solver-level impact

F3_hagenbach vs F1 at `predictive_airside_ins_1.0in_rad_1`, `k_90deg=0.0`:

| Case | mdot_F1 | mdot_F3h | change |
|---|---|---|---|
| Salt 2 | 0.02126 | 0.01839 | -13.5% |
| Salt 3 | 0.02382 | 0.02003 | -15.9% |
| Salt 4 | 0.02697 | 0.02190 | -18.8% |

F3h reduces predicted mdot by 13-19% — moves in the right direction but insufficient to
close the factor-2 gap vs CFD (which would require ~50% reduction).

### 4.3 Residual enhancement NOT captured by F3h

The remaining gap (f_CFD / f_F3h) after accounting for Hagenbach:

| Leg | Residual gap |
|---|---|
| lower_leg (heated) | 2.4-2.5× |
| right_leg (downcomer) | 1.4-2.8× |
| left_lower_leg | 1.0-1.5× |
| upper_leg (cooled) | 2.0-2.1× |

**Physical mechanisms behind the residual gap (not yet modeled):**
1. **Buoyancy-modified velocity profile**: in heated/cooled vertical legs, buoyancy forces
   distort the velocity profile → f ≠ 64/Re. Richardson number correction needed.
2. **Upcomer recirculation**: CFD shows backflow fraction in the upcomer → momentum loss
   not captured by a forward-flow friction model.
3. **Secondary flows from 90° bends**: persist for O(D×Re) downstream → extra dissipation.
4. **Feature losses**: test section inlet/outlet, test section features.

---

## 5. FRIC-FIT-001 not implemented

The `correlation_registry.csv` admits `log(f_D) = 5.23 − 0.948 log(Re) + 2.92 I[test_section]`.

**Investigation revealed**: the `target_value` in `hydraulic_fit_ready_rows.csv` is computed
as `pressure_loss_hydro × 2D / (q_dyn × L)` — NOT the standard Darcy friction factor
normalized per unit L/D. The training values reach ~46 for the test section at Re≈97, which
is physically implausible as a standard f_D. The normalization convention differs from
the `segment_friction.csv` pipeline (which gives f_D in range 0-3).

**Consequence**: FRIC-FIT-001 cannot be implemented in `friction_closures.py` without
first resolving the normalization. A placeholder note is in the module docstring.

---

## 6. Closure hierarchy roadmap

| Level | Name | Status | What it captures |
|---|---|---|---|
| F1 | 64/Re local-T | **Implemented** | fully-developed laminar baseline |
| F2 | F1 + K_j | **Existing** (MinorLosses) | contraction/expansion/bend K values |
| F3 | Hagenbach | **Implemented** | entry-length momentum redistribution |
| F4 | Buoyancy-modified | **Pending** | f × Ri correction for heated/cooled verticals |
| F5 | Per-leg CFD | **Existing** (friction_multiplier_by_parent_segment) | CFD-calibrated per-leg ratio |
| F6 | Full Shah composite | **Pending** | full x⁺ entry function, more accurate for x⁺ < 0.05 |

---

## 7. Limitations / open items

1. **Hagenbach assumes flat inlet profile**: in practice, flow enters each segment through a
   bend or fitting — not a reservoir. The actual entry correction may differ from K_∞ = 1.33.
2. **`is_segment_entry` applies to ALL segments**: in the current solver, every physical
   segment is at parent_start_fraction=0 (un-refined geometry default), so the Hagenbach
   correction fires at every segment. With geometry refinement, only the first subsegment
   gets it — correct behavior.
3. **F3h over-predicts for left_upper_leg and test_section at high Re (S3/S4)**: these
   segments show f_CFD/f_lam < F3h/f_lam, suggesting the actual entry behavior differs
   from the flat-inlet assumption.
4. **Buoyancy-modified f**: the large residual gap in the heater/cooler/downcomer (~2-3×
   after F3h) is dominated by density-driven velocity profile changes. A Richardson-number
   correction (e.g., Aicher & Martin 1997 for laminar flow) would be the next F4 closure.
