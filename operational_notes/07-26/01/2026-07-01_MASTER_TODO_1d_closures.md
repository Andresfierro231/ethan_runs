# MASTER TODO — TAMU loop 1D closures (for 2026-07-01, any agent)

Owner who wrote this: claude (AGENT-156), 2026-06-30 EOD.
Purpose: a self-contained backlog so any agent can start cold tomorrow. Read §0–§2
first (orientation + hard gotchas), then pick a task from §3 (prioritized) using
the parallel map in §4. Every task lists: context, inputs, method, acceptance,
deps, parallel-safe. Guiding principles: disclose confidence boundaries; justify
every decision; heavy docs; reusable scripts.

================================================================================
## 0. ORIENTATION — read these before touching anything
================================================================================
- `.agent/journal/2026-06-30/1d-model-status-and-plan.md` — plan + phased map.
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md` — how to run every tool;
  OF env + non-mutating reconstruction recipe.
- `operational_notes/06-26/30/2026-06-30_mesh_geometry_vs_probe_csv_provenance.md` — CRITICAL:
  the probe CSV is a schematic that mismatches the mesh (see §2).
- `operational_notes/06-26/30/2026-06-30_next_scope_branch_closures_and_cfd_design.md` — branch
  closure types + CFD design.
- `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md` — upcomer cell model.
- `operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md` — thermal method.
- `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/README.md` — current numbers.
- `.agent/journal/2026-06-30/perturbation-run-convergence-audit.md` — false-steady runs.
- `.agent/BOARD.md` — claim a task row before editing; respect codex-owned paths.

================================================================================
## 1. CURRENT STATE — what is trustworthy vs not
================================================================================
TRUSTWORTHY (mainline Salt 2/3/4 Jin continuation, coarse mesh):
- Convergence: Salt 2/3/4 Jin stationary (flow + gross duty); Salt 1 weaker.
- THERMAL closures (HTC/UA'/Nu/R') — PATCH-based, correct legs. lower_leg(heater)
  HTC 252/269/288, UA' 16.6/17.7/18.9; upcomer Nu 3.1/4.1/5.0. (`work_products/2026-06-30_claude_thermal_htc/`)
- Empirical UPCOMER recirculation (left side): 15-33% backflow, real convection cell.
- Measured TEST-SECTION bore 20.9 mm (smaller, quartz); other legs ~22.0 mm.
- Hand onset estimate: cell shuts off ~Re few-hundred (Route A 240-260, Route B 100-235).

NOT TRUSTWORTHY YET (must redo/verify):
- FRICTION / SECTION-PRESSURE / RECIRCULATION BY PROBE LABEL — cut planes placed by
  the schematic probe CSV → heater cut as vertical instead of 21°, and lower↔right
  spatially swapped. MUST re-extract from mesh geometry (T1).
- Perturbation runs (hiq/loq/hi5q/lo5q/hiins/loins/optins): FALSE-STEADY (T3).
- All f/Nu/UA' carry an unquantified coarse-mesh error (T6).
- Upcomer correlation: only 3 coupled points; onset extrapolated (T10/T13).

================================================================================
## 2. HARD GOTCHAS (will bite you)
================================================================================
- **OF13 env (needed for T / native reconstruction):** `source tools/ofenv/of13_env.sh`
  = OF13 build (/work/.../2026-06-02_openfoam13) + `module load gcc/15.2.0` (for
  GLIBCXX_3.4.32) + libRCWallBC.so via controlDict `libs(...)`. Under OF12 (`of12_env.sh`)
  T's custom BC SEGFAULTS. reconstructPar must run in ONE FOREGROUND call (~5 min;
  backgrounded runs get killed mid-merge → truncated points; if so delete
  constant/polyMesh + the partial time dir and retry).
- **Run Python with SYSTEM python** (do NOT source any OF env in the same shell —
  it swaps libstdc++ and breaks python). Tools wrap foamPostProcess in a subshell.
- **`tp_tw_probe_locations.csv` is a SCHEMATIC** — does NOT match mesh geometry. Get
  inclination/diameter/centerlines from the MESH patches (PCA), not this CSV. The
  probe frame SWAPS `lower_leg`↔`right_leg` spatially (probe lower=mesh downcomer;
  probe right=mesh heater).
- **Mesh truth (PCA-measured):** heater pipeleg_lower ~21° from horizontal (long, 2
  bends); cooler pipeleg_upper ~22°; test section pipeleg_left_04 vertical, 20.9 mm;
  downcomer pipeleg_right vertical. g=(0,-9.81,0) — CFD matches the rig.
- **Characteristic Ri = section MEDIAN (~O(1)), NOT mean** (mean ~100× larger,
  low-U-dominated). Use Ri_streamwise = Ri_median·cosθ for the correlation.
- **Segment map (owner-locked):** lower_leg=heater(=heated_incline); upcomer=
  left_lower_leg+test_section_span+left_upper_leg; downcomer=right_leg; cooler=upper.
- **mainline data** lives in `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/salt{1..4}_jin/case_stage/..._continuation/`.
- Operating T confirmed by Ethan: 165-210 °C (CFD bulk 173-201 °C ✓). No reeval needed.
- Do NOT edit codex-owned files: `tools/extract/sample_leg_centerline_major_loss.py`,
  `tools/case_analysis_profiles.py` (shared — needs coordinator), registry/config.

================================================================================
## 3. TODO BACKLOG (prioritized)
================================================================================

### PROGRESS 2026-07-01 (AGENT-162 claude + delegated bg agents)
- T1 DONE: build_mesh_centerlines.py (heater 21.5deg, bores 20.9/22.1mm). Wired into
  section-pressure. Journal T1-mesh-centerlines-geometry-refix.md.
- T1b DONE: derive_streamwise_momentum_budget.py -> de-buoyed friction, all legs
  f/f_lam ~1.0-3.3; loop-closure shows minor losses ~30-43% of buoyancy head.
  Upcomer tool wired to mesh. Journal T1b-momentum-budget-debuoyed-friction.md.
- T3 DONE (AGENT-166): operating-point gate; ALL 14 perturbation runs false-steady.
- T4 DONE: downcomer thermal (--admit-downcomer): HTC~43-44, Nu~1.74-1.76.
- T5 DONE: all-span recirc; exclusive to upcomer (bf 0.19-0.34). Journal T5-*.
- T9 DONE: dimensionless-definition audit (Lc=nominal bore mismatch in test section,
  TRef=447K datum, solver Nu uses Tw-TRef, per-cell Ri diverges at U->0). Journal T9-*.
- T2 RUNNING (AGENT-164): Salt2 hiins/loins on node c318-008 (endTime 33000s~5tau_ext);
  naming LOCKED hiins=more insulation=lower h. Requalify + extend to S3/4 next session.
- T7 DONE: sample_bend_minor_loss.py; corner K~6-16 (Re-dependent laminar bends),
  test-section connector K undefined (recirc zone). Journal T7-bend-junction-minor-loss.md.
- T8 DONE (audit + BOTH fixes): proved lower<->right centerline_labels swapped (sep
  0.566m) + labels ~1.3x too long. Fix#1 LANDED: swapped the labels in
  case_analysis_profiles.py (co-location now ~0; 196 tests pass). Fix#2 LANDED: added
  --mesh-length to sample_segment_htc_uaprime.py -> corrected UA'/q' (+27-33%;
  HTC/Nu unchanged). Journal T8-*.
- T6 BLOCKED (external): no in-repo mesher; needs Ethan to provide the NCC parametric
  mesh generator OR pre-built medium+fine polyMeshes. See
  operational_notes/07-26/01/2026-07-01_T6_gci_blocker_ethan_request.md. #1 trust limiter.
- STILL OPEN: T10 (upcomer correlation - needs T2 done + T9 reconciliation: single Lc,
  median Ri, Tbulk Nu), T11 (closure bundle refresh - needs T6 GCI bounds), T13
  (onset/limit CFD design - needs T2 requal). T8 fix#1 (profile label swap) - coordinator.

### T1 [HIGH] Re-extract hydraulic closures from MESH-built centerlines
- WHY: friction/section-pressure/recirculation were placed by the schematic probe
  CSV → mis-oriented (heater cut vertical not 21°) and lower↔right mislabeled. This
  is the #1 correctness fix for the hydraulic side.
- INPUTS: OF13 reconstructions `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13/`
  (have T,U,p_rgh,rho + Ra/Ri/Gr/Re/Pr); mesh patches pipeleg_*.
- METHOD: build per-leg centerline + true local tangent + true bore from the MESH
  (PCA of each pipeleg_* patch, or skeleton of cell centroids) — NOT the probe CSV.
  Re-place cut planes PERPENDICULAR to the true local axis. Re-run
  `sample_section_mean_pressure.py` + `derive_segment_friction.py` +
  `sample_upcomer_convection_cell.py` against the corrected geometry. New tool
  e.g. `tools/extract/build_mesh_centerlines.py` (PCA patch axis + bore) feeding the
  existing extractors (add a --centerline-source mesh option, default to mesh).
- ACCEPTANCE: heater section cut perpendicular to its 21° axis (alignment ~1.0);
  measured bores match mesh (test section 20.9, others 22.0); friction recomputed
  for heater (now correct) and downcomer; upcomer ~unchanged. Document deltas vs
  the probe-based numbers.
- DEPS: none (data ready). PARALLEL: authoring parallel; OF compute serial.

### T2 [user-requested] Resubmit loq_loins and hiq_hiins (and proper insulation runs)
- WHY: user explicitly asked to resubmit loins/hiins. Current ones are false-steady
  (mdot pinned at nominal) AND only changed Q (insulation knob was never applied —
  `insulated.h`=5.964 unchanged). So they are neither converged nor true insulation
  variants.
- ACTION (two parts):
  (a) RESUBMIT the existing loq_loins + hiq_hiins (Salt 2/3/4 Jin) continued to TRUE
      steady state — run long enough that the perturbed mdot moves to its new value
      and re-plateaus (est. several thermal time constants; compute
      τ≈ρ·cp·V_loop/(UA), likely >>5000 s; set endTime accordingly).
  (b) MAKE THEM REAL INSULATION RUNS: actually change the insulation boundary
      (the wall h on the insulated patches). CONVENTION (user-locked 2026-07-01,
      see memory insulation-naming-convention): hiins = MORE insulation = LOWER h
      (less loss, smaller wall ΔT); loins = LESS insulation = HIGHER h. (Earlier
      wording here said "hiins=higher h" — that was WRONG and is corrected.)
      Implemented in T2 as hiins→h×0.5, loins→h×2.0 on the 32 passive insulated
      patches, so insulation becomes the independent 2nd knob.
      Verify the BC change lands in case_config AND the 0/T boundaryField. If the
      insulation perturbation belongs on a different patch group than `insulated`,
      find which and document it.
- INPUTS: nominal continuation as restart; jadyn_runs campaign launchers
  (`Fluid/submit_array_campaign.sh` pattern; existing sbatch wrappers under the
  jadyn_runs waves). These are jadyn_runs campaign assets → coordinate with the run
  owner; do NOT mutate existing case_stage dirs, stage fresh.
- ACCEPTANCE: each resubmitted run reaches operating-point steady (mdot moved from
  nominal by ~Q^(1/3) and re-plateaued; gross duty stationary); hiins/loins show a
  DIFFERENT wall ΔT than nominal (insulation actually changed). Records job IDs.
- DEPS: needs Slurm + OF13 runtime + libRCWallBC.so (available). PARALLEL: submit then
  poll; independent of analysis lanes. >1 h runtime → sbatch (not interactive node).

### T3 [HIGH] Requalify perturbation runs (operating-point convergence gate)
- WHY: `assess_time_convergence.py` flags monitor-flat but runs are false-steady
  (mdot at nominal despite ±5-10% Q). See `.agent/journal/2026-06-30/perturbation-run-convergence-audit.md`.
- METHOD: add a convergence mode that requires the operating point to have MOVED
  from the nominal baseline by ~the expected amount AND re-plateaued (e.g.
  `--require-moved-from <baseline_mdot>`); compute advance-past-restart; compute
  τ_thermal. Reject runs below threshold.
- ACCEPTANCE: a per-run table {advance, mdot vs nominal, verdict}; only genuinely
  re-equilibrated runs pass. Feeds T10/U1.
- DEPS: none (reads postProcessing). PARALLEL: yes (no OF compute).

### T4 [MED] Unblock + extract downcomer (right_leg) thermal
- WHY: downcomer thermal is policy-blocked, but q_w is reconstructed and T is
  available; downcomer = ordinary f(Re)+Nu (no recirc, confirmed). See
  `operational_notes/06-26/30/2026-06-30_downcomer_closure_analysis.md`.
- METHOD: run `tools/extract/sample_segment_htc_uaprime.py` with the right_leg block
  removed (add a flag to admit it); report UA'/HTC + indicative Nu with caveats.
  USE CORRECTED geometry from T1 for D_h.
- ACCEPTANCE: downcomer UA'/HTC/Nu with confidence flags. DEPS: T1 (geometry).
  PARALLEL: after T1.

### T5 [MED] Add right_leg (+ all spans) to the convection-cell tool
- WHY: `sample_upcomer_convection_cell.py` only dumped upcomer spans → no Ri/Ra for
  downcomer to quantify its opposing-flow reversal margin.
- METHOD: make UPCOMER_SPANS configurable (`--spans all`); rerun on recon_salt{2,3,4}_of13.
- ACCEPTANCE: Ri/Ra/recirc for every leg, on corrected geometry (T1). DEPS: T1.
  PARALLEL: after T1.

### T6 [HIGH, big compute] Mesh-independence (GCI) study
- WHY: #1 trust limiter — no discretization-error bound on ANY f/Nu/UA'. Now
  executable (OF13 recovered). Protocol: `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`;
  calculator ready: `tools/analyze/compute_gci.py` (+test).
- METHOD: generate medium + fine meshes for Salt 2 & Salt 4 Jin (envelope ends);
  run to pseudo-steady; extract mdot, gross duty, f, Nu, UA' on each level; GCI.
- ACCEPTANCE: GCI bands + Richardson-extrapolated values on f and Nu; asymptotic
  check reported. DEPS: mesh gen + multi-node sbatch. PARALLEL: independent.

### T7 [MED] Bend/junction minor-loss K (NIST two-tap)
- WHY: fittings are not friction factors (LitRev/NIST). Currently in the residual.
- METHOD: K = ΔP_total,loss / (½ρV²) between upstream/downstream planes with straight
  friction removed (NIST multi-tap eq.), on corrected geometry. New tool
  `tools/extract/sample_bend_minor_loss.py`. Cluster K for close-coupled fittings.
- ACCEPTANCE: K per named corner/reducer with provenance + Re-dependence note.
  DEPS: T1 (geometry). PARALLEL: after T1.

### T8 [MED] Audit/fix case_analysis_profiles span↔patch mapping (lower↔right swap)
- WHY: span centerline labels (probe frame) and wall_patches (mesh) can refer to
  different physical legs (lower↔right swap). This is codex-owned/shared
  (`tools/case_analysis_profiles.py`) → COORDINATE on the board first.
- METHOD: verify each span's centerline geometry and wall patches co-locate (use
  mesh PCA from T1); propose corrections; do not edit unilaterally.
- ACCEPTANCE: a documented mapping table proving co-location; coordinator-approved
  edit or a follow-on task. DEPS: T1. PARALLEL: analysis parallel; edit gated.

### T9 [LOW-MED] Page-audit the solver Ra/Ri/Gr definitions
- WHY: characteristic Lc and reference ΔT in the solver's coded dimensionless fields
  are unaudited; needed before a published correlation. The section MEDIAN Ri is
  ~O(1) (use it), the mean is misleading.
- METHOD: read the `dimensionlessFields` coded FO in `system/functions`; record Lc,
  ΔT, property basis; reconcile with the literature group definitions used in the
  reversal criterion (`tools/analyze/mixed_convection_reversal.py`).
- ACCEPTANCE: documented definitions + whether they match the correlation's groups.
  DEPS: none. PARALLEL: yes.

### T10 [MED] Upcomer recirculation correlation fit (+ Nu(Ra,Pr) cell scaling)
- WHY: turn the seed data into a fitted onset law once more points exist.
- METHOD: fit backflow = F(Ri_streamwise) onset form (logistic/power) + Nu(Ra,Pr);
  report Ri_crit, bf_max, R². Use mesh-corrected geometry (T1) + requalified
  perturbation/new points (T3/T2/T13).
- ACCEPTANCE: fitted correlation with validity window + paper-ready figures.
  DEPS: T1, T3, and more data (T2/T13). PARALLEL: consumes others' output.

### T11 [MED] Re-derive the closure bundle from the continuation window
- WHY: the published `ethan_cfd_informed_salt_v2` bundle rests on warmup-era /
  legacy extraction; refresh from the mainline continuation + corrected geometry.
  Coordinate with the closure-bundle owner (external Fluid repo).
- METHOD: feed corrected f, UA'/HTC/Nu, segment map into a refreshed bundle; version
  it; keep upcomer as the cell model (not f), downcomer f+Nu, etc.
- ACCEPTANCE: versioned bundle + provenance; 1D model consumes it. DEPS: T1, T4.

### T13 [HIGH for the science] Design + (when approved) launch onset/limit CFD
- WHY: locate where the upcomer cell turns OFF and its MAX. Current runs all in-cell
  (Re 50-150); shutoff estimated ~Re few-hundred.
- DESIGN (no forced-flow per Ethan): a {Q level}×{insulation level} matrix per
  Salt 3 Jin anchor; push high-Q + high-insulation to reach Re≳250 (cell off);
  low-insulation + low-Q for the MAX. All runs: same FOs (U,T,wallHeatFlux,
  Gr/Ra/Ri/Re/Pr), run to thermal-relaxation-based steady (see T2/T3 on time).
- ACCEPTANCE: a run matrix spec + (on approval) submitted jobs + extracted points
  spanning the (Re, Ri_streamwise) envelope. DEPS: T1, T3. PARALLEL: submit+poll.

================================================================================
## 4. PARALLELIZATION MAP (1 interactive core → OF compute is serial)
================================================================================
- SERIAL DRIVER (one agent owns the OF compute queue): T1 reconstructions/sampling,
  T6 runs, T2/T13 sbatch monitoring. reconstructPar + foamPostProcess foreground.
- PARALLEL (no OF compute, multiple agents/sub-agents): T3 (convergence code),
  T8 (mapping audit, analysis part), T9 (definition audit), T10 (fitting once data
  exists), authoring for T1/T4/T5/T7 tools.
- ORDER: T1 first (unblocks T4,T5,T7,T8,T10,T11). T2+T3 in parallel with T1
  (different resources). T6 anytime (own sbatch). 
- Each agent: claim a row on `.agent/BOARD.md`, use NEW dated files, don't touch
  codex-owned paths, write a dated journal note, run tests (`python -m pytest
  tools/analyze/test_*.py tools/extract/test_*.py -q`; 62 passing baseline).

================================================================================
## 5. ENV QUICK-REF
================================================================================
- Read fields incl T / native reconstruct: `source tools/ofenv/of13_env.sh; of13_assert_ready`
- Reconstruct (foreground): `reconstructPar -case <scratch> -time <t> -fields '(T p_rgh U rho)'`
- Sample (Python, SYSTEM python): tools pass `--of-env-script tools/ofenv/of13_env.sh`
- Tests baseline: 62 passing across 5 test files.
- Scratch recon cases already built: recon_salt{2,3,4}_of13 (+ _continuation OF12 ones).
