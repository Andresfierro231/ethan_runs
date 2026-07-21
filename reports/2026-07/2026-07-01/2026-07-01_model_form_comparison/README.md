# Internal report — 1D loop model: model-form & assumption comparison with error quantification

Status: DRAFT skeleton (2026-07-01, claude). The quantitative error columns marked
`[TRIAL]` are being produced by the 3D-closure-into-1D predictivity trial
(work_products/2026-07-01_claude_1d_predictivity_trial/, AGENT-168) and will be
filled in when it returns. Everything else (framework, prior results, theories,
caveats) is written from existing artifacts.

Purpose: for each 1D model FORM / assumption set, state (1) what it assumes, (2) how
it's driven & closed, (3) its error vs CFD (mdot and per-segment ΔP), (4) the theory
for why it errs, (5) its caveats. Audience values transparency, rigor, honesty.

## 0. Common ground (all forms share)
- The physical system: buoyancy-driven (no pump) molten-salt loop; steady mdot set by
  the balance DRIVING HEAD (buoyancy) = SUM of losses (friction + minor). Laminar,
  Re ~61-135 (Salt 2-4 Jin).
- CFD reference (coarse mesh, mainline continuation): loop mdot Salt2 = -0.01318 kg/s
  (Salt 1/3/4 from monitors); per-leg de-buoyed friction f/f_lam ~1.0-3.3 (T1b);
  per-corner minor-loss K ~6-16 (T7); buoyancy driving head ~41-45 Pa (T1b loop closure).
- CFD trust boundary: coarse mesh, NO mesh-independence bound yet (T6 blocked → self-mesh
  plan in checkpoint.md); single time per case; laminar. These caveats propagate to
  every "error vs CFD" below — the CFD is the reference, not ground truth.

## 1. The model forms compared
| # | Form | Driving | Friction (major) | Minor losses | Geometry | Solve |
|---|------|---------|------------------|--------------|----------|-------|
| F0 | zero-loss | buoyancy | none | none | — | local |
| F1 | major-only | buoyancy | friction only | none | schematic | local replay |
| F2 | major+minor, DEFAULT K | buoyancy | f (mult=1.0) | textbook K (k90=1.0, k20=0.10) | model default | full 1D loop |
| F3 | major+minor, CFD closures | buoyancy | de-buoyed f/f_lam (T1b) | CFD K 6-16 (T7) | mesh-corrected (T1/T8) | full 1D loop |
| F4 | local hydraulic replay (probe) | CFD ΔP fixed | CFD resistance | CFD feature resistance | probe | local |
| F5 | local hydraulic replay (endpoint) | CFD ΔP fixed | CFD resistance | CFD feature resistance | endpoint (schematic) | local |

## 2. Error quantification (vs CFD)
### 2a. Loop mdot — FULL 1D loop solve, signed % error vs CFD (Salt 2/3/4, high-trust)
(AGENT-168 predictivity trial, scenario predictive_airside_ins_1.0in_rad_1; Salt 1
excluded — only a low-trust early-window CFD reference.)
| Form | S2 | S3 | S4 | mean | reading |
|------|----|----|----|------|---------|
| F0 zero-loss (zero-maj-zero-min) | rail | rail | rail | ~+1400% (rails to model cap 0.2) | not predictive |
| F2a default, minor OFF (zero_minor) | +29.7% | +34.4% | +39.9% | +34.7% | over-predicts |
| F2b default K (k90=1.0, mult=1.0) | +24.8% | +27.3% | +29.9% | +27.3% | over-predicts |
| F3 CFD closures (k90~10-12, mult~1.9) | -16.6% | -17.3% | -19.0% | -17.6% | UNDER-predicts |
CFD mdot ref: S2 0.01318, S3 0.01497, S4 0.01698 kg/s.
LOCAL replay (drive held FIXED, AGENT-151): F4 probe ~1.9%, F1/F5 diverge/rail.

### 2b. Per-segment pressure drop (1D vs CFD ΔP) — Salt 2, friction legs
1D uses ONE global friction multiplier; CFD friction varies per leg -> huge local error:
| leg | CFD ΔP [Pa] | 1D ΔP [Pa] | % err |
|-----|-------------|------------|-------|
| heater (lower) | 15.1 | 22.6 | +49% |
| downcomer (right) | 14.4 | 22.6 | +57% |
| upcomer-lo (left_lower) | 3.2 | 9.0 | +182% |
| test-section | 2.8 | 5.4 | +96% |
| upcomer-up (left_upper) | 2.4 | 9.0 | +282% |
| cooler (upper) | 13.4 | 22.6 | +68% |
Corner minor ΔP (CFD): ~0.4-0.76 Pa each (~2.3 Pa total, ~5% of the loss budget).
Full tables: work_products/2026-07-01_claude_1d_predictivity_trial/segment_dp_compare.csv.

## 2c. RECONCILIATION — three analyses, one honest picture (cross-check finding)
Three lanes gave apparently-different "minor-loss" fractions; the trial resolved it:
- T1b loop closure: buoyancy head 45 Pa = friction 26 + "non-closure residual" 19 Pa
  (I labeled the 19 Pa "minor losses" ~42% of head).
- T7 direct corner bend-K: only ~2.3-5.6 Pa total (~5-12% of the budget).
- AGENT-168 trial segment ΔP: loss is ~90-95% distributed friction, ~5% corner-minor.
RESOLUTION: the 19 Pa "non-closure residual" is NOT clean lumped bend-K; it is mostly
DISTRIBUTED fitting/transition loss that behaves friction-like (occurs over the
fitting-end zones truncated from the straight-friction integral). Clean corner bend-K
is small (~5%). CORRECTION to the T1b wording: "minor losses ~30-43%" over-attributed
the residual to bends; the defensible statement is "straight friction ~57-70% of the
head; the remainder is split between fitting-transition distributed loss (larger) and
clean corner bend-K (~5%)." This is a definitional correction, not a numerical error in
the closure itself. Also: the T7 corner K (6-16) were referenced to a LOCAL fitting
dynamic head; applied against the 1D pipe-bulk dynamic head they over-weight minor loss
~5-8x -> treat bend-K as an UPPER BOUND; the per-leg friction is the trustworthy term.

## 3. Theories — WHY each form errs (finalized with trial numbers)
- **F0/F1 (no minor losses):** massively over-predicts mdot because the loop resistance
  is missing ~30-43% of its total (the bend/fitting minor losses — quantified by the
  T1b loop closure: head 41-45 Pa = friction 26-29 + minor 12-19). Theory: in a compact
  loop with 4 bends + reducers at low Re, minor losses are FIRST-ORDER, not a correction.
- **F5 (endpoint/schematic geometry):** diverges because the schematic probe CSV
  mis-locates the heater/downcomer (T8 swap, 0.566 m) and cuts the inclined heater as
  vertical (T1), so the endpoint pressure differences are taken across the wrong
  geometry. Theory: geometry-provenance error, not a modeling error — FIXED this session.
- **F2 (default textbook K):** the model's defaults (k90=1.0, k20=0.10, mult=1.0) are
  HIGH-Re values; at Re~60-135 the CFD says K~6-16 and f/f_lam~2-3.3 (~10x higher).
  Theory: laminar bend/friction scale as ~C/Re, so textbook constants under-predict
  loss → over-predict mdot (unless buoyancy-dominance masks it — see F3 hypothesis).
- **F3 (CFD closures):** hypothesis — injecting the mesh-corrected de-buoyed f and CFD K
  should (i) improve the per-segment pressure DISTRIBUTION markedly, and (ii) either
  improve mdot or reveal that mdot is buoyancy-dominated (set by ΔT via the thermal
  coupling) and hence robust to loss detail. The trial decides which. [TRIAL]
- **F4 (probe replay):** already ~1.9% on mdot — good, but it holds the CFD drive FIXED
  (not a true prediction) and uses a linear resistance R=dp/mdot; it does not test the
  coupled thermal-hydraulic loop. Theory: local replay flatters the model by removing
  the drive-side error.

## 4. Caveats per form (honesty)
- F0-F1: diagnostic only; not predictive.
- F2: "predictive" but with un-physical low-Re loss coefficients; any agreement may be
  fortuitous (buoyancy dominance) rather than correct physics — must check per-segment ΔP.
- F3: closures are coarse-mesh (no GCI yet, T6), laminar-K-at-low-Re, single-time; the
  minor-loss K references a dynamic head that is ill-defined in the upcomer recirc zone
  (T7) so the test-section connector loss folds into the cell model, not a K.
- F4-F5: local replays hold the CFD drive fixed → they test the RESISTANCE model, not the
  full predictive loop; linear-resistance assumption breaks if minor losses go quadratic.
- ALL: mdot and ΔT are coupled (higher mdot → lower ΔT at fixed duty); a form that gets
  mdot "right" with wrong losses may be compensating via the thermal side — the report
  must check mdot AND ΔP AND duty together, not mdot alone.

## 5. HEADLINE VERDICT (finalized 2026-07-01, from the trial)
1. **mdot is loss-sensitive, NOT purely buoyancy-dominated** — zero-loss rails; default
   over-predicts +27%, CFD closures under-predict -18%. The truth sits between, so
   neither closure set is "right" for mdot.
2. **The dominant mdot error is DRIVER-side, not closure-side.** At matched loss the 1D
   model runs Re 2-3x the CFD Re -> its buoyancy/ΔT driver over-produces flow. Fixing
   closures alone cannot close the ±20% gap; the thermal/buoyancy driver needs attention.
3. **The 1D model's single GLOBAL friction multiplier is structurally inadequate.** CFD
   friction varies per leg (f/f_lam 0.8-3.3); a global multiplier over-predicts the
   low-loss legs (test-section +96%, upper-upcomer +282-400%) while the loaded legs are
   closer. HIGHEST-VALUE MODEL CHANGE: replace the single multiplier with a PER-LEG
   friction multiplier (the T1b per-leg f/f_lam maps directly onto the 6 legs).
4. **Minor (bend) losses are a small, upper-bounded term (~5%), not the headline.** The
   loss budget is friction-dominated; the injected corner-K are an upper bound (local vs
   bulk q_ref, ~5-8x over). Earlier "30-43% minor" wording is corrected in §2c.
5. **Local replay flatters the model.** The AGENT-151 local replay's ~1.9% mdot held the
   CFD drive FIXED (tested only resistance); the FULL predictive loop is ±20-30% because
   it must also predict the drive. Report both, and be clear which is which.

TAKEAWAY for the 1D-model roadmap: (a) per-leg friction multiplier from CFD (quick, high
value); (b) investigate the buoyancy/ΔT driver (the Re 2-3x over-prediction); (c) keep
bend-K as a small upper-bound term; (d) all of this rests on coarse-mesh CFD until the
mesh-independence bound lands (self-generation plan, checkpoint.md).

## Sources
- AGENT-151 local replay: reports/2026-06/2026-06-29/2026-06-29_ethan_salt_pressure_drop_predictivity/
- 1D model: ../cfd-modeling-tools/tamu_first_order_model/Fluid (tamu_loop_model_v2, master_summary.csv)
- This session's closures: work_products/2026-07-01_claude_{momentum_budget,bend_minor_loss,thermal_downcomer}/
- Loop closure + friction: .agent/journal/2026-07-01/T1b-momentum-budget-debuoyed-friction.md
- Geometry fixes: .agent/journal/2026-07-01/{T1-mesh-centerlines-geometry-refix,T8-span-patch-colocation-audit}.md
- Predictivity trial (fills [TRIAL] slots): work_products/2026-07-01_claude_1d_predictivity_trial/

================================================================================
## 6. OVERNIGHT CORRECTIONS (2026-07-02) — read this; it revises §2a/§5
================================================================================
The §2a/§5 predictivity numbers were all computed at the 1D scenario ins=1.0in, which
runs the loop ~60 K HOTTER than CFD. Overnight controlled experiments corrected this:

- **Insulation sensitivity (the dominant lever).** 1D loop T swings 422->512->548 K over
  insulation 0->1->2 in. CFD's 450 K corresponds to ~0.27 in effective insulation. So the
  earlier "+27% mdot over-prediction (default)" was largely a thermal/BC-setting artifact,
  NOT a closure result.
- **Fair comparison AT CFD-matched insulation (loop T~450 K, ΔT 12.1 K = CFD):**
  default mdot -27%, global-mean -46%, per-leg -49% (Salt 2, ins 0.25 in). i.e. at matched
  temperature, adding the CFD friction makes mdot WORSE, not better.
- **Closure benefit on mdot is CONDITION-DEPENDENT** (helps when the loop is too hot/over-
  predicting; hurts when temperature-matched/under-predicting). CONCLUSION: mdot is NOT a
  robust closure-quality metric. The per-segment pressure DISTRIBUTION is (per-leg friction
  matches CFD by construction, independent of thermal state).
- **Open factor-2 discrepancy (honest).** At matched T with CFD per-leg friction the 1D
  predicts ~half the CFD mdot (0.0068 vs 0.0132). Loop ΔT matches and the 1D buoyancy head
  is not smaller, so "drive too weak" is DISPROVEN. Residual = a momentum-balance / friction-
  reference discrepancy. Partial contributor found: CFD f/f_lam is Re-DEPENDENT (4/6 legs
  rise with Re), so applying Re-68 multipliers at the 1D's Re-35 over-estimates friction
  ~10-30% — but that alone does not explain the factor of 2. NO validated mechanism yet.
- **Revised model-improvement ranking:** (1) get the thermal boundary right (match effective
  insulation / ambient-loss to CFD — the dominant lever); (2) reconcile the loop momentum
  budget term-by-term (buoyancy-head definition, f(Re), minor-loss reference) to explain the
  factor-2; (3) per-leg friction (fixes the pressure DISTRIBUTION, a real but secondary win).
Artifacts: work_products/2026-07-02_overnight/*; journals .agent/journal/2026-07-02/
{predictivity-culminating-diagnosis, driver-finding-REVISED-insulation-sensitivity,
per-leg-friction-implementation-and-predictivity}.md.
