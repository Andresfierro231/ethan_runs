# Driver-side finding: the 1D model runs ~60 K too hot (overnight, 2026-07-02)

Owner: claude (autonomous). Tool: work_products/2026-07-02_overnight/driver_thermal_compare.py
(reusable). Depends on: per-leg friction (this session), CFD bulk T (T4).

## The finding
Solving the 1D model with the CORRECT per-leg CFD friction and comparing its loop
temperature to CFD (scenario predictive_airside_ins_1.0in_rad_1):
| case | src | mdot | Re_main | T_mean [K] | ΔT_loop [K] |
|------|-----|------|---------|------------|-------------|
| S2 | CFD | 0.01318 | 68 | 450.3 | 12.1 |
| S2 | 1D  | 0.01190 | 154 | **512.2** | 8.2 |
| S3 | CFD | 0.01497 | 88 | 463.7 | 12.2 |
| S3 | 1D  | 0.01350 | 211 | **527.4** | 8.3 |
| S4 | CFD | 0.01698 | 120 | 479.2 | 12.3 |
| S4 | 1D  | 0.01524 | 286 | **545.4** | 8.6 |

The 1D loop runs **~62-66 K HOTTER** than CFD, consistently, with a SMALLER loop ΔT.

## Why this matters (the predictivity story, corrected)
- This EXPLAINS the Re ~2.3x gap the trial + per-leg run flagged: at ~512 K the salt
  viscosity is much lower than at the CFD's 450 K, so Re = rho*v*D/mu is ~2.3x higher
  even at similar mdot. The Re gap is a THERMAL-FIELD symptom, not a hydraulic-closure or
  viscosity-correlation error (the mu correlation is within ~25%; see the property note).
- => The dominant 1D mdot error is DRIVER-side (thermal). Fixing friction closures cannot
  close it. The high-value 1D-model work is on the THERMAL/ambient-loss side, not hydraulics.
- Physical sanity check: 1D T_mean 512 K = 239 C is ABOVE Ethan's confirmed rig operating
  range (165-210 C); CFD 450 K = 177 C is inside it. So the 1D model is running the loop
  hotter than the real rig operates — a red flag consistent with under-predicted heat loss.

## Likely mechanism (hypothesis, to verify)
At quasi-steady, loop T ~ ambient + Q_heater / UA_total_loss. A ~60 K over-heat with the
same heater power implies the 1D model's TOTAL heat loss (ambient + cooler) is UNDER-predicted
(UA too low), so the fluid retains more heat. The smaller 1D ΔT (8.2 vs 12.1 K) is also
consistent with a different loss/transport balance. Candidate causes: ambient-loss model /
insulation UA, cooler (HX) duty, or a scenario/BC mismatch vs the CFD case (see caveat).

## Caveats / uncertainties (important)
- SCENARIO MATCHING: this used one 1D scenario (ins 1.0in, rad on). If that scenario's
  insulation/ambient/heater-power does NOT match each CFD case's actual BCs, part of the
  60 K gap is a setup mismatch, not a model error. NEXT STEP: match the 1D scenario BCs to
  each CFD case's real heater power + insulation + ambient before attributing the gap fully
  to the model. (High priority — this could reduce or re-explain the 60 K.)
- CFD T_mean is the segment-bulk mean from T4 (coarse mesh, no GCI bound yet); the 1D T_mean
  is the segment T_avg mean. Comparable, but both carry their own caveats.
- The 1D duty reported (qhx ~46-54 W) is the cooler extraction; cross-check vs CFD gross duty.

## Next steps to bolster credibility
1. Match 1D scenario BCs to each CFD case (heater power, insulation thickness, ambient) and
   re-run driver_thermal_compare -> isolate genuine model error from setup mismatch.
2. Decompose the 1D loop energy balance (Q_heater in, Q_cooler out, Q_ambient) vs CFD to find
   WHERE the ~60 K comes from (loss under-prediction vs input mismatch).
3. Once matched, if the over-heat persists, it is the #1 1D-model fix (thermal/ambient-loss),
   ranked ABOVE the per-leg friction (which fixes the pressure distribution but not mdot).

Outputs: work_products/2026-07-02_overnight/driver_thermal_compare.{py,json,log}.
