# Fused model-form comparison — mdot AND pressure-distribution, one view

Buoyancy-driven molten-salt loop, laminar, Re 61–135. CFD reference (coarse mesh, single
time, no GCI yet): mdot S2/S3/S4 = 0.01318 / 0.01497 / 0.01698 kg/s.

**Read this together with the honesty flag:** raw mdot agreement depends on the thermal
boundary (insulation) *more* than on the hydraulic closures — so the mdot column ranks
forms only *at a fixed boundary*, and the ΔP-distribution column is the boundary-robust
discriminator.

## A. All model forms — driving, closure, and both error metrics

| Form | Driving / closure | mdot error vs CFD | ΔP-distribution vs CFD | Verdict |
|---|---|---|---|---|
| **F0** zero-loss | buoyancy, no losses | ~+1400% (rails to cap) | n/a | diagnostic only — not predictive |
| **F1** major-only | friction, no minor | diverges / rails | n/a | fails as predictive form |
| **F2a** default, minor OFF | f mult=1.0, no K | +34.7% mean (ins 1.0in) | over-predicts low-loss legs | over-predicts |
| **F2b** default textbook K | k90=1.0, k20=0.10, mult=1.0 | +27.3% (1.0in) / +35.4% (1.4in) | single global mult → wrong distribution | current baseline; agreement may be fortuitous |
| **F3** CFD closures | de-buoyed f/f_lam + CFD K 6–16 | −17.6% (1.0in) / −14% (1.4in) | best distribution (per-leg by construction) | fixes ΔP, does NOT fix mdot |
| **F4** probe replay | CFD ΔP held FIXED | ~1.9% | matches (drive fixed) | sanity check, NOT a prediction |
| **F5** endpoint replay | schematic geometry | diverges | wrong (geometry bug) | cautionary; provenance bug, now fixed |
| **fit_major_k90_1p4** | fitted global mult=2.1, no K | **3.10%** (best, 1.4in) | still one global mult → distribution wrong | fitted surrogate, not validated closure |
| **fit_major_defaultK_1p4** | fitted mult=2.1 + default K | 3.15% | as above | fitted surrogate |
| **fit_k90_major1_1p4** | fitted k90=12.5, mult=1.0 | 4.86% | as above | fitted surrogate |
| **zero_minor_1p4** (ablation) | mult=1.0, no K | 44.5% (worst) | — | ablation lower bound |

## B. Friction model-form ladder — same closures, three ways of applying them
(ins=1.0in "hot" scenario vs CFD-matched insulation — the condition-dependence)

All three rows use K=0 (perleg trial config) for the hot column; default row at matched T
uses S.MinorLosses() defaults (textbook K), which differs from the global/per-leg rows (K=0)
— the matched-T default value is therefore slightly lower-magnitude than a K=0 comparison
would give, but the direction (positive→negative flip) is unaffected.

| Friction form | mdot err @ hot (ins 1.0in) | mdot err @ CFD-matched T (ins 0.25in) |
|---|---|---|
| default (mult=1.0) | +29.7 / +34.4 / +39.9% | −26.8% |
| global-mean multiplier (~1.9–2.1) | −4.6 / −3.3 / −3.1% | −45.7% |
| per-leg friction multiplier | −9.8 / −9.8 / −10.3% | −48.6% |

**Key:** the *same* per-leg friction flips from −10% (hot) to −49% (matched) → mdot is not a
robust closure metric. The per-leg form is nonetheless correct for the pressure
*distribution* by construction.

## C. Per-segment ΔP error — why one global multiplier is structurally inadequate (Salt 2)

CFD ΔP = friction_grad_corrected × L_interior (interior arc, stations s01–s03).
1D ΔP = CFD_ΔP × (mult_global / f_leg) — property-independent apples-to-apples.
Global mean mult = 1.857 (Salt 2), 2.092 (Salt 4).

| Leg | CFD ΔP [Pa] | 1D ΔP [Pa] | % err (S2) | % err (S4) |
|---|---|---|---|---|
| heater (lower) | 7.6 | 5.3 | −30% | −27% |
| downcomer (right) | 7.2 | 6.1 | −15% | −36% |
| cooler (upper) | 6.7 | 5.6 | −17% | −12% |
| test-section | 1.4 | 1.7 | +27% | +109% |
| upcomer-lo (left_lower) | 1.6 | 1.9 | +20% | −5% |
| upcomer-up (left_upper) | 1.2 | 2.1 | +79% | +155% |
| corner minor (each) | 0.4–0.76 | 3.5–5 | +363–790% (local-q_ref artifact) | |

Loss budget: friction ~93–95%, corner-minor ~5–7%.

**Note (2026-07-04 correction):** An earlier version of this table used the full fitting-to-fitting
span length (~0.71 m) instead of the interior arc length (~0.36 m) for the CFD ΔP calculation,
approximately doubling all CFD ΔP values and reporting spurious +49/+57/+68/+96/+182/+282% errors.
The corrected table shows the actual picture: the global multiplier UNDER-predicts high-f legs and
OVER-predicts low-f legs — the distribution is wrong in both directions.

## Headline verdicts (defensible, honest)
1. **Per-leg closure set delivered** and internally consistent (loop head 41–45 Pa closes).
2. **mdot is loss-sensitive** but no single closure set is "right"; a fitted global mult=2.1
   reaches ~3% only at an assumed 1.4in boundary — a surrogate, not validated physics.
3. **The single global friction multiplier is structurally inadequate** for the ΔP
   distribution; per-leg friction is the highest-value hydraulic model change.
4. **The thermal boundary dominates raw mdot** — match effective insulation to CFD before
   judging closures.
5. **Open factor-2 mdot gap** at matched T remains unexplained ("drive too weak" disproven).
6. **Minor (bend) losses ~5%**, upper-bounded; not the headline.

Sources: `2026-07-01_model_form_comparison/README.md`,
`2026-07-01_rom_model_form_fits_and_1p4_boundary/{model_form_summary,closure_fit_parameters}.csv`,
`2026-07-01_claude_1d_predictivity_trial/{predictivity_mdot_table,segment_dp_compare,perleg_vs_global_mdot}.csv`,
`2026-07-02_overnight/{matched_closure_compare,insulation_sweep_fine}.json`.
