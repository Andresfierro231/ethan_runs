# Presentation key items — advisor meeting 2026-07-02

One-pager distilled from the full record. Values > sources. Honest by design:
the advisor prizes transparency/rigor; the "what we don't claim" items are strengths.

## The 3-5 most DEFENSIBLE things to present (each: claim | caveat | next step)
1. **Geometry provenance was wrong; we caught and fixed it.** Rebuilt per-leg geometry
   from mesh PCA: heater is inclined 21.5° (schematic cut it vertical); the lower↔downcomer
   labels were swapped 0.566 m; test-section bore 20.9 mm vs 22.1 mm elsewhere. All closures
   now key on mesh geometry. CAVEAT: coarse mesh. NEXT: mesh-independence bound (below).
   [figs: geometry-swap; T1/T8 journals]
2. **De-buoyed per-leg friction: every leg physical, f/f_lam ≈ 1.0–3.3.** Single-leg p_rgh
   gradient embeds the buoyancy source; a proper streamwise momentum budget (subtract the
   buoyancy source + fix per-leg flow orientation) recovers positive friction on all 6 legs.
   Validated by an independent loop energy closure. CAVEAT: coarse mesh; single time.
   NEXT: mesh GCI to bound it. [fig1_friction_per_leg; T1b journal]
3. **Thermal closures per leg** (patch-based, length-free = most robust): heater HTC ~250–290,
   upcomer ~77–126, downcomer ~43 W/m²K; downcomer Nu ~1.74 (passive); recirculation is
   EXCLUSIVE to the upcomer (19–34% backflow, others 0). CAVEAT: coarse mesh; convective-only.
   NEXT: GCI; downcomer/thermal cross-checks. [fig4 thermal; fig6 recirc; T4/T5 journals]
4. **The predictivity test — the honest headline (overnight controlled study).** Putting the
   CFD closures into the 1D loop does NOT make mdot predictive by itself. The DOMINANT lever
   is the THERMAL boundary: the 1D loop T swings 422→548 K over 0→2 in insulation; CFD's 450 K
   ⇔ ~0.27 in. At CFD-matched T, adding CFD friction makes mdot WORSE (−27%→−49%). So mdot is
   not a robust closure metric; the pressure DISTRIBUTION is (per-leg friction matches CFD by
   construction — we implemented a per-leg friction multiplier). CAVEAT/OPEN: a factor-2 mdot
   gap remains at matched T ("drive too weak" was checked and DISPROVEN — ΔT matches); no
   validated mechanism yet. NEXT: term-by-term loop momentum-budget reconciliation.
   [figA insulation; figB condition-dependent; overnight-synthesis report]
5. **Mesh-independence: concrete plan + honest blocker.** No external meshes available, so we
   self-generate: refineMesh r=2 works geometrically (2.17M→17.3M) but the refined non-conformal
   interface breaks the OF13 stitcher at runtime. FIX: conformal-first remesh (or snappy). NEXT:
   execute conformal-first → first (2-level) GCI. [mesh-self-generation journal; mesh_gci_pipeline.sh]

## Status table
| Item | SOLID | PROVISIONAL | BLOCKED |
|------|-------|-------------|---------|
| Geometry (mesh-true) | ✓ | | |
| Per-leg friction f/f_lam | ✓ (physical, loop-closure-validated) | coarse-mesh error unbounded | |
| Thermal HTC/Nu per leg | ✓ (patch-based) | UA'/q' (length-normalized) | |
| Recirculation (upcomer-only) | ✓ | onset/limit correlation (needs T2 steady) | |
| Bend minor-loss K | | K~6-16 (upper bound; local q_ref) | |
| Per-leg friction multiplier (1D) | ✓ implemented+tested | | |
| Predictivity (mdot) | | closures fix DISTRIBUTION not mdot | factor-2 gap OPEN |
| Mesh-independence (GCI) | | | refineMesh+NCC stitcher; fix=conformal-first |
| Insulation true-steady runs (T2) | | | too slow to finish as configured |

## Ready hard-question answers
- **How many cells?** 2,166,996 (2.17M); 2.27M points, 6.60M faces. Coarse, single level.
- **Is it mesh-independent / discretization error?** Not quantified YET — stated plainly. Plan
  in motion: self-generate finer meshes (refineMesh works geometrically; the NCC interface
  breaks the stitcher → fix is a conformal-first remesh), then a 2-level Richardson/GCI. Until
  then every closure carries an unquantified mesh-error bar; we don't claim otherwise.
- **Converged/steady?** Salt 2/3/4 Jin mainline continuations stationary in flow + gross duty;
  Salt 1 weaker. Perturbation runs were audited and REJECTED as false-steady. The new
  insulation true-steady runs are advancing too slowly to finish as configured (flagged).
- **How do you get friction from a buoyancy-driven loop (why was it negative)?** Single-leg
  p_rgh gradient embeds the buoyancy source; we do a streamwise momentum budget, subtract the
  buoyancy source, and fix each leg's flow orientation → physical f/f_lam ~1–3.3; validated by
  loop energy closure (buoyancy head = friction + minor losses).
- **Do the 3D closures make the 1D model predictive?** Not by themselves (see item 4). They fix
  the pressure distribution; the dominant lever is the thermal boundary; a factor-2 mdot gap is
  open. We tested it in a controlled study and are transparent about what remains.
- **Operating temperature / regime?** CFD bulk ~450 K (177 °C), inside the rig's confirmed
  165–210 °C; laminar, Re ~61–135; natural circulation (no pump). Molten salt, Jin properties.

## Sources
reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/README.md;
reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md;
work_products/2026-07-01_claude_checkpoint_presentation/ (outline, facts_and_qa, closure_summary_table, figs);
work_products/2026-07-02_overnight/ (figA/figB, scripts, RESULTS_LOG); .agent/journal/2026-07-0{1,2}/*.md.
