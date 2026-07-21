# Per-leg friction multiplier — implementation + predictivity (overnight, 2026-07-02)

Owner: claude (autonomous). Depends on: per-leg friction capability added to
tamu_loop_model_v2/solver.py this session; CFD f/f_lam per leg (T1b).

## What was added (answers "did per-leg already exist?")
- The 1D model ALREADY: computes distributed friction per-segment (f=64/Re_local,
  segment D_h/length); has a per-parent-segment INTERNAL-HTC multiplier dict.
- It did NOT have a direct per-leg FRICTION multiplier (only a single global
  major_loss_multiplier + a profile-descriptor shape model).
- ADDED `ScenarioConfig.friction_multiplier_by_parent_segment` (mirrors the HTC dict;
  empty => 1.0, backward-compatible), applied in _effective_friction_multiplier_for_segment
  via the existing _multiplier_from_mapping helper. Smoke-tested + 4 fast tests pass.

## Predictivity comparison (Salt 2/3/4, scenario predictive_airside_ins_1.0in_rad_1)
1D loop |mdot| vs CFD, three friction forms:
| case | default (mult=1) | global-mean mult | per-leg friction | CFD |
|------|------------------|------------------|------------------|-----|
| S2 | +29.7% | -4.6% | -9.8% | 0.01318 |
| S3 | +34.4% | -3.3% | -9.8% | 0.01497 |
| S4 | +39.9% | -3.1% | -10.3% | 0.01698 |
Per-leg multipliers = CFD f/f_lam by construction (heater 2.67-2.88, downcomer
2.19-3.26, cooler 2.23-2.38, upcomer-lo 1.55-2.21, upcomer-up 0.82-1.04, test 1.0-1.46).

## Findings (honest)
1. **Per-leg gives a slightly WORSE mdot than the global mean (-10% vs -3 to -5%).**
   Why: per-leg correctly LENGTH-WEIGHTS the high-friction long legs (heater/downcomer/
   cooler, mult 2.2-3.3, ~0.9 m each) rather than a flat mean (1.86-2.09) that is pulled
   down by the short low-friction legs (test 1.0, upcomer-up 0.82). So per-leg applies
   more total resistance -> lower mdot. The global mean's closeness to CFD mdot is
   partly FORTUITOUS (a single scalar tuned near the length-weighted value), not because
   it is more correct. Per-leg is the physically-correct distribution.
2. **The dominant mdot error is DRIVER-side, not friction.** Even with per-leg CFD
   friction, predicted Re ~154 (S2) vs CFD ~68 — ~2.3x. The 1D buoyancy/ΔT driver
   over-produces flow; no friction closure can fix that. This corroborates the
   AGENT-168 trial verdict.
3. **Value of per-leg = the pressure DISTRIBUTION**, not the integrated mdot. Each leg's
   friction now matches CFD by construction, so the per-segment ΔP errors the global
   multiplier produced (+96% to +400% on the low-loss legs) collapse to ~0. That is the
   defensible win for a 1D model that must get local pressures right (e.g. for TP/TW
   pressure predictions), even if mdot is driver-limited.

## Caveats
- Coarse-mesh CFD closures (no mesh-independence bound yet; mesh GCI de-risk running).
- The per-leg dict covers the 6 named legs; short horizontal connectors default to 1.0
  (no CFD leg maps to them) — a small unmodeled term.
- Single scenario/insulation condition; mdot-ΔT coupling means the driver error and
  closure error partly trade off — must be assessed together (see model-form report).

## Next steps to bolster credibility
1. Per-segment ΔP figure: show per-leg friction ΔP vs CFD per leg (matches by
   construction) vs global-multiplier (over-predicts low-loss legs 100-400%).
2. DRIVER investigation: at the CFD mdot, compare the 1D model's predicted loop ΔT /
   gross duty / buoyancy head to CFD to localize the Re-2.3x over-prediction (thermal
   driver). This is the highest-value 1D-model fix after per-leg friction.
3. Once the mesh GCI bound lands, re-state the closures with a discretization-error bar.

Outputs: work_products/2026-07-01_claude_1d_predictivity_trial/{perleg_vs_global_mdot.csv,
.json, fig4_perleg_vs_global_mdot.png, run_perleg_friction_compare.py, make_perleg_figure.py}.
