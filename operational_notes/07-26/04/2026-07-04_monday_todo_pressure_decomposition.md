# Monday TODO — Pressure-Drop Decomposition Roadmap

Written: `2026-07-04`
Author: claude (AGENT-179)
Context: user asked to decompose the 1D model pressure drop into physically distinct
terms (buoyancy, entry-length, minor losses, buoyancy-modified friction, thermal entry,
upcomer recirculation) and compare many friction correlation forms.

---

## 1. Full decomposition status

The physics decomposition the user asked for maps to these terms in `solver.py`:

| Component | Status | Location in solver |
|---|---|---|
| Buoyancy driving term | ✅ Correct and separate | `buoyancy_pressure()` |
| Distributed friction (F1: 64/Re local-T) | ✅ Wired | `friction_closures.py` → `distributed_and_minor_losses()` |
| Local K losses (F2) | ✅ Implemented | `MinorLosses` dataclass; bend K from T7 CFD |
| Entry-length correction (F3: Hagenbach) | ✅ Implemented | `friction_closures.py` → `dp_F3_hagenbach` |
| Buoyancy-modified friction (F4) | ❌ **Not yet — dominant missing term** | Placeholder |
| Thermal entry length (developing Nu) | ❌ Not yet | Nu is constant per leg |
| Upcomer recirculation correction | ❌ Not yet | Treated as forward flow |
| Full Shah x⁺ composite (F6) | ❌ Placeholder | Supersedes Hagenbach for x⁺ < 0.05 |

**Buoyancy is already a SEPARATE term in `buoyancy_pressure()`.** Do NOT add a
buoyancy force to the friction loop — it is already handled correctly.

**The largest single gap is F4: buoyancy-modified friction.** This is the 2–3× residual
f/f_lam in the heater (lower_leg), cooler (upper_leg), and downcomer (right_leg) that
remains after accounting for both fully-developed laminar friction and the Hagenbach
entry correction.

---

## 2. What F4 is and why it is dominant

In natural-circulation loops, the heated and cooled vertical legs have a strong
transverse density gradient across the pipe cross-section (hot center, cooler wall
in the heater; hot wall, cooler center in the cooler). This distorts the velocity
profile away from the Poiseuille parabola:

- In the **heater** (lower_leg, ~21° inclined): buoyancy enhances near-wall upflow,
  flattening the profile → higher wall shear → f > 64/Re.
- In the **cooler** (upper_leg, ~22° inclined): buoyancy retards near-wall downflow
  → same effect.
- In the **downcomer** (right_leg, vertical): weaker but present.

The governing parameter is the Richardson number: `Ri = Gr/Re²`.

For laminar mixed convection in vertical pipes, the literature provides:

### F4 candidate correlations

**Option A — Aicher & Martin (1997) laminar correction:**

```
f × Re = 64 × [1 + C × Ri^n × (D/L)]
```

where C and n are fitted from experimental/DNS data (typical range: C ~ 0.03–0.1,
n ~ 0.5–1.0 for laminar). Ri here is the streamwise Richardson number.

**Option B — Jackson & Hall general form (mixed convection):**

```
f/f_fd = F(Ri, Pr)
```

Various forms exist; most converge to `f/f_fd ~ 1 + C(Pr) × Ri^0.5` for laminar.

**Option C — Simple power law fit to CFD data:**

```
f/f_lam = a × Ri^b    (fit to momentum_budget.json per-leg data)
```

This is the most honest approach given that we have CFD data. Use S2/S3/S4 to
constrain a and b per segment type (heater, cooler, downcomer), then extrapolate
to the F4 form.

### Recommended Monday approach

1. **Plot Ri vs f/f_lam** for each leg across S2/S3/S4 using the momentum budget data.
   The momentum budget already has both `f_corrected` and `Re`. Need `Ri` per span —
   available from the CFD dimensionless fields (or compute from T extraction).
2. **Fit power-law** per leg type (heater, cooler, downcomer) with CFD data.
3. **Implement in `friction_closures.py`** as `dp_F4_buoyancy(Re, Ri, rho, v, L, D, is_entry)`.
4. **Wire into solver** via `friction_form = "F4_buoyancy"` and expose `Ri` from the
   thermal state (compute from `Gr/Re²` using local `rho`, `d_rho_dT`, `T_wall - T_bulk`,
   `D`, `mu`).

---

## 3. Monday task list (prioritized)

### Immediate (check running jobs first)

- [ ] **Check job 3275448–3451** (corrected Salt Q perturbations):
  ```bash
  squeue -u andresfierro231
  # or if done:
  sacct -u andresfierro231 --format=JobID,JobName%24,State,ExitCode,Elapsed --starttime=2026-07-04
  ```
  For each finished job: verify `preflight_patch_audit_<job>.csv` exists, then check
  mdot monitor — did it move from nominal by ~Q^(1/3)? Run operating-point gate.

- [ ] **Check job 3275531** (gap analysis + insulation sweep):
  ```bash
  cat work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.out
  ls work_products/2026-07-04_jin_perleg_gap_analysis/
  ```
  Review insulation sensitivity vs per-leg friction gap. Use to calibrate F4.

### 1D model — next closures

- [ ] **F4: Buoyancy-modified friction** (highest priority new term)
  - Extract `Ri` per leg per case from CFD (use `momentum_budget.json` Re + compute
    Gr from T extraction data, or use the `dimensionlessFields` foam function output).
  - Plot f/f_lam vs Ri per leg type.
  - Fit power law per leg type from S2/S3/S4 data.
  - Implement `dp_F4_buoyancy(Re, Ri, ...)` in `friction_closures.py`.
  - Wire Ri computation into `distributed_and_minor_losses()` via the thermal state.

- [ ] **More laminar friction correlation forms from LitRev ch04**
  - Confirm with user which forms from the LitRev are desired.
  - Candidates: Shah-Baehr-Stephan composite, Churchill-Usagi, per-leg CFD lookup.
  - All go into `friction_closures.py` as new `dp_F*` functions in `AVAILABLE_FORMS`.

- [ ] **Thermal entry length (Nu developing)** — lower priority
  - Current model: constant Nu per leg from CFD.
  - Future: Graetz-Lévêque or Shah (1978) thermal entry form.
  - Gating question: is the developing-Nu effect large compared to F4? Check Gz number
    for each leg (Gz = Re × Pr × D/L). If Gz >> 1, thermal entry is significant.

- [ ] **Upcomer recirculation correction** — blocked on T2/T13
  - Cannot model without more (Re, Ri) data points.
  - Current approach: treat upcomer as forward flow, accept the residual error.
  - Unblocks when T2 perturbation runs requalify AND/OR T13 onset/limit CFD runs.

### Documentation / lit review integration

- [ ] Confirm user's desired friction form list from LitRev — then add all named
  forms to `friction_closures.py` in one batch.
- [ ] Add `FRIC-FIT-001` normalization resolution to the queue: before that
  correlation can be used, the `target_value` normalization in
  `hydraulic_fit_ready_rows.csv` needs to be traced to a physical definition and
  converted to standard Darcy f_D. See journal entry for details.

### Code quality (carried forward from 2026-07-04 EOD)

- [x] **`test_friction_closures.py` written and passing** (42/42, 2026-07-04):
  `cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`
  Covers F1/F3h/F3h-always, factory dispatch, SegmentDpBreakdown immutability,
  physics ordering, helpers, and summarise_forms_table smoke.

- [ ] **Wire comparison script to use `compute_dp` from `friction_closures.py`**
  instead of its inline Hagenbach re-implementation. Currently
  `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py` has a
  standalone `hagenbach_f_ratio()` that duplicates the physics. If F3h ever
  changes in `friction_closures.py`, the comparison table will silently diverge.
  Fix: import `compute_dp` and read `f_D_apparent / f_D_fd` from the breakdown.

- [ ] **Commit both repos** — `cfd-modeling-tools` has uncommitted changes:
  `friction_closures.py` (untracked), `solver.py` (modified),
  `test_friction_closures.py` (new). `ethan_runs` has uncommitted `CLAUDE.md`,
  BOARD.md, journal files, and operational notes from this session.

---

## 4. Friction closure hierarchy summary (F0–F6)

| ID | Name | File | Status | What it captures |
|---|---|---|---|---|
| F0 | 64/Re constant | (retired) | Superseded | Isothermal, constant properties |
| F1 | 64/Re local-T | `friction_closures.py` | ✅ Production default | Fully-developed laminar with local-T properties |
| F2 | F1 + K_j | `solver.py` MinorLosses | ✅ Existing | Bends, contractions — need K renormalization |
| F3 | Hagenbach entry | `friction_closures.py` | ✅ Implemented | Entry-length momentum redistribution |
| F4 | Buoyancy-modified | `friction_closures.py` | ❌ **Next** | Ri correction for heated/cooled verticals |
| F5 | Per-leg CFD | `solver.py` `friction_multiplier_by_parent_segment` | ✅ Existing | CFD-calibrated per-leg ratio |
| F6 | Full Shah composite | `friction_closures.py` | ❌ Placeholder | Full x⁺ entry function (better than Hagenbach for x⁺ < 0.05) |

**Wire order for comparison runs:**
- Baseline: `friction_form = "F1"` (current default, backward-compatible)
- Entry correction: `friction_form = "F3_hagenbach"` (-13 to -19% mdot vs F1)
- When F4 ready: `friction_form = "F4_buoyancy"` (expected further reduction)
- When F5 needed: keep `friction_multiplier_by_parent_segment` on ScenarioConfig

---

## 5. Key quantitative reference points

From `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`:

| Leg | Re range (S2–S4) | f_CFD/f_lam | F3h explains | Residual gap |
|---|---|---|---|---|
| lower_leg (heater, 21°) | 45–123 | ~3.0–3.5 | ~4–8% | **2.4–2.5×** |
| right_leg (downcomer, vertical) | 38–118 | ~2.0–3.5 | ~6–9% | **1.4–2.8×** |
| left_lower_leg (upcomer, vertical) | 44–135 | ~2.0–3.0 | ~42–79% | 1.0–1.5× |
| upper_leg (cooler, 22°) | 41–115 | ~2.5–3.0 | ~5–11% | **2.0–2.1×** |

The upcomer residual is small after F3h (the short segment length explains most of
the excess). The heater/cooler/downcomer residual is the F4 target.

Solver-level mdot impact (F3h vs F1, no K correction):
- Salt 2: -13.5% (0.02126 → 0.01839 kg/s)
- Salt 3: -15.9% (0.02382 → 0.02003 kg/s)
- Salt 4: -18.8% (0.02697 → 0.02190 kg/s)

The CFD mdot is lower still — closing this gap requires F4.
