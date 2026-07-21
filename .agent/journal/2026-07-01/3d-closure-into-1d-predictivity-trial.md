# 3D-Closure-into-1D Predictivity Trial (AGENT-168, 2026-07-01)

**Goal.** Inject THIS SESSION's mesh-corrected CFD closures into the
`tamu_loop_model_v2` 1D loop solver and quantify how well the 1D model predicts
(a) loop mdot and (b) per-segment pressure drops, versus CFD, compared against
the model's default closures and two loss ablations. Paper/presentation grade.

Confidence boundaries are stated throughout (per user memory: disclose
assumptions, validity windows, limitations; every decision carries an explicit
"why").

---

## 1. Inputs (loaded, not hand-copied)

This session's CFD closures (Salt 2/3/4 Jin, mesh-built centerlines, OF13
continuation reconstructions):

- **Per-corner minor-loss K (T7):**
  `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.json`.
  K = |ΔP0|/q_ref across each corner's two interface patches.

  | corner | S2 K | S3 K | S4 K |
  |---|---|---|---|
  | lower_left  | 8.21 | 8.30 | 8.29 |
  | lower_right | 16.50| 13.81| 10.73|
  | upper_right | 15.92| 14.33| 13.58|
  | upper_left  | 6.25 | 6.22 | 6.68 |
  | **mean**    | 11.72| 10.67| 9.82 |

- **Per-leg de-buoyed friction f/f_lam (T1b):**
  `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`.
  f_corrected_over_flam (f relative to laminar 64/Re):

  | leg | S2 | S3 | S4 |
  |---|---|---|---|
  | lower_leg (heater)      | 2.67 | 2.72 | 2.88 |
  | right_leg (downcomer)   | 2.19 | 2.72 | 3.26 |
  | left_lower_leg          | 1.55 | 1.79 | 2.21 |
  | test_section_span       | 1.46 | 1.19 | 1.00 |
  | left_upper_leg          | 1.04 | 0.91 | 0.82 |
  | upper_leg (cooler)      | 2.23 | 2.30 | 2.38 |
  | **mean**                | 1.86 | 1.94 | 2.09 |

- **CFD per-segment ΔP / mdot:**
  `work_products/2026-07-01_claude_section_mean_pressure/*.json` (station p_rgh,
  monitor mdot). CFD |mdot| targets (continuation, high trust):
  S2 = 0.013184, S3 = 0.014967, S4 = 0.016985 kg/s.
  Salt 1: **no** continuation extraction and **no** closures this session; the
  only CFD mdot is an early-window terminated / convergence_audit_required value
  (0.011265 kg/s) from `reports/.../2026-06-29_ethan_salt_pressure_drop_predictivity`
  — used ONLY as a low-trust reference, never for a closure claim.

- **T8 geometry note honored:** heater/downcomer labels were swapped + lengths
  ~1.3x inflated in the schematic (now fixed). The 1D model's `geometry.py`
  already encodes the mesh-true orientation: heater = `heated_incline` (~+20°
  incline, 36 in), cooler = `cooled_incline_*` (~-20°), downcomer =
  `right_vertical` (vertical, 36 in), test-section legs vertical. Leg lengths fed
  to the ΔP comparison are the MESH station-to-station lengths (from the section
  JSON x/y/z), and the 1D friction uses the model's own mesh-consistent segment
  lengths.

---

## 2. How the 1D model applies closures (read from solver.py)

`distributed_and_minor_losses()` (solver.py ~L1609):
- Major loss: per segment `f = friction_factor(Re) * friction_multiplier`, then
  `dp = f*(L/D)*½ρv²`, summed, and the whole sum scaled by
  `minor_losses.major_loss_multiplier`. `friction_factor(Re)=64/Re` for Re<2300
  (solver.py L381) — i.e. the multiplier is exactly an f/f_lam scale, matching the
  CFD T1b definition.
- Minor loss: `total_fixed_k() = n_90deg*k_90deg + n_20deg*k_20deg` applied on ONE
  main-line dynamic head `q_ref = ½ρ_ref·v_main²` (v_main = mdot/(ρA) at D=0.87 in).
- Optional test-section sudden contraction/expansion K if
  `include_test_section_diameter_change`.

**Key modeling limitation exposed by this structure:** the model has ONE global
friction multiplier and ONE lumped bend-K on ONE q_ref. CFD gives PER-LEG
friction and PER-CORNER K on LOCAL q_ref. The mapping below is the best possible
projection onto that reduced form.

## 3. Closure mapping (the "why")

- **Bend K → n_90deg:** the 4 CFD corners ARE the loop's 4 turns. Set
  `k_90deg = mean(4 CFD corner K)`, `n_90deg=4`, `k_20deg=0`, `n_20deg=4` so that
  `total_fixed_k = 4·k_90deg ≈ Σ(4 CFD corner K)`. Justification: velocity is
  ~uniform around the loop (near-constant bore), so a single q_ref is defensible;
  the incline "20-deg" transitions are not separate CFD features, they are folded
  into the corner turns, hence k_20deg=0.
- **Friction → major_loss_multiplier:** simple mean of the 6 CFD leg f/f_lam. A
  flow/length-weighted mean was considered but the legs carry the same mdot and
  similar length, so the simple mean is within a few % and is the transparent
  choice. Documented limitation: a single scalar CANNOT reproduce the leg-by-leg
  spread (0.8–3.3).

New tracked config (Fluid repo, additive, non-breaking):
`minor_loss_preset: ethan_cfd_2026_07_01` (k_90deg=10.7 [3-case avg],
major_loss_multiplier=1.96, k_20deg=0, test-section-diam off) and campaign
`ethan_cfd_closures_salt_2026_07_01`. All 13 campaign plans still load.

## 4. Run method / commands

The full `run_resumable --campaign baseline` matrix is slow locally (each
`solve_case` root-finds mdot + marches temperatures). For a CONTROLLED trial I
drove the physics core directly, holding the scenario fixed
(`predictive_airside_ins_1.0in_rad_1`) and varying ONLY the `MinorLosses` object:

```
cd .../tamu_first_order_model/Fluid   # on PYTHONPATH
python3 work_products/2026-07-01_claude_1d_predictivity_trial/run_predictivity_trial.py
python3 work_products/2026-07-01_claude_1d_predictivity_trial/run_segment_dp_compare.py
python3 work_products/2026-07-01_claude_1d_predictivity_trial/make_figures.py
```

The scenario choice (1 in insulation, radiation on) is a fixed, realistic
middle-of-road setting; it shifts all closure sets together so the
closure-vs-closure comparison is unaffected. Absolute mdot depends on it (a
caveat).

## 5. Results

### 5a. mdot predictivity (|mdot| kg/s; % error vs CFD)

| case | CFD | default | zero-minor | zero-maj-zero-min | CFD-closures |
|---|---|---|---|---|---|
| S1* | 0.011265* | 0.013714 (+21.7%) | 0.014072 (+24.9%) | 0.200 (rail) | n/a |
| S2  | 0.013184 | 0.016457 (+24.8%) | 0.017106 (+29.7%) | 0.200 (rail) | 0.010992 (-16.6%) |
| S3  | 0.014967 | 0.019059 (+27.3%) | 0.020109 (+34.4%) | 0.200 (rail) | 0.012375 (-17.3%) |
| S4  | 0.016985 | 0.022068 (+29.9%) | 0.023757 (+39.9%) | 0.200 (rail) | 0.013750 (-19.0%) |

\* Salt 1 CFD value is low-trust (early-window terminated); no CFD closures.
Figure: `fig1_mdot_predictivity.png`.

Observations:
- **mdot is loss-sensitive, not purely buoyancy-dominated.** Going default →
  CFD-closures raises total loss and drops mdot by ~33% (from +25% to -17%).
- **zero-minor is worse than default** — removing minor losses raises mdot
  further from CFD. So the model NEEDS some minor loss.
- **zero-major-zero-minor rails at the mdot search ceiling (0.2 kg/s)** — with no
  friction the buoyancy head cannot be balanced; the ablation is a pure sanity
  bound, not a physical case.
- **CFD-closures under-predict by ~17-19%, default over-predicts by ~25-30%.**
  The true answer sits between; the CFD closures roughly halve the |error| but
  flip its sign.

### 5b. Per-segment ΔP (Salt 2 & 4, evaluated AT the CFD mdot)

To isolate closure FORM from operating point, the 1D loss terms are evaluated at
the CFD mdot (the model's self-consistent mdot differs; a raw comparison would
confound the two). Figures `fig2_segment_dp.png`, `fig3_minor_loss_budget.png`.

CFD loss budget: **friction ≈ 95%, corner-minor ≈ 4-5%** (S2: 51.2 / 2.3 Pa;
S4: 57.8 / 3.3 Pa).

Per-leg friction ΔP, 1D (global mult) vs CFD:
- Heated/downcomer/cooler legs (high CFD f/f_lam ~2.2-3.3): 1D within +4 to +68%.
- Low-loss legs (test-section, left-upper; CFD f/f_lam ~0.8-1.0): 1D over-predicts
  +96 to +400% because the single global multiplier (~2) is far too high there.
- **A single global major_loss_multiplier structurally cannot reproduce the CFD
  leg-by-leg friction distribution.**

Per-corner minor ΔP: injected CFD K give 3.5-5 Pa/corner in the 1D model, but the
actual CFD corner ΔP is 0.4-0.9 Pa (~5-8x over). Root cause (verified): the CFD
corner K were normalized on a very low LOCAL fitting-interface dynamic head
(u≈0.008 m/s, q≈0.06 Pa; the interface patches span a larger cross-section than
the pipe bore), whereas the 1D model applies K on the pipe bulk q_ref (v≈0.018
m/s, q≈0.30 Pa). Same mdot, ~2.2x velocity → ~5x q → ~5x inflated minor ΔP. So the
large CFD K (6-16) are an artifact of the local normalization and must NOT be
injected as-is.

## 6. Verdict (quantitative, honest)

1. **Does injecting the CFD closures improve mdot predictivity?** No, not net. It
   changes the error from +25-30% (default, over) to -17-19% (CFD, under) —
   similar magnitude, opposite sign. It does NOT reduce |error| enough to call it
   an improvement, and it flips the bias.
2. **Is mdot buoyancy-dominated / loss-insensitive?** No. mdot responds strongly
   to losses here (~33% swing). BUT the residual ~±20% after best-effort closure
   injection is dominated by the buoyancy/ΔT driver, not hydraulics: the model
   runs at Re 2-3x the CFD Re at matched loss level, i.e. its thermal solution
   produces a larger effective buoyancy head. The pressure DISTRIBUTION
   absolutely needs the closures (per-leg friction differs 4x across legs); the
   mdot MAGNITUDE needs the closures AND a corrected buoyancy/ΔT.
3. **Which CFD closure is trustworthy?** The per-leg friction multiplier (physical,
   ~95% of the budget). The bend-K should be treated as an UPPER BOUND only,
   because of the local-q_ref normalization; corner losses are only ~4-5% of the
   CFD budget so this does not dominate mdot anyway.
4. **Highest-value model change:** move the model from a single global
   major_loss_multiplier to a PER-LEG friction multiplier (the T1b table maps
   directly onto the 6 model legs). That is the change that would let the 1D ΔP
   distribution match CFD. Second: renormalize the CFD bend-K onto the pipe bulk
   q_ref before injection (or drop them, given the ~5% budget share).

## 7. Caveats / confidence boundaries

- **Coarse mesh** (nCells ≈ 2.17M, single level; T6 could not do GCI — no mesh
  generator in-repo). All CFD closures inherit unquantified discretization error.
- **Laminar K at very low Re** (Re ≈ 60-135): minor-loss K are not Re-independent
  in this regime; the reported K are effective values at these operating points.
- **mdot↔ΔT coupling:** the 1D model self-consistently solves mdot and the thermal
  field; the ~±20% residual is entangled with the buoyancy driver, not purely
  hydraulic. The per-segment ΔP comparison sidesteps this by forcing the CFD mdot.
- **Scenario fixed** at 1 in insulation / radiation on; absolute mdot depends on it
  (closure-vs-closure comparison does not).
- **Salt 1** excluded from closure claims (no S1 closures/continuation this
  session); its CFD mdot reference is low-trust early-window.
- **Single-q_ref minor-loss lumping** and **single global friction multiplier** are
  model-form limitations, not fit failures — documented in §5b and §6.

## 8. Artifacts

`work_products/2026-07-01_claude_1d_predictivity_trial/`:
- `run_predictivity_trial.py`, `run_segment_dp_compare.py`, `make_figures.py`
- `predictivity_mdot_table.{csv,json}`, `segment_dp_compare.{csv,json}`
- `fig1_mdot_predictivity.png`, `fig2_segment_dp.png`, `fig3_minor_loss_budget.png`

Fluid repo config (additive): `configs/campaigns.yaml` preset
`ethan_cfd_2026_07_01` + campaign `ethan_cfd_closures_salt_2026_07_01`.

Tests: `test_geometry_refinement.py` + `test_launch_predictive_closure_study.py`
pass (4); all 13 campaign plans load. Full solver suite is slow (not run to end).
