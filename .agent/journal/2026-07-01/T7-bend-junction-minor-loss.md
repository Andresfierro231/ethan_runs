# T7 — Bend / junction / connector minor-loss K factors (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162). Motivated + bounded by the T1b loop-closure
(~30-43% of the buoyancy head is lost in the corners/fittings, ~12-19 Pa).

## Method (new tool `tools/extract/sample_bend_minor_loss.py`)
Each feature in the profile `feature_budgets` (4 corners + the test-section
connector) is bounded by two ncc interface patches (start/end). Dump (U,p_rgh,rho)
on each patch (raw `surfaces` FO, OF13), area-mean per face. Dissipative loss:

    loss = -(Delta p_rgh + gh*Delta rho + Delta q_dyn),  gh = -9.81*y_feature_mean

i.e. the mechanical-head drop with the REVERSIBLE buoyancy source gh*Delta rho
subtracted (same decomposition as the T1b momentum budget). K = |loss|/q_ref;
q_ref = throat-max dynamic head for area-change features, mean otherwise.

**Sign-convention lesson (documented so it is not repeated):** neither raw p_rgh
nor p_rgh+rho*gh works. Using P0=p_rgh+1/2 rho u^2 MISSES the buoyancy source
(gh*Delta rho); using P0=p_rgh+rho*gh+1/2 rho u^2 re-introduces the full,
RECOVERABLE hydrostatic (rho*g*dz ~ 335 Pa across an 18 mm corner) and swamps the
~0.5 Pa loss. Only subtracting gh*Delta rho (NOT rho*Delta(gh)) isolates dissipation.

## RESULT — corner minor-loss K, Salt 2/3/4 Jin
| Feature            | K (S2) | K (S3) | K (S4) | loss[Pa] S2 | dz[m] |
|--------------------|--------|--------|--------|-------------|-------|
| corner_lower_left  | 8.2    | 8.3    | 8.3    | 0.50 | -0.018 |
| corner_lower_right | 16.5   | 13.8   | 10.7   | 0.77 | +0.018 |
| corner_upper_right | 15.9   | 14.3   | 13.6   | 0.60 | +0.018 |
| corner_upper_left  | 6.3    | 6.2    | 6.7    | 0.40 | -0.018 |
| test_section_complex | K UNDEFINED (recirc zone, q_ref~0) | loss ~3.3 Pa | -0.249 |
Re envelope ~61-135 (S2->S4).

## Interpretation (paper)
- Corner K ~ O(6-16), DECREASING with Re on the right-side corners (16.5->10.7),
  ~constant on the left corners. Classic laminar-bend behaviour (K ~ C/Re + K_inf):
  at Re~60-135 the viscous C/Re part is large, so K >> the high-Re turbulent
  values (~0.2-1). This is expected and important: the 1D model must use Re-dependent
  minor-loss K, not textbook high-Re constants.
- The test-section connector's interface patches sit IN the upcomer recirculation
  cell (T5), so their mean face velocity ~0 and a dynamic-head K is ill-defined.
  The loss (~3.3 Pa) is real but must be folded into the upcomer cell model, not a K.

## Reconciliation with the loop-closure budget (T1b)
Sum of the 4 corner + connector losses ~ 5.6 Pa (S2) vs the loop-closure minor-loss
budget ~19 Pa. The gap is expected: the loop-closure |P| lumps ALL non-straight
pressure change, including the FITTING-END leg zones that were truncated from the
straight-friction integral (interior stations only). So ~5.6 Pa is the named-feature
share; the remainder lives in the fitting transitions between each corner and the
straight run. A full reconciliation needs per-fitting planes (future).

## Confidence / limits
- Coarse mesh (GCI pending, T6); single time per case; area-mean of ncc faces
  (coverage <1 possible). Corner K's are provisional pending T6.
- Connector K undefined in the recirc zone (flagged, not fabricated).

## Tests / outputs
`tools/extract/test_sample_bend_minor_loss.py` (4: buoyancy subtraction at equal +
changing elevation, recirc-zone guard, throat-max q_ref).
`work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.{json,csv}`.
