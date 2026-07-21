# Overnight synthesis report — 2026-07-01/02 (autonomous)

Owner: claude (autonomous overnight run). Audience: the advisor meeting + the project
record. Every quantitative claim cites a dated artifact. Transparency, rigor, honesty
are the priority; caveats are stated inline and next-steps are ranked at the end.

## 0. Executive summary (what changed overnight)
Focused on the "3D-closures-into-1D → is it predictive?" question and the mesh-
independence blocker. Net result: the picture is now HONEST and well-characterized —
and it is NOT the simple "inject CFD closures → predictive 1D" story.
1. **Per-leg friction multiplier implemented** in the 1D model (was missing; HTC per-leg
   existed, friction did not). Backward-compatible, tested.
2. **Predictivity, corrected:** the earlier "closures help mdot" result was an ARTIFACT of
   running the 1D at an insulation setting that made the loop ~60 K too hot. At a CFD-matched
   temperature the closures do NOT improve mdot — they make it worse. Closure benefit on mdot
   is condition-dependent; the pressure DISTRIBUTION is the robust closure metric.
3. **Dominant 1D error is the THERMAL BOUNDARY, not the closures:** the loop temperature is
   extremely sensitive to insulation/ambient-loss (422→548 K over 0→2 in); CFD 450 K ⇔ ~0.27 in.
4. **An open factor-2 mdot discrepancy** remains even at matched temperature with CFD friction
   — flagged honestly, no mechanism asserted.
5. **Mesh self-generation de-risked:** uniform refineMesh works geometrically but the refined
   non-conformal interface breaks OF13's mesh stitcher at runtime; the fix is a conformal-first
   remesh. No GCI fabricated.
6. **T2 insulation runs are too slow to finish** (~22 s sim/hr vs ~25,000 s needed) — flagged.

## 1. Per-leg friction multiplier (1D model)
- The 1D model already computed distributed friction per-segment (f=64/Re_local, segment D_h)
  and had a per-parent-segment INTERNAL-HTC multiplier — but NO direct per-leg FRICTION
  multiplier (only a single global major_loss_multiplier + a profile-descriptor shape model).
- ADDED `ScenarioConfig.friction_multiplier_by_parent_segment` (mirrors the HTC dict; empty ⇒
  1.0, backward-compatible), applied via the existing `_multiplier_from_mapping`. Smoke-tested
  (baseline 1.0, per-leg 2.67 applied); fast tests pass.
- Value: makes each leg's friction match the CFD f/f_lam by construction, so the per-segment
  ΔP errors a single global multiplier produces (+96% to +400% on low-loss legs) collapse.
- Journal: .agent/journal/2026-07-02/per-leg-friction-implementation-and-predictivity.md.

## 2. Predictivity — the corrected story (headline)
Method: inject CFD per-leg friction (T1b f/f_lam) into the 1D loop solver; compare loop mdot &
per-segment ΔP to CFD, CONTROLLING the thermal boundary.
- At the arbitrary ins=1.0in scenario (loop ~60 K too hot): default +27%, per-leg −10% (mdot).
- At CFD-MATCHED insulation (~0.25-0.27 in, loop T≈450 K, ΔT 12.1 K = CFD): default −27%,
  global-mean −46%, per-leg −49% (Salt 2). i.e. adding CFD friction at matched T makes mdot WORSE.
- Therefore whether closures "help" mdot is CONDITION-DEPENDENT (help when over-hot/over-
  predicting; hurt when matched/under-predicting). mdot is NOT a robust closure-quality metric.
- The per-segment ΔP DISTRIBUTION is robust: per-leg friction matches CFD by construction; a
  single global multiplier over-predicts the low-loss legs (test-section +96%, upper-upcomer
  +282-400%) regardless of thermal state.
- OPEN factor-2: at matched T with CFD friction, 1D mdot ≈ 0.0068 vs CFD 0.0132 (Re 35 vs 68).
  "Drive too weak" DISPROVEN (loop ΔT matches; 1D buoyancy head ≈56 Pa not < CFD ~45 Pa). Residual
  is a momentum-balance / friction-reference discrepancy. Partial contributor: f/f_lam is
  Re-dependent (4/6 legs rise with Re) → Re-68 multipliers over-estimate friction at the 1D's
  Re-35 by ~10-30%, but that alone does not explain the factor of 2. NO validated mechanism yet.
- Figures: figA (insulation sensitivity), figB (condition-dependent closure). Journals:
  predictivity-culminating-diagnosis.md, driver-finding-REVISED-insulation-sensitivity.md.
  Full model-form comparison + §6 overnight corrections:
  reports/2026-07/2026-07-01/2026-07-01_model_form_comparison/README.md.

## 3. Thermal-boundary sensitivity (the dominant lever)
- 1D loop mean T vs insulation: 0.0in→422 K, 1.0in→512 K, 2.0in→548 K (rad on). CFD 450 K is
  bracketed at ~0.27 in. So matching the effective insulation/ambient-loss to CFD is the single
  most important thing for a predictive 1D loop — more than the hydraulic closures.
- CAVEAT: the 1D "insulation thickness" is a model parameterization, not the CFD's wall-h
  boundary; "matched" = matched loop T / effective UA, not identical BC form. rad on/off is a
  second strong lever (rad-on ins-0 nearly stalls the loop).

## 4. Mesh self-generation for mesh-independence (T6) — de-risked, blocked, fix identified
- refineMesh -all (r=2): 2.17M→17.34M cells (exact ×8; BL first cell halved). createNonConformal-
  Couples regenerates all 10 couples (0.99 coverage). checkMesh OK.
- BLOCKER: the refined non-conformal interface breaks OF13 fvMeshStitcher at RUNTIME (parallel
  decomposePar FATAL; serial foamRun SIGSEGV). The coarse mesh runs fine → the NCC interface
  refinement is the sole failure. NO GCI produced (correctly not fabricated).
- FIX PATH: make the mesh CONFORMAL first (merge legs / drop NCC → refine → run, no stitcher),
  or interior-only refine away from couple faces, or snappy a fresh conformal mesh. Stage clones
  from the ORIGINAL DECOMPOSED processors (p_rgh fidelity), not the reconstructed recon.
- Reusable: work_products/2026-07-02_overnight/mesh_gci_pipeline.sh + gci_2level.py.
  Journal: .agent/journal/2026-07-02/mesh-self-generation-gci.md.

## 5. T2 insulation runs — too slow (flag)
Advancing ~22 s of sim time per wall-clock hour vs ~25,000 s needed to reach the endTime;
they will not reach steady this week as configured. Left running (not killed). Needs a bigger
timestep / acceleration / rethink. The upcomer onset correlation (T10) stays blocked on this.

## 6. Ranked next steps to bolster credibility
1. **Match the 1D thermal boundary to each CFD case** (effective insulation / ambient-loss UA)
   as the standard predictive condition — the dominant lever; do all closure comparisons there.
2. **Reconcile the loop momentum budget term-by-term** (CFD vs 1D at matched T): buoyancy-head
   definition, f(Re) not a constant multiplier, minor-loss reference — to explain the factor-2.
3. **Mesh-independence via conformal-first remesh** (unblock T6) → a real discretization-error
   bound; everything above rests on coarse-mesh CFD until then.
4. **Fix T2** (timestep/acceleration) or redesign the insulation study so it can reach steady.
5. Per-leg friction is landed; use it for the pressure DISTRIBUTION, not as an mdot fix.

## 7. Confidence boundaries (global)
Coarse-mesh CFD (no GCI bound yet); single time per case; laminar; 1D "matched" is via effective
insulation not identical BC form; interpolations across the coarse insulation grid are approximate;
the factor-2 mdot discrepancy has NO validated mechanism yet. None of the overnight numbers were
fabricated; every failure (mesh stitcher, T2 slowness) is reported as-is.

## 8. Artifact index
- Scripts (reusable): work_products/2026-07-02_overnight/{insulation_sweep,insulation_sweep_fine,
  matched_closure_compare,driver_thermal_compare,make_overnight_figures}.py, mesh_gci_pipeline.sh,
  gci_2level.py; work_products/2026-07-01_claude_1d_predictivity_trial/{run_perleg_friction_compare,
  make_perleg_figure}.py.
- Data/figures: work_products/2026-07-02_overnight/*.{json,png,log}; .../2026-07-01_claude_1d_predictivity_trial/*.
- Journals: .agent/journal/2026-07-02/*.md; running log work_products/2026-07-02_overnight/RESULTS_LOG.md.
- Code change: cfd-modeling-tools/.../tamu_loop_model_v2/solver.py (friction_multiplier_by_parent_segment).
