# Weekly checkpoint — proposed outline & <2 h build plan (2026-07-01)

Theme: "This week we corrected the 3D→1D closure pipeline's geometry provenance and
produced a self-consistent, honestly-bounded hydraulic + thermal closure set for the
Salt Jin family — and we're explicit about what is not yet trustworthy."
Audience values TRANSPARENCY, RIGOR, HONESTY. Every quantitative slide cites its
source artifact; a dedicated "what we don't trust yet" slide is a feature, not a risk.

## Slides (RESULTS-FIRST ordering — emphasis = the closure deliverables)
1. **Title / one-line status.** Delivered this week: a self-consistent per-leg
   hydraulic + thermal closure set for Salt 2/3/4 Jin (the 1D-model inputs), on
   mesh-corrected geometry. Mesh-independence + true-steady insulation runs in progress.
2. **The deliverable.** Natural-circulation molten-salt loop; the 1D model needs, per
   leg: friction f, minor-loss K, wall HTC/Nu, recirculation. Here they are.
3. **HEADLINE — friction per leg [FIG1].** f/f_lam ≈ 1.0-3.3, every leg physical,
   across Re 61-135. (One line on method: computed from a streamwise momentum budget
   that separates buoyancy from friction — details in backup.)
4. **Minor-loss K [FIG3].** Corner K ~6-16, Re-dependent (K~C/Re+K_inf) → the 1D model
   needs K(Re), not textbook high-Re constants. Test-section connector folds into the
   upcomer cell (recirc zone).
5. **Thermal per leg [FIG4].** Wall HTC: heater ~250-290, upcomer ~77-126, downcomer
   ~43 (passive). Nu: upcomer 3.1-5.0, downcomer ~1.74. HTC/Nu are length-free & most
   robust; UA'/q' length-corrected via mesh geometry.
6. **Recirculation [FIG6].** Convection cell EXCLUSIVE to the upcomer (backflow 19-34%);
   heater/downcomer/cooler zero → downcomer modeled as an ordinary f(Re)+Nu leg.
7. **Validation — loop energy closure [FIG2].** Independent check: buoyancy head
   (41-45 Pa) = straight friction (57-70%) + bend minor losses (30-43%). The closure
   set is internally consistent (this is why we trust the friction numbers).
8. **How we know the geometry is right [FIG5].** Brief rigor backing: we rebuilt leg
   geometry from mesh PCA after catching a schematic-CSV bug (heater cut vertical;
   lower↔downcomer label swap, 0.566 m) — now fixed. Supports every number above.
9. **What we DON'T trust yet (honesty slide).** No mesh-independence bound YET
   (concrete plan on the next slide); perturbation runs false-steady (audited &
   rejected); coarse mesh (2.17M cells); dimensionless-group definition offsets flagged.
9.5 **Mesh-independence: our plan (preempts "is it mesh-converged?").** The pre-built
    finer meshes / generator aren't available to us, so we SELF-GENERATE from the
    existing mesh with the OF13 tools we already run. This week: (1) uniform refineMesh
    r=2 → 17.3M cells, exact geometry, BL first-cell halved, regenerate non-conformal
    couples; (2) run coarse+fine → 2-level Richardson/GCI (calculator built & tested)
    on mdot/f/Nu/y+; (3) cheap refineWallLayer wall-sensitivity in parallel; (4) if a
    3-level observed-order GCI is needed, independent snappyHexMesh rebuild. Honest:
    2-level = assumed-order (weaker than 3-level) but a real first bound vs the current
    none. First de-risk: couple regeneration on a clone. (checkpoint.md)
10. **Asks / next.** (a) Mesh-independence bound landing this week via self-generated
    meshes (above) — reduces the #1 trust limiter without external dependency.
    (b) True-steady insulation runs finishing → enables the upcomer onset correlation.
    (c) [if useful] confirm with the group whether an independent finer mesh can be
    sourced to strengthen the GCI to 3 levels.

(Rationale: results-first per the emphasis choice. Slides 3-6 are the deliverables;
7-8 are the "why you can trust them" backing; 9-10 are the honest boundary + asks.)

## MAJOR SECTION (professor-priority) — "Do the 3D closures make the 1D model predictive?"
Insert as slides 6.5-6.9 (right after the closures, before the loop-closure validation).
This is the 3D-closure-into-1D TRIAL: put the CFD-measured f and K into the 1D loop
model (tamu_loop_model_v2) and score its predictions vs CFD. Being produced by the
predictivity-trial lane (work_products/2026-07-01_claude_1d_predictivity_trial/).

- Slide A — "The test." 1D loop model, driven by buoyancy head, resisted by friction
  (major) + bend/fitting minor losses. We inject CFD-measured closures and ask: does
  it predict loop mdot and the per-segment pressure drops?
- Slide B — "What's been the gap." The 1D model's DEFAULT loss coefficients are
  textbook high-Re values (k_90deg=1.0, k_20deg=0.10, major mult=1.0), but at this
  regime (Re 61-135) the CFD says corner K ~6-16 and f/f_lam ~2-3.3. ~10x gap.
  [CORRECTED overnight — the honest, controlled story replaces the first-pass verdict:]
- Slide C — "The control that matters: thermal boundary [figA_insulation_sensitivity.png]."
  The 1D loop T is EXTREMELY insulation-sensitive (422→512→548 K over 0→1→2 in); CFD's
  450 K ⇔ ~0.27 in. Our first-pass predictivity ran at ins=1.0in = loop ~60 K too hot, so
  any mdot comparison there conflated closure error with a thermal-setting artifact. Lesson:
  match the thermal boundary to CFD before judging closures.
- Slide D — "Closure benefit is condition-dependent [figB_condition_dependent_closure.png]."
  At the hot setting, adding friction "helps" mdot; at CFD-matched T it HURTS (default −27%
  → per-leg −49%). => mdot is NOT a robust closure metric. The robust one is the per-segment
  pressure DISTRIBUTION: per-leg friction matches CFD by construction (we implemented a
  per-leg friction multiplier), while a single global multiplier over-predicts low-loss legs
  +96% to +400%.
- Slide E — VERDICT (honest, professor-facing): (1) The DOMINANT lever for a predictive 1D
  loop is the THERMAL boundary (effective insulation/ambient-loss), not the hydraulic
  closures. (2) The CFD closures are physically sound and fix the pressure DISTRIBUTION, but
  do NOT make mdot predictive by themselves. (3) An OPEN factor-2 mdot gap remains even at
  matched T with CFD friction ("drive too weak" was checked and DISPROVEN — ΔT matches);
  no validated mechanism yet (partial: f/f_lam is Re-dependent). (4) Ranked fixes: match
  thermal BC → reconcile the loop momentum budget term-by-term → per-leg friction (distribution)
  → mesh-independence bound. Caveats: coarse mesh (GCI pending; self-gen blocked at the NCC
  stitcher, fix=conformal-first), laminar, single time.
  Full analysis: reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/ + .../2026-07-01_model_form_comparison/.

STATUS: DONE + CORRECTED overnight. Figures: figA_insulation_sensitivity.png,
figB_condition_dependent_closure.png, fig4_perleg_vs_global_mdot.png (in this folder),
plus the earlier fig1-3 in work_products/2026-07-01_claude_1d_predictivity_trial/.
The overnight correction (thermal boundary dominates; closures don't fix mdot; factor-2 open)
is the scientifically honest headline — lead with it.

## Figures (DONE, in this folder)
- fig1_friction_per_leg.png · fig2_loop_budget.png · fig3_corner_K.png · fig4_thermal_htc.png
- Backing tables: work_products/2026-07-01_claude_{momentum_budget,bend_minor_loss,thermal_downcomer,allspan_convection}/*.csv

## What is achievable in <2 h (all ASSEMBLY of existing, validated results — no new compute)
- [DONE] 4 figures from this session's work_products.
- [DONE] facts + anticipated-Q&A sheet (checkpoint_facts_and_qa.md).
- [OPTIONAL, ~20 min] geometry before/after figure (heater 21.5° vs schematic vertical)
  from mesh_stations — a strong "we found the bug" visual for slide 3.
- [OPTIONAL, ~20 min] recirculation figure: backflow fraction per leg (slide 8) from
  the allspan_convection CSVs.
- [OPTIONAL, ~15 min] one-page provenance/co-location table graphic (slide 3).
- NOT achievable in 2 h and NOT to be faked: any mesh-independence / GCI number
  (blocked on finer meshes), any converged insulation-run result (still running).

## Honesty guardrails for the talk
- Lead with the limitation slide's content if asked "is this final?" — it isn't; these
  are coarse-mesh closures with the mesh-error bar still open.
- If asked for a single trust level: HTC & Nu (patch-based, length-free) are the most
  robust; f and K are physically sound but carry the coarse-mesh caveat; the upcomer
  correlation is seed-stage.
