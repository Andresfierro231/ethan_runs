# Predictivity thread — culminating diagnosis (overnight, 2026-07-02)

Owner: claude (autonomous). Synthesizes the per-leg friction + trial + insulation +
matched-condition results into one honest picture. This SUPERSEDES the intermediate
"drive too weak" hypothesis (disproven by direct check — see below).

## The controlled experiment (Salt 2)
Injected the CFD per-leg friction (f/f_lam by leg, T1b) into the 1D model AND matched
the insulation so the loop mean-T equals CFD (ins ~0.25-0.27 in -> T ~447-450 K vs CFD 450.3):
| quantity | 1D (matched-T, per-leg CFD friction) | CFD | note |
|----------|--------------------------------------|-----|------|
| T_mean | 447.2 K | 450.3 K | MATCHED (by insulation) |
| loop ΔT | 12.1 K | ~12.1 K | **MATCHES** (not 8 K; the 8 K was at the hot ins=1.0in) |
| dP_buoyancy | 56.4 Pa | ~45 Pa (T1b loop-closure) | 1D head is if anything HIGHER (defn differs) |
| mdot | 0.00677 | 0.01318 | 1D ~HALF |
| Re_main | 35.0 | 68 | 1D ~HALF |

## What this rules IN and OUT (honest)
- RULED OUT: "thermal drive too weak." The loop ΔT matches CFD (12.1 K) and the 1D
  buoyancy head is not smaller. So the residual is NOT a thermal-drive-magnitude problem.
- RULED OUT (as the mdot story): "CFD closures improve mdot." At CFD-matched T, adding the
  CFD friction makes mdot WORSE: default -27% -> global-mean -46% -> per-leg -49% (ins 0.25).
  Whether closures help mdot is CONDITION-DEPENDENT (help when the loop is too hot/over-
  predicting; hurt when matched/under-predicting). => mdot is NOT a robust closure-quality
  metric; the per-segment pressure DISTRIBUTION is (per-leg matches CFD by construction).
- OPEN DISCREPANCY (flagged, not explained): at matched T with CFD per-leg friction, the 1D
  predicts ~HALF the CFD mdot. The model balances a (nominally higher) buoyancy head against
  its friction at a much lower mdot/Re than CFD. Candidate causes, NONE yet confirmed:
  (a) friction-REFERENCE Re: f/f_lam~2 was measured at CFD Re~68; f/f_lam is likely
      Re-DEPENDENT (developing/secondary-flow excess), so applying a constant multiplier on
      64/Re at the 1D's lower Re (35) over-estimates friction and drives a low-mdot spiral;
  (b) buoyancy-head DEFINITION mismatch between the CFD loop-closure (Σ -σ gh dρ L ~45 Pa)
      and the 1D (Σ -ρ g Δy ~56 Pa) — not apples-to-apples, so the "head" comparison is only
      indicative;
  (c) unmodeled distributed fitting loss / minor-loss reference (the ~5-30% budget nuance).

## Honest bottom line for the advisor
The CFD closures are physically sound (friction f/f_lam~2, distribution matches by
construction), but simply plugging them into the current 1D loop model does NOT yield a
predictive mdot — at CFD-matched temperature the 1D under-predicts mdot by ~half. The
apparent "closures help" seen earlier was an artifact of running at a 60 K-too-hot
insulation. The real, open question is a term-by-term MOMENTUM-BALANCE reconciliation
between the CFD and the 1D (friction reference Re, buoyancy-head definition, minor-loss
budget). We are transparent that we do NOT yet have a validated mechanism.

## Next steps to bolster credibility (ranked)
1. Check f/f_lam Re-DEPENDENCE: is the CFD "excess friction" a constant multiplier or does
   it scale with Re? Re-derive f vs Re per leg from the CFD (we have Salt 2/3/4 = 3 Re
   points). If Re-dependent, the 1D must apply f(Re), not a constant multiplier at the wrong Re.
2. Reconcile the buoyancy-head DEFINITIONS (CFD loop-closure vs 1D Σρg Δy) on a common basis
   so the drive comparison is apples-to-apples.
3. Full term-by-term loop momentum budget: CFD vs 1D, at matched T, to localize the factor-2
   mdot gap (drive vs friction vs minor).
4. All of the above rest on coarse-mesh CFD (no GCI bound yet; mesh self-gen blocked at the
   NCC stitcher, fix = conformal-first).

## Artifacts
work_products/2026-07-02_overnight/{matched_closure_compare,insulation_sweep,insulation_sweep_fine}.{py,json,log},
driver_thermal_compare.*, run_perleg_friction_compare.py; journals per-leg-*, driver-*REVISED*.
