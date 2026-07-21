# REVISED driver finding: the 60 K over-heat is mostly an insulation/BC mismatch (2026-07-02)

Owner: claude (autonomous). SUPERSEDES the interpretation in
driver-side-thermal-overheat-finding.md (the raw 60 K gap stands, but its CAUSE is
now attributed correctly). This is the caveat-resolution I flagged as the next step —
and it changed the conclusion. Tool: work_products/2026-07-02_overnight/insulation_sweep.py.

## What the insulation sweep showed (Salt 2, default closures)
| scenario | T_mean [K] | mdot | Re |
|----------|-----------|------|-----|
| ins 0.0in rad0 | 421.7 | 0.00776 | 27.5 |
| ins 0.0in rad1 | 375.3 | 0.00106 | 2.9 |
| ins 1.0in rad1 | 512.0 | 0.01646 | 209.5 |
| ins 1.0in rad0 | 544.1 | 0.01947 | 354.6 |
| ins 2-3in | 541-548 | ~0.019-0.020 | ~350-380 |
CFD Salt 2: T_mean 450.3 K, mdot 0.01318, Re 68.

## The correction
- The 1D loop temperature is EXTREMELY sensitive to the insulation/ambient-loss boundary:
  T swings 422 -> 512 -> 548 K over insulation 0 -> 1 -> 2 in. CFD's 450 K is BRACKETED
  between the 1D's 0 in and 1 in settings -> CFD's EFFECTIVE insulation ~ 0.3-0.5 in equiv.
- => The dramatic "60 K over-heat / Re 2.3x" reported earlier was measured at an ARBITRARY
  insulation setting (1.0 in) that runs the loop far hotter than CFD. It is DOMINATED by a
  boundary-condition mismatch, NOT a structural model defect.
- Interpolating the 1D result to the CFD loop T (450 K): mdot ~ 0.0095-0.0105 (-20 to -28%
  vs CFD) and Re ~ 104-116 (ratio 1.5-1.7x vs CFD, DOWN from 2.3x). So matching the thermal
  boundary removes most of the discrepancy; a ~1.5x Re / ~20-28% mdot RESIDUAL remains as
  the genuine model gap.

## CRITICAL methodological consequence (affects all prior predictivity numbers)
The earlier predictivity comparisons (AGENT-168 trial: default +27%, CFD-closures -18%;
per-leg run: per-leg -10%) were ALL run at ins=1.0in — i.e. at a loop ~60 K HOTTER than CFD.
So they conflate CLOSURE error with the INSULATION-driven over-heat (which changes rho, mu,
Re, and hence friction). The predictivity comparison is only meaningful at a CFD-MATCHED
operating temperature. THIS IS THE HEADLINE OVERNIGHT CORRECTION: the closure comparison must
be redone at matched effective insulation (matched loop T ~ 450 K) before any claim about
whether CFD closures help. The prior numbers are NOT wrong arithmetic; they were computed at
an uncontrolled thermal condition and must not be read as closure-only effects.

## Caveats / uncertainties
- Linear interpolation across the coarse 0->1 in insulation step (T 375-512 K in rad1) is
  APPROXIMATE; the matched insulation (~0.3-0.5 in) and the residual mdot/Re are rough. A
  finer insulation sweep (0.25/0.5/0.75 in) is launching to pin it.
- The 1D "insulation thickness" is a model parameterization, not the CFD's wall-h boundary;
  "matched" means matched loop T / effective UA, not identical BC form.
- Coarse-mesh CFD reference (no GCI bound yet); rad on/off changes the sweep markedly (the
  rad_1 ins_0 case nearly stalls, T 375 K) -> the radiation setting is itself a lever to match.

## Next steps to bolster credibility (ranked)
1. Finer insulation sweep (0.25/0.5/0.75 in) -> pin the effective insulation that gives CFD
   T~450 K (running now: insulation_sweep_fine.py).
2. RE-RUN the closure predictivity (default vs global-mult vs per-leg) AT THAT MATCHED
   insulation -> the ONLY fair closure comparison. Report mdot + per-segment ΔP there.
3. Decompose the 1D loop energy balance (Q_heater in, Q_cooler out, Q_ambient) at matched T
   vs CFD to characterize the residual ~20% model gap (ambient-loss model form).
4. Longer term: match the 1D ambient-loss UA directly to the CFD wall-h boundary rather than
   via an effective insulation thickness.
