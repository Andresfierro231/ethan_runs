# T1b — Streamwise momentum budget: friction without embedded buoyancy (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162)
Depends on: T1 (mesh centerlines). Status: DONE for the friction decomposition;
upcomer-tool wiring (sample_upcomer_convection_cell.py) still pending.

## Problem (from T1)
Single-leg `p_rgh` gradient gave NEGATIVE apparent Darcy f on the heated/cooled
legs. Two distinct errors were tangled:
1. **Flow-orientation error.** `derive_segment_friction.py` implicitly assumes
   loop-order s == flow direction (sigma=+1) on EVERY leg. Measured
   sigma = sign(mean U . tangent) is **-1 on the heater (`lower_leg`) and
   downcomer (`right_leg`)** — flow runs against loop-order there — and **+1 on
   the upcomer and cooler**. So the legacy tool mis-signed the heater/downcomer.
2. **Buoyancy embedded in p_rgh.** `p = p_rgh + rho*gh`, `gh = g.x = -9.81*y`
   (g verified in constant/g). The streamwise momentum balance carries a buoyancy
   SOURCE `gh*d(rho)/ds` that `p_rgh` does not contain; on the active legs it
   dominates the gradient.

## Method (new tool `tools/analyze/derive_streamwise_momentum_budget.py`)
Rigorous steady bulk balance, projected on the flow direction xi = sigma*s:

    friction_loss_per_vol = -dp_rgh/dxi - gh*d(rho)/dxi - rho*u*du/dxi
                          = -sigma * ( dP + gh*dR + rho*u*dU )     [Pa/m]

with dP,dR,dU = endpoint gradients over INTERIOR stations (fitting ends dropped),
sigma from the measured `u_along_tangent` (added to sample_section_mean_pressure.py),
gh at the leg-mean y, mu from Jin(T(rho)) for Re. f = 2 D_h (loss)/(rho u^2).
Reports f_raw (orientation-fixed, buoyancy still in), f_corrected (de-buoyed),
f_corrected_noinertia, AND the raw terms so the buoyancy source is reported.
Consistency check built in: isothermal leg (dR->0) => f_corr == f_raw.

## RESULT — de-buoyed Darcy friction (all legs POSITIVE, physical), Salt 2/3/4 Jin
f_corrected / f_lam(=64/Re):

| Leg (physical)        | Salt2 | Salt3 | Salt4 | sigma | buoy/dP (S2) |
|-----------------------|-------|-------|-------|-------|--------------|
| lower_leg (HEATER)    | 2.67  | 2.72  | 2.88  |  -1   | 2.20 (buoy-dominated) |
| upper_leg (COOLER)    | 2.23  | 2.30  | 2.38  |  +1   | 1.21 |
| right_leg (DOWNCOMER) | 2.19  | 2.72  | 3.26  |  -1   | 0.26 |
| test_section_span     | 1.46  | 1.19  | 1.00  |  -1   | 1.20 |
| left_lower (UPCOMER)  | 1.55  | 1.79  | 2.21  |  +1   | 0.23 |
| left_upper (UPCOMER)  | 1.04  | 0.91  | 0.82  |  +1   | 0.54 |
Re envelope ~61-135 (S2->S4). Inertial term negligible everywhere
(O(0.01-0.3) Pa/m vs dP/buoy O(10-100)) — now quantified, not assumed.

## Interpretation (paper)
- Every leg now yields a POSITIVE, O(f_lam) friction: f/f_lam ~ 1.0-3.3.
- Buoyancy contamination (buoy/dP) is largest on the ACTIVE legs — heater ~2.2x,
  cooler ~1.2x — and smallest on the downcomer (~0.1-0.26x): exactly as physics
  predicts (density gradients concentrate where heat is added/removed).
- The COOLER's raw f_raw stays negative (-11 -> -8 -> -5.8) because its gradient
  is ~120% buoyancy; only the de-buoyed f_corr (~2.2-2.4) is meaningful.
- Trends: heater & downcomer f/f_lam RISE with Re (developing-flow / secondary-
  flow signature); the upper upcomer approaches fully-developed laminar
  (f/f_lam ~ 0.8-1.0). These are provisional (coarse mesh, GCI pending = T6).

## Two user asks — status
1. "consistently report the bulk momentum gradient term": DONE — momentum_budget
   .json/.csv report dP/ds, buoyancy source gh*dR, inertial term, sigma, per leg
   per case, in `work_products/2026-07-01_claude_momentum_budget/`.
2. "friction that doesn't embed buoyancy": DONE — f_corrected removes the buoyancy
   source rigorously via the momentum balance + measured per-leg flow orientation.

## Confidence / limits (disclose)
- Bulk 1D reduction of section means; leading-order balance, not full 3D stress.
- Coarse-mesh discretization error still unquantified (T6/GCI).
- gh at leg-mean y (2nd-order rho*d(gh)/ds absorbed in p_rgh, not double counted).
- Perfect loop closure (sum of leg friction losses == buoyancy driving head) not
  yet checked end-to-end — a good next validation.

## Follow-ons
- Wire `--centerline-source mesh` into sample_upcomer_convection_cell.py (rest of T1b).
- Loop-closure energy check (friction losses vs buoyancy head).
- Feed f_corrected into the closure bundle (T11) once GCI (T6) bounds it.

## Loop-closure capstone (2026-07-01) — validates + yields the minor-loss budget
Summing the per-leg momentum budget around the loop (F = total straight friction
loss, B = buoyancy head, P = p_rgh non-closure), leg lengths from mesh_stations
(interior stations):

| Case | F_fric [Pa] | B_buoy [Pa] | P_close [Pa] | F-(B+P) | F/B |
|------|-------------|-------------|--------------|---------|-----|
| Salt2 | 25.63 | 44.87 | -19.25 | 0.004 | 0.57 |
| Salt3 | 27.03 | 43.49 | -16.48 | 0.020 | 0.62 |
| Salt4 | 28.98 | 41.17 | -12.25 | 0.054 | 0.70 |

- F-(B+P) ~ 0 confirms inertia is negligible (identity holds to rounding).
- Around a CLOSED loop the p_rgh integral must vanish, so the straight-leg
  non-closure |P| ~ 12-19 Pa is the pressure drop in the UN-MODELED corners /
  fittings = the MINOR-LOSS budget. It is ~30-43% of the buoyancy driving head
  (B ~ 41-45 Pa), and its fraction shrinks as Re rises (F/B 0.57 -> 0.70).
- => Straight friction alone under-predicts loop resistance by ~30-43%; the
  bends/reducers/test-section contraction (T7 K-factors) are first-order, not a
  correction. Directly motivates + bounds T7.
- Caveat: assumes corners contribute to P but negligibly to B and straight F
  (short segments); a per-corner decomposition is T7.

## Tests
`tools/analyze/test_derive_streamwise_momentum_budget.py` (3: isothermal
consistency, sigma orientation, decomposition identity). Suite 39 pass.
