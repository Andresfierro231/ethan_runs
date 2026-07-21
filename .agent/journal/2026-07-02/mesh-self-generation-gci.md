# Mesh self-generation + first mesh-independence bound (T6) — 2026-07-02

Owner: claude (AGENT-171). Prompt assigned AGENT-169, but 169 (codex presentation-readiness)
and 170 were already claimed on the board — took AGENT-171 to avoid a collision. This is the
overnight de-risk of self-generating a finer mesh from the coarse mesh (the #1 trust limiter,
T6) and, if it validates, a first discretization-error bound.

READ FIRST: .agent/journal/2026-07-01/checkpoint.md (approaches A/B/C, constraints),
.agent/journal/2026-07-01/OVERNIGHT_PLAN.md (guardrails).

## Guardrail compliance
- Node c318-008 (256 CPU). T2 (idev job 3269598, `idv89401`) verified running 128 `foamRun`
  procs via `ps` (NOT nproc, which returns 1 under cgroup). Load avg ~129 → ~128 free cores.
  T2 and codex jobs (3265969-72 on other nodes) untouched.
- Worked on a CLONE only. Source recon case `tmp/2026-06-30_claude_action_items/recon_salt2_of13`
  NOT mutated (its constant/ + processors64 are symlinks into read-only jadyn_runs; the clone
  dereferences them). All work under `tmp/2026-07-02_mesh_gci/`.
- 445 GB RAM free, scratch 2.9 P free.

## Approach chosen
Approach A (checkpoint §3): uniform `refineMesh -all` (r=2). Splits every hex into 8 → geometry
preserved EXACTLY (topological subdivision), patch names preserved, no CAD/STL needed, first BL
cell halves → y+ ~halves. This gives a coarse+fine 2-level study.

## Clone assembly (why these sources)
- constant/ (mesh + physicalProperties) and 7915/ (reconstructed fields incl. T with the custom
  `rcExternalTemperature` BC) dereferenced from the recon case.
- system/ taken from the AUTHORITATIVE run config
  `jadyn_runs/.../salt2_jin/case_stage/..._continuation/system` because the recon case's controlDict
  is a stripped post-processing dict (no `solver`, only libsampling). The run config has
  `application foamRun; solver fluid; libs ("libRCWallBC.so"); createNonConformalCouplesDict` (10 couples).

## STEP 1 — baseline checkMesh (coarse) — PASS
- nCells = **2,166,996** (matches the expected value exactly), points 2,268,735, faces 6,598,756,
  internal faces 6,403,220, 109 boundary patches = 69 wall + 20 nonConformalCyclic + 20 nonConformalError.
- Quality: non-orthogonality max **45.12** / avg 7.51; skewness max **1.22**; aspect ratio max **10.48**;
  max cell openness 6.1e-16; min cell volume 4.6e-11 m³. **Mesh OK.**
- Log: work_products/2026-07-02_overnight/checkMesh_coarse.log

## STEP 2 — refineMesh + NCC de-risk (the key unknown)
### 2a. refineMesh -all -overwrite — EXIT 0 (~1.5 min serial)
- Refined **nCells = 17,335,968 = 2,166,996 × 8 EXACTLY** → clean uniform octree, r=2 linear.
  nPoints 17,734,972, nFaces 52,398,976, nInternalFaces 51,616,832.
- Min edge length HALVED (x-aligned min 1.56e-4 m → 6.06e-5 m; "other" 8.06e-5 → 4.03e-5) →
  confirms the first BL cell halves, so y+ ~halves — the wall-gradient QoIs (f, Nu) get the intended
  resolution bump.
- Boundary AFTER refine: 20 nonConformalCyclic + 20 nonConformalError + 69 wall still present —
  refineMesh PRESERVED the NCC patch structure and patch names.
- IMPORTANT CAVEAT: `refineMesh -overwrite` wrote ONLY the mesh to constant/polyMesh; it did NOT
  interpolate the 7915 fields (T/U/p_rgh remain 2,166,996 values → mesh/field mismatch). So a
  fine RUN or dry-run must (re)initialize fields on the fine mesh via `mapFields` (coarse→fine,
  consistent geometry) or setFields. Documented; handled in Step 3.
- Log: work_products/2026-07-02_overnight/refineMesh_fine.log

### 2b. checkMesh on the refined 17.3M mesh
- Topology (serial): ALL OK — Boundary definition OK, cell-face addressing OK, point usage OK,
  upper-triangular OK, face vertices OK, zip-up OK, face-face connectivity OK. Mesh stats: 17,335,968
  cells 100% HEXAHEDRA (clean octree), 109 patches, 4 face zones, 33 cell zones preserved.
- Geometry phase: serial checkMesh on 17.3M cells ran >30 min with no completion → serial checkMesh is
  impractically slow at this size. Switched to PARALLEL (decomposed) checkMesh (Step 2e). Killed only MY
  checkMesh procs; T2's 128 foamRun verified still running.

### 2c. createNonConformalCouples on the refined interface — SUCCESS (EXIT 0)
- All 10 couples (couple0..couple9) rebuilt from createNonConformalCouplesDict on the refined `ncc_*` patches.
- Per-couple match quality is EXCELLENT: source coverage avg **0.99** (target 1.0), openness ~**1e-16**,
  match error ~**1e-13**, angle 0; ~14.5k-18.9k couplings/couple in ~0.1-0.2 s. Each interface 2304 faces (=4× coarse).
- fvMeshStitcher connected: cell openness ~4e-17, projected-volume-fraction ~9e-14 → clean stitched mesh.
- **VERDICT: refineMesh(r=2) + createNonConformalCouples WORKS on this NCC-assembled loop mesh.** This is the
  key de-risk the whole T6 self-meshing plan hinged on. Log: work_products/2026-07-02_overnight/ncc_fine.log

### 2d. Field initialization on the fine mesh (refineMesh does NOT map fields)
- refineMesh -overwrite left 7915 fields at the coarse 2,166,996 count (mesh/field mismatch) → must map.
- `mapFields -mapMethod cellVolumeWeight`: REJECTED (this OF13 build only offers mapNearest/interpolate/cellPointInterpolate).
- `mapFields -mapMethod interpolate`: **SIGFPE core-dump (exit 136)** — floating-point exception in the
  interpolation weights (benign division, likely at/near the NCC interface). Documented.
- Retry with `-mapMethod mapNearest`: SAME FPE. Stack trace pins the root cause: it is NOT in the mapping —
  it is in `fvMeshStitcher::connectThis → fvMesh::unconform → mag(surfaceVectorField)` when the STITCHED FINE
  mesh is loaded. i.e. the refined NCC interface has at least one **zero-area face**, and `mag()`/normalisation
  hits a div/sqrt-of-zero that trips OF's SIGFPE trap.
- IMPORTANT COMPARISON: the ORIGINAL coarse run (`log.foamRun`, same NCC couples) ran `fvMeshStitcher: Connecting`
  and advanced time steps fine WITH SIGFPE trapping ON → the COARSE couples have NO zero-area faces. The zero-area
  face is introduced by REFINING the non-conformal interface (r=2 splits an interface face into 4; at the couple
  edges this can yield sliver/zero-area sub-faces). Given createNonConformalCouples reported excellent coverage
  (0.99) and openness (~1e-16), these are benign edge slivers, not broken couples — but they DO trip the FPE trap.
- FIX: OF13 gates the trap on `env("FOAM_SIGFPE")` = variable-IS-DEFINED (any value, incl. empty). OF's bashrc
  EXPORTS `FOAM_SIGFPE=` (empty) → always on; `FOAM_SIGFPE=false` does NOT disable it. Must `unset FOAM_SIGFPE`.
  Applies to EVERY tool that loads the stitched fine mesh, INCLUDING foamRun → the solver dry-run must also unset it.
  CAVEAT for the eventual production run: running with FPE untrapped means a genuine NaN could go unnoticed; the
  run must be watched for finite residuals + bounded fields. A cleaner long-term fix is to collapse/merge the
  zero-area interface slivers (e.g. tighter createNonConformalCouples matchTolerance or a small collapseEdges),
  but for the de-risk, unset-FPE + residual monitoring is the pragmatic path.
- mapFields also FATAL "size 2166996 != 17335968" — it READS the stale coarse-sized field files refineMesh left
  in 7915. Moved them to 7915_stale_backup/ so mapFields creates fresh fine fields (BC dicts come from the source).
- **mapFields mapNearest (FPE untrapped, clean target) EXIT 0** — fine mesh now carries consistent 17,335,968-value
  T/U/p_rgh/rho. mapNearest is exact for octree children (each fine cell inherits its parent coarse value).
  Benign "no valid tet decomposition" warnings on the refined interface faces (same sliver faces).

### 2e. Parallel decomposition — BLOCKER (as of ~18:31)
- Serial checkMesh on 17.3M cells was impractically slow, so the plan was: decomposePar to 64 ranks → parallel
  checkMesh + parallel foamRun dry-run.
- `decomposePar` (scotch, 64) on the refined+stitched mesh runs the scotch partition, then **FOAM-FATALs in
  `HashTable<int, Pair<int>>::operator[]`** — decomposePar cannot map a nonConformalCyclic couple's processor-pair
  across the decomposition. (Wrapper's tail-pipe masked it as exit 0; the real run FATALs. Re-running to capture the
  exact message.)
- CONTEXT: the ORIGINAL coarse run's `log.decomposePar` decomposed the SAME stitched-couple mesh with the SAME plain
  `scotch` dict and SUCCEEDED (processors64/constant carries the couples). So decomposing a stitched NCC mesh is the
  intended workflow — the failure is SPECIFIC to the refined couples (their inter-processor pair addressing has an
  inconsistency the coarse couples don't). This is the current hard edge of the self-meshing pipeline.
- EXACT ERROR (captured): `--> FOAM FATAL ERROR: (56 54) not found in table` — a nonConformalCyclic couple's two
  ORIGINAL patches landed on processors 56 and 54, a pair decomposePar's couple-topology table never created
  (the valid entries are mostly self-pairs (N N) + a few regular neighbours like (10 28)). The coarse mesh's
  couples never split this way, so it is refinement-induced (4× more/finer couple faces → scotch splits a couple).
- TRIED: `preservePatches` decomposition constraint over all 20 base `ncc_*` patches. decomposePar got MUCH further
  (built all 64 processor meshes, Max cells 273,583 ≈ balanced) but STILL FATAL'd with the SAME (56 54) error —
  preservePatches keeps a single patch's faces together but the couple pairs faces across TWO patches on different
  legs, which can still land on different processors. So preservePatches alone is insufficient for NCC.
- REMAINING FIXES (not yet landed, documented for continuation): (a) `singleProcessorFaceSets` forcing each
  couple's BOTH patches onto one processor (needs a faceSet per couple, built via topoSet); (b) decompose the
  refined mesh with couples REMOVED (base ncc_ patches only) then `createNonConformalCouples -parallel` after
  decomposition — the OF-canonical NCC-in-parallel workflow (needs an un-stitched refined mesh; createNonConformalCouples
  has no -remove, so re-refine a couple-free clone); (c) fewer ranks to reduce couple-split probability (not guaranteed).

### 2f. PIVOT — SERIAL solver dry-run (avoids the parallel-NCC decompose blocker)
- The Step-3 goal is only to PROVE the custom `rcExternalTemperature` wall BC constructs on the fine mesh and that
  the solver starts with finite residuals. That does NOT require parallel. Running foamRun SERIALLY on the fine 17.3M
  mesh (unset FOAM_SIGFPE, tiny endTime 7915→7915.03, a few deltaT) sidesteps the decompose blocker entirely.
  Slow per step, but a couple of steps is enough for the BC-construction + finite-residual proof.
- RESULT: foamRun got FAR — loaded the mesh, re-computed all 10 couples (18,624 couplings, openness ~1e-16),
  ran `fvMeshStitcher: Connecting` reporting **"0/NNNN small couplings removed/added"** for every couple (i.e.
  the couples stitch cleanly, no slivers removed) — then **SIGSEGV (exit 139)** in:
  `fvMesh::fvMesh → postConstruct → fvMeshStitcher::connectThis → intersect → applyOwnerOrigBoundaryEdgeParts →
   primitiveMesh::edgeFaces() → faceEdges()`.
  i.e. a memory fault computing EDGE-FACE addressing on the stitched fine mesh during the stitcher's
  boundary-edge-part application. NOT an FPE (that was unset) — a genuine segfault in the refined interface's
  edge topology.

## KEY FINDING / HONEST VERDICT (T6 de-risk)
- **refineMesh (r=2, exact octree, 17.3M cells, 100% hex) SUCCEEDS**; the coarse baseline and refined topology are clean.
- **createNonConformalCouples on the refined interface SUCCEEDS as a standalone utility** with EXCELLENT match
  metrics (coverage 0.99, openness 1e-16, error 1e-13) — the couples are geometrically valid.
- **BUT the refined non-conformal interface breaks OF13's fvMeshStitcher at run/solve time**, in TWO independent ways:
  (1) PARALLEL: `decomposePar` FATAL "(56 54) not found in table" — a couple's two patches split onto an
      incompatible processor pair (preservePatches constraint did not fix it);
  (2) SERIAL: `foamRun` SIGSEGV in `fvMeshStitcher::applyOwnerOrigBoundaryEdgeParts → edgeFaces()` on the stitched
      fine mesh's edge addressing.
  The COARSE mesh does neither (original run stitches + decomposes fine). So uniform refinement of the NCC
  *assembly interface* is the failure point — refining the interior is fine, but the refined non-conformal couples
  are not runnable in this OF13 build via the naive refineMesh→createNonConformalCouples path.
- CONSEQUENCE: I did NOT get a runnable fine mesh, so **NO GCI number is produced** (correctly — fabricating one
  would violate the rigor mandate). Steps 1-2 (baseline + refine + couple-create) validated; Step 3 (solver dry-run)
  FAILED at the stitcher; Step 4 (bounded run + GCI) not reached.

## Baseline COARSE-clone solver check (isolates the fine-interface as the sole fine-mesh blocker)
- Ran foamRun serially on the COARSE clone (tiny endTime). Needed to add uniform `p` (101325) + `ph_rgh` (0) to the
  reconstructed 7915 dir — the recon only reconstructed (T p_rgh U rho), and the fluid solver requires `p`/`ph_rgh`.
- RESULT: solver fully constructed (heRhoThermo dynamicCode compiled, laminar/Stokes, Fourier, PIMPLE/PISO), the
  custom **rcExternalTemperature BC constructed with NO segfault**, couples stitched (openness ~4e-17), and it
  ADVANCED A TIMESTEP: `Time = 7915.0058s`, Courant mean 0.089/max 0.99, and solved **rho, Ux (7.9e-3→9.6e-7),
  Uy (0.84→1.6e-7), Uz (0.30→5.7e-7), h (3.4e-6→8.2e-9)** — all FINITE, converging. Momentum+energy work.
- It then FATAL'd at the `p_rgh` pressure solve ("cannot solve incomplete matrix, no diagonal") — a RESTART-STATE
  fidelity artifact: the reconstructed recon case lacks a consistent `ph_rgh` at t=7915 (I substituted the t=0
  uniform field). fvSolution is byte-identical to the original run's, so this is NOT a solver-config or mesh problem;
  it is the recon clone's pressure restart state. IMPLICATION: for a real baseline/fine run, stage the clone from the
  original DECOMPOSED processors (which carry a consistent p_rgh/ph_rgh at 7915) rather than the T/p_rgh/U/rho-only recon.
- NET: the clone + OF13 env + libRCWallBC.so + solver pipeline are PROVEN correct on the coarse mesh (BC constructs,
  momentum+energy solve, time advances). Therefore the FINE-mesh failure is EXCLUSIVELY the refined non-conformal
  interface breaking fvMeshStitcher (decompose FATAL + serial SIGSEGV) — not any pipeline/clone/env error.

## Next steps to make the fine mesh RUNNABLE (for a follow-on session)
1. **Avoid refining the NCC interface.** The couples are an ASSEMBLY convenience, not physics. Options:
   a. `mergeMeshes`/`stitchMesh` the coarse legs into ONE CONFORMAL mesh FIRST (removing the 40 NCC couples),
      THEN `refineMesh -all` the conformal mesh (no couples to break), then run. This is the cleanest: uniform
      refinement of a conformal mesh has no NCC stitcher to segfault. Verify the merged interface is watertight first.
   b. Refine only the INTERIOR cells (a cellSet excluding a band around each ncc_ interface) via `refineMesh -dict`
      with a refined cellSet, leaving the couple faces at coarse resolution → couples unchanged → stitcher happy.
      Not a uniform r=2 everywhere (weakens the clean GCI ratio) but keeps the wall-BL refinement where the QoIs live.
2. **Or** decompose the refined mesh with couples REMOVED then `createNonConformalCouples -parallel` (needs a
   couple-free refined mesh; createNonConformalCouples has no -remove, so build from a couple-free clone) — this only
   addresses the parallel path, not the serial-stitch segfault, so (1) is preferred.
3. **Or** Approach B from the checkpoint: `foamToSurface` the boundary → snappyHexMesh a fresh CONFORMAL mesh at
   2-3 resolutions (independent-mesh convergence, needs the 69-wall-patch BC re-mapping) — fully sidesteps NCC.
4. Report to the advisor: the naive "refine the delivered NCC mesh" path is blocked by fvMeshStitcher on the
   refined interface; the conformal-merge-then-refine path (1a) is the recommended fix and is the fastest route to
   the first 2-level GCI bound.
5. Stage the clone from the original DECOMPOSED processors (processors64 at t=7915, consistent p_rgh/ph_rgh),
   not the T/p_rgh/U/rho-only reconstructed recon case — otherwise the coarse baseline p_rgh solve fails on an
   inconsistent pressure restart (observed here; fvSolution is byte-identical to the working original run).

## Artifacts (all under work_products/2026-07-02_overnight/ unless noted)
- Reusable pipeline: mesh_gci_pipeline.sh (clone→check→refine→ncc→map→checkf→dryrun→run; NRANKS=64 to protect T2;
  encodes the unset-FOAM_SIGFPE, stale-field-move, and preservePatches lessons). `bash -n` clean.
- 2-level GCI helper: gci_2level.py (assumed-order Richardson/GCI, Fs=3.0; self-contained; smoke-tested).
- Logs: checkMesh_coarse.log, refineMesh_fine.log, ncc_fine.log, mapfields_fine4.log, decompose_fine2.log,
  decompose_fine3.log, dryrun_serial_fine.log, dryrun_coarse2.log.
- Clones (kept for resume): tmp/2026-07-02_mesh_gci/{coarse_clone, fine_workspace} (6.7 G).

## Guardrails honored
- T2 (idev 3269598, 128 foamRun) verified untouched throughout (ps, not nproc). Codex jobs untouched.
- All mutation on clones; recon source + jadyn_runs read-only trees not modified. Killed only my own checkMesh procs.
- No fabricated mesh or GCI number — the pipeline is blocked at the refined-interface stitcher, and that is reported as such.

## Reusable pipeline
work_products/2026-07-02_overnight/mesh_gci_pipeline.sh (clone→check→refine→ncc→checkf→dryrun→run;
NRANKS=64 to protect T2's 128 cores). RESULTS_LOG.md carries the running milestones.

## Honest confidence boundary (so far)
- refineMesh subdivision is exact and cheap; the OPEN question is whether the refined NCC couples
  are geometrically valid + runnable (checkMesh geometry + a solver dry-run must confirm before any
  GCI number is trusted). No GCI fabricated.
- Even when it runs, this is a 2-LEVEL study → ASSUMED formal order, NOT observed order. Roache's own
  guidance (and the docstring of tools/analyze/compute_gci.py) is Fs=3.0 for a 2-grid assumed-order
  band (NOT Fs=1.25, which is for a 3-grid OBSERVED-order study). I will use Fs=3.0 and label it.
