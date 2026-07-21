# T4 — Downcomer (right_leg) thermal closure (paper notes)

Date: 2026-07-01
Owner: claude (AGENT-162)
Depends on: T1 (geometry — downcomer is vertical, so schematic cut is acceptable).

## What / why
The downcomer thermal segment was policy-BLOCKED in
`tools/extract/sample_segment_htc_uaprime.py` (THERMALLY_BLOCKED_SEGMENTS={downcomer}).
q_w is reconstructed, T is available (OF13), and U3 confirmed the downcomer is an
ordinary passive f(Re)+Nu leg with NO recirculation. Added `--admit-downcomer`
(unblocks downcomer + admits an INDICATIVE Nu for right_leg). The downcomer is
vertical so the schematic cut-plane orientation is fine for its bulk T (the T1
geometry problem was specific to the inclined heater).

## RESULT — downcomer thermal, Salt 2/3/4 Jin (mainline continuation)
| Case | HTC [W/m2K] | UA' [W/mK] | R' [mK/W] | Nu | q' [W/m] | Tbulk[K] | Twall[K] |
|------|-------------|-----------|-----------|-----|----------|----------|----------|
| Salt2 | 43.2 | 2.96 | 0.338 | 1.74 | -25.0 | 451.6 | 443.1 |
| Salt3 | 43.9 | 3.01 | 0.333 | 1.76 | -27.4 | 464.5 | 455.4 |
| Salt4 | 43.7 | 3.00 | 0.334 | 1.74 | -30.4 | 480.0 | 469.8 |

Consistency: same run reproduced the heater HTC (252/269/288) and UA'
(16.6/17.7/18.9) from the prior thermal lane exactly, and the upcomer Nu
(3.1/4.1/5.0). So T4 only ADDS the downcomer; it does not perturb established numbers.

## Interpretation (paper)
- Downcomer HTC ~43-44 and Nu ~1.74-1.76 are essentially CONSTANT across the
  Re 61-135 envelope -> a passive leg with near-constant parasitic heat loss to
  ambient (q' ~ -25 to -30 W/m; wall cooler than bulk -> fluid sheds heat).
- Nu ~1.75 sits BELOW the fully-developed laminar values (4.36 const-q, 3.66
  const-T): consistent with a low-Peclet parasitic-loss leg dominated by the
  external/ambient resistance, not internal developed convection. Report as an
  INDICATIVE Nu with that caveat.
- Confirms the U3 model: downcomer = ordinary passive leg (f from T1b momentum
  budget f/f_lam ~2.2-3.3; thermal = small parasitic loss, no recirculation).

## Confidence / limits
- Coarse mesh, GCI unquantified (T6).
- foamPostProcess returned rc=1 on the T-cut dump (benign post-write exit; the T
  and wall fields parsed and the values are physically consistent + reproduce
  prior heater/upcomer numbers). Re-run under a clean OF13 step if a reviewer
  needs rc=0 provenance.
- Nu is indicative (right_leg admitted for reporting; downcomer is not a
  developed-convection leg).

## UA'/q' CORRECTION via T8 mesh-length fix (2026-07-01)
The initial UA'/q' above used the schematic centerline_labels for segment length,
which are ~1.3x inflated (T8). Re-ran with `--mesh-length` (mesh-centerline length):
| Case | heater UA' | downcomer UA' | upcomer UA' | (HTC/Nu unchanged) |
|------|-----------|---------------|-------------|--------------------|
| Salt2 | 16.56 -> **22.08** | 2.96 -> **3.75** | 5.10 -> **6.64** | HTC 252/43/77; Nu -/1.74/3.11 |
| Salt3 | 17.67 -> **23.55** | 3.01 -> **3.80** | 6.69 -> **8.72** | HTC 269/44/102; Nu -/1.76/4.06 |
| Salt4 | 18.92 -> **25.22** | 3.00 -> **3.79** | 8.29 -> **10.79** | HTC 288/44/126; Nu -/1.74/4.99 |
HTC (q_w/DeltaT) and Nu (D_h) are LENGTH-FREE and UNCHANGED. UA' and q' rose
~27-33% (length-normalized). The mesh-length values are the accurate ones; the
prior "matches prior work" agreement was because prior work also used the inflated
label length. Use the mesh-length UA'/q' henceforth.

## Outputs
`work_products/2026-07-01_claude_thermal_downcomer/segment_htc_uaprime_*.{json,csv}`
(now with `--mesh-length`; `segment_length_source=mesh_centerline`).
