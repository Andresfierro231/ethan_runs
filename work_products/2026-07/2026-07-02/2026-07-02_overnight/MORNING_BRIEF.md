# MORNING BRIEF — START HERE (2026-07-02)

60-second overnight summary + pointers. Everything is honest + sourced; failures reported as-is.

## What I did overnight (autonomous)
Worked the "do the 3D closures make the 1D model predictive?" question to a rigorous,
honest conclusion, implemented the missing per-leg friction capability, de-risked the
mesh-independence path, and produced a report + figures + updated presentation.

## The 5 headline results
1. **Per-leg friction multiplier IMPLEMENTED** in the 1D model (`friction_multiplier_by_
   parent_segment`, mirrors the HTC path; backward-compatible; tested). It was genuinely
   missing — per-leg HTC existed, per-leg friction did not.
2. **Predictivity, honestly:** injecting CFD closures does NOT make mdot predictive by
   itself. The DOMINANT lever is the THERMAL boundary — the 1D loop T swings 422→548 K over
   0→2 in insulation; CFD's 450 K ⇔ ~0.27 in. Our first-pass "closures help" was an artifact
   of a 60 K-too-hot setting. At CFD-matched T, adding friction makes mdot WORSE. => the
   pressure DISTRIBUTION (not mdot) is the robust closure metric.
3. **Open factor-2 mdot gap** at matched T with CFD friction; "drive too weak" was CHECKED
   and DISPROVEN (ΔT matches). No validated mechanism yet — flagged, not hand-waved.
4. **Mesh self-generation de-risked:** refineMesh r=2 works geometrically (2.17M→17.3M) but
   the refined non-conformal interface breaks the OF13 stitcher at runtime. FIX = conformal-
   first remesh. No GCI fabricated.
5. **T2 insulation runs are too slow** to finish as configured (~22 s sim/hr). Needs a rethink.

## Read in this order
1. `PRESENTATION_KEY_ITEMS.md` (this folder) — the one-pager for the meeting: 5 defensible
   items, a solid/provisional/blocked table, and ready hard-question answers.
2. `reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/README.md` — full synthesis.
3. `work_products/2026-07-01_claude_checkpoint_presentation/` — deck outline + facts_and_qa
   + closure_summary_table + 9 figures (figA/figB = the overnight corrections).
4. `reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md` (§6 = corrections).
5. `RESULTS_LOG.md` (this folder) — chronological log of every overnight run + caveat.
6. Journals: `.agent/journal/2026-07-02/*.md` (per-leg, driver-REVISED, predictivity-
   culminating, mesh-self-generation).

## Top next steps (ranked, to bolster credibility)
1. Match the 1D thermal boundary (effective insulation/ambient-loss) to each CFD case — do
   all closure comparisons there (the dominant lever).
2. Reconcile the loop momentum budget term-by-term (buoyancy-head defn, f(Re), minor-loss ref)
   to explain the open factor-2 mdot gap.
3. Mesh-independence via conformal-first remesh (unblock GCI) — the #1 trust limiter.
4. Fix/redesign T2 so the insulation study can reach steady.

## Reusable tooling created (workflows, not one-offs)
- 1D model: per-leg friction multiplier (solver.py); run_perleg_friction_compare.py,
  matched_closure_compare.py, insulation_sweep[_fine].py, driver_thermal_compare.py,
  make_overnight_figures.py.
- Mesh: mesh_gci_pipeline.sh (encodes every lesson incl. the stitcher blocker), gci_2level.py.
- Everything runs with system python3; figures via matplotlib.

## Honest global caveats
Coarse-mesh CFD (no GCI bound yet); laminar; single time per case; 1D "matched" = matched
effective insulation, not identical BC form; the factor-2 mdot gap has no validated mechanism
yet. Nothing was fabricated.
