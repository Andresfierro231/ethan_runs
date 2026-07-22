# Overnight results log — 2026-07-01/02

Every run: inputs, outputs, caveats. Updated by the autonomous loop.

- [17:35 CDT] Setup. per-leg comparison PID 3453674; mesh de-risk agent launching; T2 too slow (documented in OVERNIGHT_PLAN.md).

## AGENT-171 — mesh self-generation + GCI de-risk (T6)
(Prompt said AGENT-169, but 169+170 already claimed by codex; took AGENT-171.)
Env: c318-008, T2=128 foamRun procs (verified `ps`), ~128 free, 445G RAM free. OF13 native (of13_env.sh, libRCWallBC.so).
Clone: tmp/2026-07-02_mesh_gci/coarse_clone (constant deref 439M, 7915 deref 302M incl T, system=run config solver=fluid+libRCWallBC.so+createNonConformalCouplesDict[10 couples]).
- [~17:50] STEP 1 checkMesh coarse: **Mesh OK**. nCells=2,166,996 (exact match), pts 2,268,735, faces 6,598,756. 109 patches=69 wall+20 nonConformalCyclic+20 nonConformalError. nonOrtho max 45.12/avg 7.51, skew max 1.22, AR max 10.48. Log: checkMesh_coarse.log
- [~17:55] STEP 2 refineMesh de-risk starting.
- [17:56] `refineMesh -all -overwrite` EXIT 0 (~1.5 min serial). Wrote refined mesh to constant/polyMesh.
  Refined **nCells=17,335,968 = 2,166,996 × 8 EXACTLY** (clean uniform octree, r=2 linear). nPoints 17,734,972, nFaces 52,398,976.
  Min edge length HALVED (x-aligned 1.56e-4 → 6.06e-5) → confirms 1st BL cell halves → y+ ~halves, as intended.
  Boundary preserved 20 nonConformalCyclic + 20 nonConformalError + 69 wall (refineMesh kept NCC patch structure).
  CAVEAT: refineMesh -overwrite wrote ONLY the mesh; it did NOT map the 7915 fields (T/U/p_rgh still 2,166,996 values
  → mesh/field mismatch). Fine RUN + dry-run must (re)initialize fields on the fine mesh (mapFields from coarse, or setFields).
- [~18:00-18:40] checkMesh on refined 17.3M mesh (serial, both plain and -allTopology): topology ALL OK
  (boundary def OK, addressing OK, zip-up OK, face-face OK; 17,335,968 cells, 100% hexahedra, 109 patches,
  4 face zones, 33 cell zones preserved). BUT the GEOMETRY phase ran >30 min single-threaded with no output
  and did not complete → checkMesh serial on 17.3M cells + coupled patches is impractically slow.
  FINDING: the `couple*_on_*` nonConformalCyclic overlay patches have nFaces=0 in BOTH coarse and fine
  (they are runtime/utility-populated overlays; the coarse mesh passed checkMesh fast WITH them empty, so
  empty overlays are normal). The base `ncc_*` interface patches refined correctly (e.g.
  ncc_junction_lower_left_right_end 576 → 2304 faces = 4× interface refinement). So the fine slowness is the
  raw 8× cell count in serial geometry loops, not a couple defect per se.
  DECISION: killed only MY checkMesh procs (T2's 128 foamRun VERIFIED still running, untouched); switch to
  (a) rebuild couples with createNonConformalCouples, (b) map fields coarse→fine, (c) do checkMesh + the
  solver dry-run in PARALLEL (decomposed) which is far faster than serial on 17M cells.
- [18:17] **createNonConformalCouples -overwrite EXIT 0 — KEY DE-RISK SUCCESS.** All 10 couples rebuilt on the
  refined interface. Per-couple metrics (excellent): source coverage avg **0.99** (target 1.0), openness ~**1e-16**,
  match error ~**1e-13**, angle 0; ~14,500-18,900 couplings/couple in ~0.1-0.2 s each. Each interface 2304 faces
  (= 4× coarse 576). fvMeshStitcher connected them: cell openness ~4e-17, projected-volume-fraction ~9e-14 → clean.
  => refineMesh(r=2) + createNonConformalCouples WORKS on this NCC-assembled mesh. Log: ncc_fine.log
- [18:20-18:27] mapFields coarse→fine field init: hit obstacles, resolved:
  (1) `cellVolumeWeight` unsupported in this build → use `interpolate`/`mapNearest`;
  (2) `interpolate` + `mapNearest` both SIGFPE core-dumped in `fvMeshStitcher::unconform → mag(surface vector)`
      — the REFINED NCC interface has benign zero-area sliver faces (the ORIGINAL coarse run stitched fine under
      SIGFPE-on, so this is refinement-induced). OF gates the trap on env-IS-DEFINED; must `unset FOAM_SIGFPE`
      (=false is insufficient). Applies to foamRun too.
  (3) mapFields FATAL "size 2166996 != 17335968" reading the STALE coarse-sized field files left by refineMesh
      → move them aside so mapFields creates fresh. 
  **mapFields mapNearest (FPE untrapped, clean target) EXIT 0** — fine mesh now has consistent 17,335,968-value
  T/U/p_rgh/rho. (mapNearest = exact for octree children.) Some "no valid tet decomposition" warnings on the
  refined interface faces (same sliver faces; benign for the run). Log: mapfields_fine4.log
- [18:27] decomposePar fine mesh to 64 ranks (scotch) running → then PARALLEL checkMesh + tiny-endTime foamRun dry-run.

- [18:29 CDT] PER-LEG FRICTION predictivity done. mdot: default +30/+34/+40%, global-mean -3 to -5%, per-leg -10% (S2/3/4). Per-leg length-weights the long high-f legs (heater/downcomer/cooler 2.2-3.3x) -> more resistance -> lower mdot; global-mean closeness is partly fortuitous. Residual is DRIVER-side (Re ~2.3x CFD even with correct friction). Value of per-leg = pressure DISTRIBUTION (per-segment ΔP matches CFD by construction). Journal: .agent/journal/2026-07-02/per-leg-friction-implementation-and-predictivity.md. Fig: fig4_perleg_vs_global_mdot.png.
- [18:29 CDT] DRIVER diagnosis (checked numerically): 1D salt_current mu is ~25% HIGHER than CFD Jin mu (ratio Jin/1D 0.77-0.82); salt_kirst is close (0.87-0.98). So viscosity is NOT the Re-2.3x cause (higher mu -> lower Re, opposite). To get pred Re~154 at pred mdot, 1D mu must be evaluated at ~510K vs CFD bulk 447K -> the 1D loop runs HOTTER / different ΔT. => driver mismatch is THERMAL, not viscosity. Actionable consistency item: use Jin mu in 1D to match the CFD closures' property basis (~25%). NEXT: pull the 1D solve's loop ΔT/mean-T/duty vs CFD to localize the thermal driver.
- [18:29 CDT] Mesh de-risk (AGENT-169) progressing: staged clone, refineMesh, createNonConformalCouples, checkMesh, decompose, mapFields all ran. NCC regeneration appears to work. Still running (fine-mesh solve).

### AGENT-171 (continued) — de-risk VERDICT (~18:45)
- refineMesh(r=2) → 17,335,968 cells (exact 8×, 100% hex). createNonConformalCouples on refined interface EXIT 0,
  coverage 0.99 / openness 1e-16 — couples geometrically valid. mapFields mapNearest (unset FOAM_SIGFPE, clean
  target) gave consistent 17.3M fields.
- **BLOCKER: the REFINED non-conformal interface breaks OF13 fvMeshStitcher at run time, two ways:**
  (1) decomposePar FATAL `(56 54) not found in table` (couple split across incompatible procs; preservePatches
      constraint did NOT fix); (2) serial foamRun **SIGSEGV** in `fvMeshStitcher::applyOwnerOrigBoundaryEdgeParts →
      edgeFaces()` after cleanly stitching all 10 couples ("0/NNNN small couplings removed"). Coarse mesh does
      neither (original run stitches+decomposes fine) → refining the NCC ASSEMBLY interface is the failure point.
- **NO GCI produced** (correctly not fabricated). Steps 1-2 validated; Step 3 solver dry-run failed at the stitcher.
- Now confirming the COARSE clone runs (baseline) to prove clone/env/custom-BC are correct and isolate the refined
  interface as the sole cause. RECOMMENDED FIX for a runnable fine mesh: merge legs to a CONFORMAL mesh then refine
  (no NCC to break), or refine INTERIOR-only away from the couple faces, or snappy a fresh conformal mesh (Approach B).
  Full detail + next steps: .agent/journal/2026-07-02/mesh-self-generation-gci.md. Pipeline: mesh_gci_pipeline.sh.
- [18:29 CDT] T2 still crawling (8072->8097 in ~1h). Not waiting.

- [~19:15 CDT] MESH DE-RISK (AGENT-171) COMPLETE — honest verdict: refineMesh -all (r=2) works GEOMETRICALLY (2.17M->17.34M cells exact x8, BL first cell halved; createNonConformalCouples regenerates all 10 couples at 0.99 coverage). BUT the refined non-conformal interface BREAKS OF13 fvMeshStitcher at RUNTIME: parallel decomposePar FATAL "(56 54) not found in table"; serial foamRun SIGSEGV in fvMeshStitcher::applyOwnerOrigBoundaryEdgeParts. Coarse mesh runs fine (custom BC constructs, residuals finite) -> the NCC interface refinement is the sole failure. NO GCI produced (not fabricated). FIX PATH: conformal-first (merge legs/drop NCC -> refineMesh -> run, no stitcher), OR interior-only refine away from couple faces, OR snappy conformal rebuild (Approach B). Also stage clones from ORIGINAL DECOMPOSED processors (consistent p_rgh) not the reconstructed recon. Reusable: mesh_gci_pipeline.sh, gci_2level.py (Fs=3.0). Journal: .agent/journal/2026-07-02/mesh-self-generation-gci.md.

- [18:50 CDT] DRIVER THERMAL COMPARE (key finding): the 1D loop runs ~62-66 K HOTTER than CFD (S2 1D 512K vs CFD 450K; S3 527 vs 464; S4 545 vs 479), with smaller ΔT (8.2 vs 12.1 K). This EXPLAINS the Re ~2.3x (hotter -> lower mu -> higher Re) and confirms the dominant mdot error is THERMAL/driver-side, NOT the friction closures. 1D 512K=239C is ABOVE the rig's 165-210C range. Likely under-predicted total heat loss (UA too low). CAVEAT: assumes 1D scenario BCs match each CFD case; NEXT match BCs to isolate model-error from setup-mismatch. Journal: .agent/journal/2026-07-02/driver-side-thermal-overheat-finding.md.

- [19:21 CDT] Wake 3 (Phase 1): scenario-BC matching for the 60K driver finding. CONFIRMED 1D Salt 2 heater_power_W=265.7 MATCHES CFD (265.7). Differences to probe: 1D adds +37W test-section power; 1D uses "1.0in insulation" param vs CFD's wall-h insulation; ambient 300K. Launched insulation_sweep.py (Salt 2, ins 0/1/2/3in x rad) to see which insulation setting reproduces the CFD loop T~450K -> if one does, the 60K is a setup/insulation mismatch, not a model error (decisive for the driver interpretation). Background PID 3582282.

- [20:08 CDT] Wake 4 (Phase 1): INSULATION SWEEP -> REVISED driver finding (major correction). 1D loop T is EXTREMELY insulation-sensitive (422->512->548K over 0->1->2in); CFD 450K is BRACKETED between 1D's 0in and 1in. So the "60K over-heat / Re 2.3x" was measured at an ARBITRARY ins=1.0in and is DOMINATED by a BC mismatch, NOT a model defect. Interpolated to matched T=450K: 1D mdot ~0.0095-0.0105 (-20 to -28%), Re ~104-116 (ratio 1.5-1.7x, DOWN from 2.3x). CRITICAL: all prior predictivity numbers (default +27%, per-leg -10%) were at ins=1.0in (60K too hot) -> they CONFLATE closure error with insulation over-heat. The closure comparison MUST be redone at CFD-matched insulation. Journal: driver-finding-REVISED-insulation-sensitivity.md. Launched insulation_sweep_fine.py (0.25-0.75in) to pin the matched insulation (PID 3631962). CAVEAT: coarse 0->1in interpolation is approximate.

- [20:56 CDT] Wake 5 (Phase 1): FINE insulation sweep PINS the CFD-matched insulation. CFD T=450.3K <-> ~0.27in (0.25in->446.9K, 0.375in->465.4K). At matched T (default closures): 1D mdot ~0.0099 (-25%), Re ~53 (UNDER CFD 68, ratio 0.78). So at CFD-matched thermal conditions the 1D UNDER-predicts mdot -> adding CFD friction (higher f) would push mdot LOWER (worse). KEY COUPLING INSIGHT: whether closures "help" mdot is CONDITION-DEPENDENT — at ins=1.0in (hot) default over-predicts +27% so friction helps; at matched-T default under-predicts -25% so friction hurts. => mdot is NOT a robust closure-quality metric; the per-segment pressure DISTRIBUTION is (per-leg matches CFD by construction regardless of thermal condition). Launched matched_closure_compare.py (ins 0.25/0.375 x default/global/per-leg) PID 3678352.

- [21:43 CDT] Wake 6 (Phase 1): matched-insulation closure comparison + drive check + f/f_lam(Re). At CFD-matched T (ins 0.25-0.375in): adding CFD friction makes mdot WORSE (default -27% -> per-leg -49%); loop ΔT MATCHES CFD (12.1K) and 1D buoyancy head (56Pa) is NOT smaller -> "drive too weak" DISPROVEN. Residual = factor-2 mdot gap (1D 0.0068 vs CFD 0.0132 at matched T w/ CFD friction) = OPEN momentum-balance discrepancy. f/f_lam is Re-DEPENDENT (4/6 legs rise with Re; downcomer 2.19->3.26 over Re61-118); extrapolated to Re35 the multipliers drop ~10-30% -> PARTIAL contributor to over-friction, NOT the full factor-2. Culminating journal: predictivity-culminating-diagnosis.md. Honest: no validated mechanism for the factor-2 yet; next = full term-by-term CFD-vs-1D momentum budget + f(Re) reconciliation.

- [22:34 CDT] Wake 7 (Phase 1->consolidation): built reusable make_overnight_figures.py -> figA_insulation_sensitivity.png (1D loop T vs insulation, CFD 450K<->~0.27in, shows the ins=1.0in +60K artifact) + figB_condition_dependent_closure.png (mdot err at hot ins=1.0 vs matched ins=0.25 across default/global/per-leg -> closure benefit condition-dependent). Predictivity thread fully documented + figured. NEXT: draft Phase 2 overnight-synthesis report + update presentation package with corrected story.

- [23:21 CDT] Wake 8 (Phase 2 early): wrote comprehensive overnight-synthesis report reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/README.md — exec summary + per-leg friction + corrected predictivity + thermal-boundary sensitivity + mesh de-risk(blocked+fix) + T2-slow + ranked next-steps + global confidence boundaries + artifact index. NEXT: update presentation package (outline + facts_and_qa) with corrected predictivity story; then Phase 3 distillation at 07:00.

- [00:08 CDT] Wake 9 (Phase 2): UPDATED presentation package with the CORRECTED predictivity story. facts_and_qa "did closures help?" rewritten (thermal boundary dominant; condition-dependent closure benefit; distribution robust; factor-2 open). Outline slides C-E rewritten (figA insulation-sensitivity, figB condition-dependent). Copied figA/figB/fig4 into the presentation folder (9 PNGs total). Presentation now leads with the honest overnight correction. NEXT: Phase 3 (07:00) — distill 3-5 key defensible items + what's-solid/provisional/blocked one-pager + hard-question answers (can start ahead).

- [00:56 CDT] Wake 10 (Phase 3 early): wrote PRESENTATION_KEY_ITEMS.md (5 defensible items + solid/provisional/blocked table + hard-Q answers) and MORNING_BRIEF.md (START HERE: 60-sec summary + read-order + ranked next-steps + reusable-tooling index). Verified all 9 presentation figures exist + package self-consistent. ALL MAJOR DELIVERABLES COMPLETE (analysis, synthesis report, model-form report, presentation package, figures, key-items, morning brief, thorough journals). Winding loop to longer cadence for a final morning readiness check; no more substantive work pending (mesh blocked=conformal-first; T2 too slow; analysis done).
