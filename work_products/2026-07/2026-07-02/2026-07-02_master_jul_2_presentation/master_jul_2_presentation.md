# Master presentation — July 2, 2026

**Theme (closure-deliverable-first):** *This session we delivered a self-consistent,
mesh-corrected per-leg hydraulic + thermal closure set for the Salt Jin family — the
inputs a 1D loop model needs — and then rigorously tested how far those closures carry
a 1D model, comparing every model form against CFD. We are explicit about what is not
yet trustworthy.*

Audience values transparency, rigor, honesty. Every quantitative slide cites its source
artifact. The "what we don't trust" slide is a feature.

**Consolidates:** ChatGPT/codex ROM-fit + readiness packages and Claude closure +
predictivity figures into one deck. Duplicate figures de-conflicted (see manifest).

---

## ⚠️ One honesty flag to resolve before you present
Two packages disagree on **what insulation setting matches CFD**:
- **codex ROM fit** assumed CFD ⇔ **1.4 in** insulation → best fit form = 3.10% mdot error.
- **Claude overnight thermal matching** found CFD 450 K ⇔ **~0.27 in** effective insulation.

These are not reconciled. **Recommendation:** present the *matched-temperature* result as
the physics story (thermal boundary dominates; §slide 7–8) and cite the codex fit as
"a global multiplier of ~2.1 fits mdot to ~3% *if* you accept the 1.4 in boundary" —
i.e. a fitted surrogate, not a validated closure. Do not present 3.10% as "the model works."

---

# SLIDE WALKTHROUGH (12 slides)

## 1 — Title / status
**Bullets**
- Buoyancy-driven molten-salt natural-circulation loop; 1D reduced-order model program.
- Delivered: self-consistent per-leg **hydraulic + thermal closure set**, Salt 2/3/4 Jin, on **mesh-corrected geometry**.
- In progress: mesh-independence bound and true-steady insulation runs.

**Speaker notes:** Frame the week as *closures delivered + honestly tested*. Set expectation that the last slides are limitations — deliberately.

**Figure/Table:** none.

---

## 2 — The deliverable: per-leg closure set  ⭐ LEAD RESULT
**Bullets**
- Per leg, the 1D model needs: friction `f/f_lam`, minor-loss `K`, wall `HTC`/`Nu`, recirculation.
- Delivered for all six legs, Salt 2/3/4 — see table.

**Table (USE):** `closure_summary_table.md` (render as slide table)
- f/f_lam 1.0–3.3; HTC heater 252/269/288, upcomer 77/102/126, downcomer 43/44/44 W/m²K; Nu upcomer 3.1/4.1/5.0.

**Speaker notes:** This is the headline deliverable. Everything after either backs it up (trust) or tests it (predictivity).

---

## 3 — Friction per leg  [FIG]
**Bullets**
- De-buoyed per-leg friction `f/f_lam ≈ 1.0–3.3`; every leg physical, across Re 61–135.
- Computed from a streamwise momentum budget that separates buoyancy from friction.
- f/f_lam is **Re-dependent** (4/6 legs rise with Re) — the model needs f(Re), not a constant.

**Figure (USE):** `2026-07-01_claude_checkpoint_presentation/fig1_friction_per_leg.png`

**Speaker notes:** heater 2.67→2.88, downcomer 2.19→3.26 (rises with Re); test-sec/upcomer-up near laminar (0.8–1.5).

---

## 4 — Minor-loss K + thermal + recirculation  [FIG panel]
**Bullets**
- Corner K ≈ 6–16, Re-dependent (K≈C/Re+K∞) → needs K(Re), not textbook high-Re constants.
- Wall HTC: heater 250–290, upcomer 77–126, downcomer ~43 (passive). Nu upcomer 3.1–5.0, downcomer ~1.74.
- Recirculation is **exclusive to the upcomer** (backflow 19–34%); heater/downcomer/cooler = 0 → downcomer modeled as an ordinary f(Re)+Nu leg.

**Figures (USE):** `fig3_corner_K.png`, `fig4_thermal_htc.png`, `fig6_recirculation.png` (checkpoint dir)

**Speaker notes:** HTC/Nu are patch-based, length-free → most robust numbers in the set. Corner K carry a normalization caveat (see slide 11).

---

## 5 — The model forms compared (F0–F5)  [TABLE]
**Bullets**
- F0 zero-loss · F1 major-only · F2 default textbook K · F3 CFD closures · F4 probe replay · F5 endpoint replay.
- Differ in driving, friction, minor loss, geometry, solve type.

**Table (USE):** §1 table of `2026-07-01_model_form_comparison/README.md` (or the FUSED table — slide 5b below)

**Speaker notes:** F0/F1 diagnostic; F2 current baseline; F3 the CFD-closure test; F4/F5 local replays (drive held fixed).

---

## 6 — Model-form mdot error vs CFD  ⭐ COMPARISON CORE  [FIG + TABLE]
**Bullets**
- Zero-loss rails (+1400%); default over-predicts +25–35%; CFD closures under-predict −17%.
- A fitted single global multiplier (~2.1) reaches ~3% *at the 1.4 in boundary* — a surrogate fit, not validated physics.
- **mdot is loss-sensitive, not purely buoyancy-dominated** — but no single closure set is "right."

**Figure (USE):** `2026-07-01_rom_model_form_fits_and_1p4_boundary/figures/model_form_mdot_error_bar.png`
**Table (USE):** FUSED model-form table (slide artifact #1) — combines mdot error (§2a) + fit ranking.

**Speaker notes:** This is the "compare the model forms" money slide. Pair with the fused table so both mdot and ΔP metrics are visible together.

---

## 7 — Per-segment ΔP: a single global multiplier is structurally inadequate  ⭐  [FIG + TABLE]
**Bullets**
- CFD friction varies per leg; one global multiplier (mean f/f_lam = 1.86) mis-predicts the distribution in BOTH directions: under-predicts heavy legs (heater −30%, downcomer −15%) and over-predicts light legs (upcomer-up +79%).
- At Salt 4 the spread widens: downcomer −36%, upcomer-up +155%.
- Minor (bend) loss is only ~5% of the budget — friction-dominated (~93–95%).
- Highest-value model change: **per-leg friction multiplier** (maps the T1b f/f_lam onto the 6 legs).

**Figures (USE):** `2026-07-01_claude_1d_predictivity_trial/fig2_segment_dp.png`, `fig3_minor_loss_budget.png`
**Table (USE):** §C table (segment ΔP % error) of `fused_model_form_comparison.md`.

**Speaker notes:** ΔP comparison uses interior arc length (s01–s03 stations) for both CFD and 1D — the property-independent apples-to-apples basis. The global multiplier gets the total right (it's the mean by construction) but the distribution is wrong. Per-leg friction fixes the pressure *distribution* by construction — this is a real win independent of thermal state. (An earlier draft reported one-sided over-prediction up to +282%; that was an error from using 2× the correct arc length for CFD ΔP.)

---

## 8 — The thermal boundary is the dominant lever  ⭐ OVERNIGHT KEY FINDING  [FIG]
**Bullets**- 1D loop T is extremely insulation-sensitive: ~375→512→542 K over 0→1→2 in (rad=1 scenario; see figA).
- CFD's 450 K ⇔ ~0.27 in effective insulation. The earlier "+27% over-prediction" was largely a **thermal-BC artifact**, not a closure result.
- Lesson: match the thermal boundary to CFD before judging closures.

**Figure (USE):** `figA_insulation_sensitivity.png` (checkpoint or overnight — byte-identical)

**Speaker notes:** This reframes all raw mdot-agreement claims. The insulation setting swamps the closure choice. Values cited are the rad=1 series (matching the main scenario); the figA plot uses this same rad=1 data. At rad=0 the range is 422→544→548 K — directionally the same but the rad=1 series is the operationally relevant comparison.

---

## 9 — Closure benefit is condition-dependent  [FIG]
**Bullets**
- At the hot setting, adding friction "helps" mdot; at CFD-matched T it **hurts** (default −27% → per-leg −49%).
- ⇒ **mdot is NOT a robust closure-quality metric.** The robust metric is the per-segment pressure *distribution*.

**Figure (USE):** `figB_condition_dependent_closure.png` + `fig4_perleg_vs_global_mdot.png`

**Speaker notes:** Per-leg −9.8% at hot vs −48.6% at matched — same closures, opposite verdict. That's the whole point.

---

## 10 — How we know the geometry is right (why trust the closures)  [FIG]
**Bullets**
- Rebuilt leg geometry from mesh PCA after catching a schematic-CSV bug: heater cut vertical (really 21.5°), lower↔downcomer label swap (0.566 m), test-section bore 20.9 vs 22.1 mm.
- Now fixed — supports every number in slides 2–4.

**Figure (USE):** `fig5_geometry_swap.png` + optionally `fig2_loop_budget.png` (loop energy closure 41–45 Pa).

**Speaker notes:** Rigor backing. A "we found and fixed a bug" slide builds credibility.

---

## 11 — What we DON'T trust yet + the open factor-2 gap  ⭐ HONESTY  [FIG]
**Bullets**
- **No mesh-independence bound yet.** refineMesh r=2 works geometrically (2.17M→17.3M) but the refined non-conformal interface breaks the OF13 stitcher → **NO GCI produced (not fabricated)**; fix = conformal-first remesh.
- Perturbation runs are false-steady (audited & rejected); coarse mesh; single time; laminar.
- Corner K referenced to a local dynamic head over-weight minor loss ~5–8× → treat as **upper bound**.
- **Open factor-2 mdot gap:** at matched T with CFD per-leg friction, 1D predicts ~half CFD mdot (0.0068 vs 0.0132). "Drive too weak" was checked and **disproven** (ΔT matches). No validated mechanism yet.

**Figure (USE):** `boundary_sensitivity_mdot_error.png` (rom fits dir).

**Speaker notes:** Lead here if asked "is this final?" — it isn't. This slide is the integrity of the whole talk.

---

## 12 — Asks & next steps
**Bullets**
- Mesh-independence bound via self-generated conformal-first mesh (removes the #1 trust limiter, no external dependency).
- True-steady insulation runs (T2) to enable the upcomer onset correlation — currently too slow (~22 s sim/hr); needs sbatch + revised endTime.
- Ranked model improvements: (1) match thermal BC / effective insulation to CFD; (2) reconcile the loop momentum budget term-by-term (explain the factor-2); (3) per-leg friction multiplier (fixes ΔP distribution).

**Speaker notes:** Optional ask — whether an independent finer mesh can be sourced to strengthen GCI to 3 levels.

---

# FIGURE / TABLE MANIFEST (exact paths)

Base: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs/`

| Slide | Artifact | Path | Status |
|---|---|---|---|
| 2 | closure table | `work_products/2026-07-01_claude_checkpoint_presentation/closure_summary_table.md` | USE |
| 3 | fig1 friction | `work_products/2026-07-01_claude_checkpoint_presentation/fig1_friction_per_leg.png` | USE |
| 4 | fig3 corner K | `work_products/2026-07-01_claude_checkpoint_presentation/fig3_corner_K.png` | USE |
| 4 | fig4 thermal | `work_products/2026-07-01_claude_checkpoint_presentation/fig4_thermal_htc.png` | USE |
| 4 | fig6 recirc | `work_products/2026-07-01_claude_checkpoint_presentation/fig6_recirculation.png` | USE |
| 5 | F0–F5 table | `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md` §1 | USE |
| 6 | mdot error bar | `reports/2026-07/2026-07-01/2026-07-01_rom_model_form_fits_and_1p4_boundary/figures/model_form_mdot_error_bar.png` | USE |
| 6 | predicted vs cfd | `reports/.../2026-07-01_rom_model_form_fits_and_1p4_boundary/figures/predicted_vs_cfd_mdot.png` | USE (backup) |
| 6 | FUSED model-form table | `work_products/2026-07-02_master_jul_2_presentation/fused_model_form_comparison.md` | CREATE |
| 7 | fig2 segment ΔP | `work_products/2026-07-01_claude_1d_predictivity_trial/fig2_segment_dp.png` | USE |
| 7 | fig3 minor budget | `work_products/2026-07-01_claude_1d_predictivity_trial/fig3_minor_loss_budget.png` | USE |
| 8 | figA insulation | `work_products/2026-07-01_claude_checkpoint_presentation/figA_insulation_sensitivity.png` | USE |
| 9 | figB condition-dep | `work_products/2026-07-01_claude_checkpoint_presentation/figB_condition_dependent_closure.png` | USE |
| 9 | fig4 perleg vs global | `work_products/2026-07-01_claude_checkpoint_presentation/fig4_perleg_vs_global_mdot.png` | USE |
| 10 | fig5 geometry | `work_products/2026-07-01_claude_checkpoint_presentation/fig5_geometry_swap.png` | USE |
| 10 | fig2 loop budget | `work_products/2026-07-01_claude_checkpoint_presentation/fig2_loop_budget.png` | USE (optional) |
| 11 | boundary sensitivity | `reports/.../2026-07-01_rom_model_form_fits_and_1p4_boundary/figures/boundary_sensitivity_mdot_error.png` | USE |
| 6 | annotated error bar | `work_products/2026-07-02_master_jul_2_presentation/figures/model_form_error_annotated.png` | CREATE |

## Figures/tables to CREATE (2)
1. **`fused_model_form_comparison.md`** — one table, F0–F5 + fitted forms, with BOTH mdot error and ΔP-distribution behavior side-by-side. The centerpiece for "compare model forms."
2. **`model_form_error_annotated.png`** — the mdot-error bar chart annotated with the hot-vs-matched-T story arc so condition-dependence reads at a glance.

## DO NOT regenerate (already exist, byte-verified)
- figA/figB/fig4_perleg: originals in overnight/predictivity dirs; deck copies are identical.
- All codex ROM-fit figures.

## Deck slide ordering note (validation figures available if you want a backup section)
codex readiness package also has paper-ready validation figures (mass-flow, energy-partition,
sensor-parity, scenario heatmap) under
`reports/2026-06/2026-06-23/2026-06-23_ethan_frozen_state_1d_validation/figures/png/` —
hold as backup slides if asked "how does the current baseline validate?"
