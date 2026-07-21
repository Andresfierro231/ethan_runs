# T9 — Solver Ra/Ri/Gr/Re/Nu definition audit (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162). Source: `system/functions` coded FO `dimensionlessFields`
in the Salt 2 Jin continuation case (embedded by factory.py; same across the family).

## Exact solver definitions (per-cell coded FO, written each output time)
Constants: D = **0.022098 m** (nominal bore), gMag = 9.81, rhoRef = **1958.4841 kg/m3**,
TRef = **447.00 K (173.85 C)**. Properties evaluated at each cell's T via the Jin
mu(T)=A exp(b/T...), k(T), Cp(T), rho(T)=2293.6-0.7497 T (rho(447)=1958.5 = rhoRef ✓).

- Pr = mu*Cp/k
- Re = rho*|U|*D/mu               (local rho,|U|,mu; **D = nominal 22.098 mm**)
- Gr = g*|rhoRef - rho|*D^3*rhoRef / mu^2   (DENSITY-based Grashof; buoyancy from
  |rho-rhoRef| about the fixed TRef, NOT beta*DeltaT; density scale = rhoRef)
- Ri = Gr/Re^2
- Ra = Gr*Pr
- Nu = |q_w|*D / (k*|T_w - TRef|)  (wall Nu referenced to the FIXED TRef=447 K)

## Findings that affect the closures / correlation (disclose in paper)
1. **Characteristic length is the NOMINAL bore 22.098 mm applied to EVERY cell**,
   including the test section whose true bore is **20.9 mm** (T1). So the solver's
   coded Re/Nu are ~+5.7% and Gr/Ra ~+18% high IN THE TEST SECTION vs a
   true-bore definition. My extraction tools use the MEASURED per-leg D_h, so the
   solver-field Ri/Ra and my tool numbers use DIFFERENT D there -> reconcile before
   quoting either as "the" dimensionless group. (Elsewhere D_meas~22.1 ~ nominal, OK.)
2. **Buoyancy reference is fixed (TRef=447 K, rhoRef=1958.48)**, not local. The
   reversal correlation must use this same reference (or convert) for Gr/Ri to be
   comparable across cases; document TRef as the datum.
3. **Solver wall Nu uses (T_w - TRef)**, but the physically meaningful convective
   Nu uses (T_w - T_bulk) -- which is what T4's sample_segment_htc_uaprime.py uses.
   These are DIFFERENT quantities; the T4 Nu (local bulk) is the correct
   convective one. Do NOT mix the solver-field Nu with the extracted Nu.
4. **Per-cell Ri = Gr/Re^2 diverges where |U|->0** (Re->0). This is the ROOT of the
   "use section MEDIAN Ri, not mean" gotcha: the section mean is dominated by
   near-stagnant cells. The correlation must use the median (Ri_streamwise =
   Ri_median*cos theta), consistent with the reversal-criterion lane.
5. Gr uses |rhoRef - rho| (absolute) -> loses the SIGN of buoyancy (heating vs
   cooling). For a signed reversal criterion, recover the sign from (rho - rhoRef)
   or from the flow-orientation work in T1b.

## Reconciliation actions (for T10/T11)
- Decide ONE characteristic length policy (recommend measured per-leg D_h from T1)
  and recompute Re/Gr/Ra/Nu consistently, OR clearly tag solver-field vs extracted.
- Use (T_w - T_bulk) Nu (T4), not the solver's (T_w - TRef) Nu.
- Use median Ri; carry the buoyancy sign.
No code changed in this audit (read-only). Feeds T10 (correlation) + T11 (bundle).
