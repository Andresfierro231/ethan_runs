# Segment Friction from Section-Mean Pressure (continuation / mainline)

Date: `2026-06-30` · Owner: claude (AGENT-156) · Tool: `tools/analyze/derive_segment_friction.py`

## What this is

Apparent Darcy friction factor per straight segment, derived the NEW way — from
geometry-measured section-mean pressure gradients on the MAINLINE continuation
reconstructions (salt2_jin t=7915, salt3_jin t=7618, salt4_jin t=10000) — as an
independent cross-check of the legacy wall-based extractor.

Inputs: `work_products/2026-06-30_claude_continuation_section_mean/section_mean_pressure_*.json`
(section-mean p_rgh, total pressure, measured D_h≈21.8 mm, u_bulk, rho per station).

## Headline results (observed)

- **Heated `lower_leg`: apparent f ≈ 3.1 / 2.7 / 2.7 (Salt 2/3/4 Jin).** This
  CROSS-VALIDATES the legacy defended fit (~2.5 on lower_leg) via a fully
  independent method (section-mean total-pressure gradient + measured D_h vs the
  legacy wall-shear / wall-pressure route). Agreement to ~10–25% is strong given
  the methods share no machinery.
- `right_leg` (downcomer): f ≈ 0.9–1.0.
- `left_lower_leg` (upcomer section): f ≈ 1.0–2.1 (two-station gradient — flagged
  as low-support).
- **`upper_leg` (cooler leg): NEGATIVE f (−6 to −11), flagged.** p_rgh rises in the
  flow direction (pressure recovery). Likely the cooling-induced density change /
  buoyancy in that leg or a flow-direction sign convention; INVESTIGATE before
  use — do not feed a negative f to the 1D model.

D_h is measured at ≈21.8 mm on every clean leg (bore area ≈3.7e-4 m², consistent
with the ~21 mm pipe geometry and the mdot face-zone reference).

## Confidence boundaries (read before use)

- Static-gradient vs total-pressure-gradient f differ by <1% here — the dynamic
  head (~0.18–0.36 Pa) is small vs the p_rgh swings (~±20 Pa), so the kinetic
  correction is real but minor at these very low velocities.
- Re / f_lam / excess factor are NaN: `mu(T)` was not supplied (rerun with
  `--mu-pa-s` evaluated at the segment bulk T to populate them). f itself does
  not need Re.
- Coarse mesh (no mesh-independence bound yet — see `compute_gci.py` + protocol).
- Two-station segments (`left_lower_leg`) use a single endpoint gradient — low
  support, flagged.
- `upper_leg` negative f is unresolved (see above).

## Next

1. Provide `mu(T)` per case → Re, f_lam, excess factor.
2. Resolve the `upper_leg` sign / pressure-recovery question.
3. Add intermediate clean stations on two-station segments for a real gradient.
