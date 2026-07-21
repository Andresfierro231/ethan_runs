# Downcomer (`right_leg`) closure analysis — type decision

Date: `2026-06-30` · Owner: claude · Type: read-only analysis (one new note + one
new pure-python helper; no OpenFOAM runs, no edits to existing files)

> **RECOMMENDED CLOSURE TYPE: (a) ordinary forced/mixed straight — admits a
> friction factor f(Re) and (pending an unblock) a Nu(Re,Pr).** The downcomer
> does NOT recirculate: the right_leg interior (TW4/TW5/TW6) shows **0 % backflow
> area and flow alignment 0.99** in all three cases — the opposite of the
> upcomer's 15–33 % backflow. The apparent f is **positive and clean
> (≈1.31 / 1.00 / 0.86)**, not negative like the upcomer. Upcomer and downcomer
> therefore correctly get **different** closures, satisfying the LitRev
> branch-direction policy.

## What was asked / segment map

- Downcomer = CFD span `right_leg` (owner-locked map). It is the cooled
  descending return leg: a bottom DIAGONAL leg from corner **TP2 (0.888, −0.245)**
  → **TP3 (0, 0)**, interior stations **TW4, TW5, TW6**.
- Note on the map: in `build_loop_polyline`, **TP2 is tagged `lower_leg`** (it is
  the lower_leg→right_leg corner), and **TP3 is tagged `right_leg`** (the
  right_leg→left_lower_leg corner at the origin). The right_leg SPAN proper is
  TW4/TW5/TW6; TP2 and TP3 are corner/junction context only.

## Data used (existing reconstructions only; NO OF run)

- Cut-plane secmean dumps (cols `x y z Ux Uy Uz p_rgh rho T`) for TW4/5/6, TP2/3:
  `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13/postProcessing/secmeanSurfaces/<t>/plane_*.xy`
  (times 7915 / 7618 / 10000 for Salt 2 / 3 / 4).
- Apparent friction: `work_products/2026-06-30_claude_segment_friction/segment_friction.json`.
- Thermal duty / block status: `work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_*.json`.
- Upcomer comparison: `work_products/2026-06-30_claude_upcomer_convection_cell/*.json`.
- Negative-friction mechanism note:
  `operational_notes/06-26/30/2026-06-30_upper_leg_negative_friction_investigation.md`.

New helper written for this analysis (pure python, reuses the 0.04 m single-leg
radius mask and the IDENTICAL recirculation-metric defs as the upcomer tool):
`tools/extract/sample_downcomer_recirculation.py` →
`work_products/2026-06-30_claude_downcomer_recirculation/downcomer_recirculation.{json,csv}`.

> **Ra/Ri/Re NOT available for right_leg.** The `convcell` function object that
> writes Ra/Ri/Gr/Re/Pr to cut planes was configured for the UPCOMER spans only
> (it dumped TW7/TW8/TP4/5/6). The right_leg stations exist ONLY in
> `secmeanSurfaces`, which has no nondimensional fields. The recirculation metric
> below is velocity-field-based (does not need Ri); but the downcomer buoyancy
> SCREEN (Ri = Gr/Re²) is unavailable. **NEEDS DATA: re-run the convcell tool
> with right_leg (TW4/5/6) added** — do not run it as part of this analysis.

## 1. Recirculation metric on `right_leg` cross-sections

Metric defs identical to `sample_upcomer_convection_cell.py`:
backflow_area_fraction = fraction of masked faces with u·n̂ < 0 (n̂ = unit mean U);
recirculation_intensity = Σ|u_n|_back / Σ|u_n|_fwd; flow_alignment = |mean U| / mean|U|.

| Case | station | span | backflow | recirc | align | u_bulk (m/s) | T (K) |
|---|---|---|---:|---:|---:|---:|---:|
| Salt 2 | TW4 | right_leg | 0.00 | 0.00 | 0.99 | 0.0137 | 448.8 |
| Salt 2 | TW5 | right_leg | 0.00 | 0.00 | 0.99 | 0.0139 | 452.8 |
| Salt 2 | TW6 | right_leg | 0.00 | 0.00 | 0.99 | 0.0140 | 455.8 |
| Salt 2 | TP3 | (corner) | 0.50 | 0.04 | 0.90 | 0.0092 | 443.6 |
| Salt 3 | TW4 | right_leg | 0.00 | 0.00 | 0.99 | 0.0156 | 461.7 |
| Salt 3 | TW5 | right_leg | 0.00 | 0.00 | 0.99 | 0.0158 | 465.8 |
| Salt 3 | TW6 | right_leg | 0.00 | 0.00 | 0.99 | 0.0160 | 468.8 |
| Salt 3 | TP3 | (corner) | 0.49 | 0.03 | 0.90 | 0.0105 | 456.5 |
| Salt 4 | TW4 | right_leg | 0.00 | 0.00 | 0.99 | 0.0180 | 477.6 |
| Salt 4 | TW5 | right_leg | 0.00 | 0.00 | 0.99 | 0.0182 | 481.3 |
| Salt 4 | TW6 | right_leg | 0.00 | 0.00 | 0.99 | 0.0184 | 484.3 |
| Salt 4 | TP3 | (corner) | 0.49 | 0.03 | 0.90 | 0.0120 | 472.0 |

(TP2, the lower_leg-tagged corner, also shows ~0 backflow except a marginal 0.05
in Salt 4 — not a downcomer-span result.)

**Interpretation.** The right_leg SPAN (TW4/5/6) has **no reversed flow at all**
(backflow = 0, recirc = 0) and is essentially perfectly aligned (0.99) in every
case. This is clean, coherent through-flow. The bulk velocity rises Salt 2→4
(0.0137 → 0.0184 m/s), consistent with the rising loop drive; alignment stays at
0.99 throughout, i.e. no onset of a cell as flow changes.

**Comparison to the upcomer:** the upcomer interior runs **15–33 % backflow**
with alignment dropping to ~0.5 at TP6 (a genuine buoyancy-driven convection
cell, Ri ≈ 64–300 ≫ 1). The downcomer is **categorically different**: 0 %
backflow, 0.99 alignment. There is **no recirculation in the downcomer span.**

The 0.49–0.50 backflow at TP3 is a **corner artifact**, not a leg property: TP3
sits at the origin where right_leg turns into left_lower_leg, so a single mean
direction necessarily splits the junction faces ~50/50. It should not be read as
downcomer recirculation (the three interior stations bracketing it are all 0).

## 2. Apparent friction on `right_leg` (existing output)

From `segment_friction.json` (Darcy f_D, total-pressure-gradient method, n=4 stations):

| Case | apparent f_D | Re | f_lam = 64/Re | f_app/f_lam | flow_align_min |
|---|---:|---:|---:|---:|---:|
| Salt 2 | 1.309 | 63.9 | 1.001 | 1.31 | 0.897 |
| Salt 3 | 0.998 | 85.2 | 0.751 | 0.90 | 0.900 |
| Salt 4 | 0.857 | 116.0 | 0.552 | 0.55 | 0.898 |

**The downcomer f is POSITIVE and physically clean** — a real frictional loss, of
the same order as the laminar reference (f_app/f_lam ≈ 0.5–1.3), and it DECREASES
as Re rises, qualitatively consistent with a f(Re) law. This is the opposite of
the upcomer's negative apparent f (≈ −11 / −8 / −6), which flagged the convection
cell. A single friction factor is therefore meaningful for the downcomer.

**Buoyancy/elevation caveat (does it apply here?).** The negative-friction note
showed that on a NON-horizontal COOLED descending leg, the `p_rgh = p − ρg·y`
hydrostatic removal uses local ρ against absolute y, leaving a `Δρ·g·⟨y⟩` residual
that can swamp the true frictional drop and flip the sign. The right_leg is also a
cooled, non-horizontal (descending in y, from y=−0.245 up toward y=0) leg, so the
caveat MECHANISM applies in principle. **But here it did NOT flip the sign:** f
came out positive and O(f_lam), the elevation span is small (|Δy| ≈ 0.245 m, and
the leg ascends in y toward TP3), and the density change is ~0.2 %. The residual
exists but is sub-dominant to the real loss on this leg. Trust the SIGN and ORDER
of magnitude; do NOT treat the exact f value as closure-grade (coarse mesh, n=4,
section-mean static-vs-total split is indicative).

## 3. Recommended downcomer closure TYPE (ranked)

1. **(a) Ordinary forced/mixed straight: f(Re) + Nu(Re,Pr) — RECOMMENDED.**
   Evidence: 0 % backflow and 0.99 alignment at all three interior stations and
   all three cases; positive clean f that falls with Re. The downcomer behaves as
   coherent through-flow, not a cell. **Data support: strong for the
   no-recirculation finding** (consistent across 3 cases, 3 stations each).
   *Trust:* coarse-mesh, laminar, single-time SEED data — adequate to decide the
   TYPE, not to publish the coefficients.

2. **(b) Mixed-convection with a buoyancy screen — KEEP AS A GUARDED FALLBACK.**
   Buoyancy OPPOSES the descent of cooled fluid here, which is exactly the regime
   that *can* reverse flow (Jackson/Cotton–Axcell). We see no reversal in the
   current Re ≈ 64–116 window, but we have **no per-section Ri for right_leg**
   (convcell didn't cover it), so we cannot prove we are far from the opposing-flow
   reversal threshold. Recommend computing Ri on right_leg and adding a buoyancy
   screen as a GATE on option (a): use f(Re)+Nu while Ri stays below an
   opposing-flow reversal criterion, and revisit if a wider Re/ΔT sweep pushes Ri
   up. *Data support: partial — the screen variable itself is missing.*

3. **(c) Recirculation/convection-cell closure like the upcomer — REJECT.**
   Directly contradicted by the data (0 backflow). Do not mirror the upcomer
   closure onto the downcomer; the LitRev "must not share a closure" policy is
   satisfied precisely because the downcomer is the clean-through-flow branch.

## 4. Downcomer thermal (HTC / UA′) policy block

Current state (`segment_htc_uaprime_*.json`): downcomer (`right_leg`) is
`thermally_blocked: true` with `blocker_B1: false` and
`nu_direct_admitted: false` — i.e. blocked by the **blanket Nu-not-admitted
policy**, NOT by a missing-data blocker. The wall duty is, however, fully
reconstructed: **q_w ≈ −364 W/m²** (Salt 2; negative = heat leaving the fluid =
cooling, physically correct for the return leg), over 3 wall patches, all present.

**Recommendation: UNBLOCK the downcomer thermal closure to the same level the
upcomer/lower_leg are admitted — i.e. report UA′/q_w and a *direct, indicative*
Nu, NOT a fitted Nu(Re,Pr) law.** Justification:
- The OF13 T-reconstruction is now available (T present in every right_leg secmean
  plane; section-mean T rises 449→484 K across cases and falls along the leg as
  expected for a cooled descent), so the data blocker that justified the block is
  resolved.
- The flow is clean through-flow (§1), so a wall-HTC/Nu is physically
  well-posed here (unlike the cell-dominated upcomer, where Nu is not identifiable).
- **Keep the existing global caveats:** coarse mesh / mesh-independence
  UNESTABLISHED (B2), narrow laminar Re band, rad_off → q_r not applicable. Admit
  a *direct* Nu only, flagged indicative, exactly as defended for left_lower_leg.

This is a recommendation; the closure-map policy edit is owner-gated and was not
made here.

## NEEDS MORE ANALYSIS / NEEDS DATA

- **NEEDS DATA (high priority): re-run the convcell function object with right_leg
  (TW4/5/6) added** to obtain per-section Ra/Ri/Gr/Re/Pr for the downcomer. Without
  it the option-(b) buoyancy screen and the opposing-flow reversal margin cannot be
  quantified. (Do not run OF as part of this note.)
- **NEEDS MORE ANALYSIS:** an onset/limit sweep (higher Re and/or larger cooling
  ΔT) to confirm the downcomer does not cross into opposing-flow reversal outside
  the current Re ≈ 64–116 / 3-case window before locking option (a).
- **NEEDS MORE ANALYSIS:** mesh-independence bound (B2) before any downcomer f or
  Nu coefficient is treated as closure-grade rather than seed/indicative.
- Provenance: all numbers are from coarse-mesh, laminar, single-time mainline
  reconstructions; section-mean / single-leg-masked. Treat as SEED evidence for
  the closure-TYPE decision, which is robust; treat coefficients as indicative.

## Provenance / files

- New helper: `tools/extract/sample_downcomer_recirculation.py`
- New outputs: `work_products/2026-06-30_claude_downcomer_recirculation/downcomer_recirculation.{json,csv}`
- This note: `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md`
