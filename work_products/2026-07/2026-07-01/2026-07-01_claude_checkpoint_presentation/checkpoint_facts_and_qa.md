# Checkpoint — facts sheet & anticipated-question prep (2026-07-01)

Everything here traces to a dated artifact this session; each answer states its
confidence boundary. Values are for the mainline Salt Jin continuation, coarse mesh.

## HARD NUMBERS (have these ready verbatim)
- **Mesh size:** 2,166,996 cells · 2,268,735 points · 6,598,756 faces
  (6,403,220 internal). Source: `constant/polyMesh/owner` header. ONE mesh level
  ("coarse"); mesh_group_id 7ab7fb2650596980.
- **Solver:** OpenFOAM 13, buoyant variable-density (p_rgh formulation), LAMINAR
  (momentumTransport laminar), custom wall BC `libRCWallBC.so`. g=(0,-9.81,0).
- **Working fluid / properties:** molten salt, Jin correlation set: mu(T)=A·exp(b/T),
  rho(T)=2293.6-0.7497·T [kg/m3], cp=1423.47 [J/kgK], k(T) poly. TRef=447 K.
- **Operating regime:** Re ≈ 61-135 (Salt 2→4 Jin, by Jin mu at bulk T); laminar,
  natural circulation (no pump). Bulk T ≈ 173-201 °C (Ethan-confirmed rig 165-210 °C).
- **Loop mdot ≈ -0.0132 kg/s** (nominal, monitor faceZones).
- **Geometry (mesh-PCA measured, T1):** heater (pipeleg_lower) 21.5° from horizontal;
  cooler (pipeleg_upper) 21.5°; downcomer (right) vertical; test section vertical,
  bore **20.9 mm** (quartz); all other legs bore **22.1 mm**.

## THE ADVISOR'S LIKELY QUESTIONS — honest answers
**Q: How many cells in the CFD?**
A: 2.17 M (2,166,996). It's the COARSE level and the ONLY level we currently have.

**Q: Is the solution mesh-independent? What's your discretization error?**
A: Not yet quantified — we state that plainly (the 1D-model READMEs themselves flag
coarse mesh as diagnostic-only), and we have a CONCRETE plan in motion, not just a
blocker. The pre-built medium/fine meshes and the parametric generator are not
available to us, so we are SELF-GENERATING finer meshes from the existing coarse
mesh. The OpenFOAM v13 toolchain we already run has everything needed (refineMesh,
refineWallLayer, snappyHexMesh, createNonConformalCouples, checkMesh). Plan (this
week): (1) uniform refineMesh r=2 → 17.3M-cell fine level with EXACT geometry
preserved and the boundary layer's first cell halved, regenerating the non-conformal
couples; (2) run coarse+fine to pseudo-steady and compute a 2-level Richardson/GCI
bound (Roache/ASME V&V20 calculator, already built and tested) on mdot, f, Nu, y+;
(3) a cheap refineWallLayer wall-resolution sensitivity in parallel; (4) if a formal
3-level observed-order GCI is needed, an independent snappyHexMesh rebuild from the
extracted boundary surface. First step is de-risking the couple regeneration on a
clone. Honest scope: a 2-level bound is assumed-order (weaker than 3-level) but a
real first discretization-error bar — far better than the current NONE. Until it
lands, every closure carries an UNQUANTIFIED mesh-error bar and we don't claim
otherwise. (plan: .agent/journal/2026-07-01/checkpoint.md)

**Q: Is it converged / steady?**
A: Salt 2/3/4 Jin mainline continuations are stationary in flow (mdot) and gross
duty; Salt 1 is weaker. We built an operating-point convergence gate and used it to
REJECT the ±Q perturbation runs as false-steady (mdot pinned at nominal despite
±5-10% heater power; moved <0.3% vs a 1.6-3.5% expectation). So we are NOT using
those for correlations. (T3, assess_time_convergence.py)

**Q: Laminar or turbulent?**
A: Laminar (Re 61-135). Natural circulation; no turbulence model.

**Q: How do you get a friction factor from a buoyancy-driven loop? (early f was negative)**
A: A single leg's p_rgh gradient is NOT friction — in a buoyancy-driven loop p_rgh
carries the buoyancy source gh·dρ/ds, which dominates on the heated/cooled legs and
flipped the naive f negative. We do a full streamwise momentum budget, subtract the
buoyancy source AND fix each leg's flow orientation (measured from U·tangent), and
recover physical friction: f/f_lam ≈ 1.0-3.3 on every leg. We validated it with a
loop energy closure: buoyancy head (41-45 Pa) = straight friction (57-70%) + bend
minor losses (30-43%). (T1b)

**Q: Why is the bend K so large (6-16)?**
A: Low Re. Laminar bend loss scales K ≈ C/Re + K_inf, so at Re~60-135 K is far above
the textbook high-Re (~0.2-1) values, and it DECREASES with Re as we see. The 1D
model must use K(Re), not constants. (T7)

**Q: Do you trust the geometry / how did you get the leg angles & diameters?**
A: From mesh PCA of the wall patches (authoritative), NOT the schematic probe CSV.
We CAUGHT two provenance bugs in the schematic and corrected our pipeline: (1) it
cut the inclined heater as if vertical; (2) it swapped the lower/downcomer leg
labels (0.566 m off) and inflated leg lengths ~1.3×. Our closures now key on mesh
geometry; we re-reported the affected thermal UA'/q' (+27-33%). (T1, T8)

**Q: What about the downcomer thermal — wasn't it blocked?**
A: It was policy-blocked; we unblocked it with justification (q_w reconstructed, T
available, confirmed no recirculation). Downcomer HTC ~43-44 W/m2K, Nu ~1.74 —
a passive parasitic-loss leg (Nu below developed value, ambient-resistance limited). (T4)

**Q: Do the 3D closures make the 1D model predictive? Did injecting them help?**
A: Honest answer, refined by a controlled overnight study: NO, not by themselves —
and the reason is instructive. We put the CFD per-leg friction into the 1D loop and
compared to CFD, but CRUCIALLY we controlled the thermal boundary. Findings:
(1) The 1D loop temperature is EXTREMELY sensitive to the insulation/ambient-loss
setting — it swings 422→512→548 K over 0→1→2 in insulation; CFD's 450 K corresponds
to ~0.27 in. Our first "closures help mdot" result was an ARTIFACT of an insulation
setting that ran the loop ~60 K too hot.
(2) At a CFD-MATCHED temperature (loop T≈450 K, ΔT 12.1 K = CFD), adding the CFD
friction makes mdot WORSE, not better (default −27% → per-leg −49%). So whether
closures "help" mdot is CONDITION-DEPENDENT (they help when the loop is too hot/over-
predicting, hurt when temperature-matched/under-predicting). => mdot is NOT a robust
closure-quality metric; the per-segment pressure DISTRIBUTION is (per-leg friction
matches CFD by construction, independent of thermal state) — that is the defensible
win, and we implemented a per-leg friction multiplier for it.
(3) Even at matched temperature with CFD friction, the 1D under-predicts mdot by ~half
(0.0068 vs 0.0132). We checked and DISPROVED "drive too weak" (loop ΔT matches CFD;
buoyancy head not smaller). So there is an OPEN momentum-balance discrepancy — we do
NOT yet have a validated mechanism (partial contributor: CFD f/f_lam is Re-dependent,
so applying Re-68 multipliers at the 1D's Re-35 over-estimates friction ~10-30%).
BOTTOM LINE: the CFD closures are physically sound, but the dominant lever for a
predictive 1D loop is the THERMAL BOUNDARY (match effective insulation/ambient-loss),
not the hydraulic closures; and a factor-2 momentum-balance gap remains open. The
older "local replay ~1.9% mdot" held the CFD drive FIXED (tested only resistance) —
the full predictive loop is far from that. Full analysis:
reports/2026-07/2026-07-02/2026-07-02_overnight_synthesis/ + .../2026-07-01_model_form_comparison/.

**Q: Radiation? Insulation?**
A: Convective HTC reported (wallHeatFlux has no qr column → convective-only, flagged).
Insulation = external wall HTC on 32 passive patches. We just launched proper
true-steady insulation-perturbation runs (hiins=more insulation=lower h) to make
insulation an independent 2nd knob — running now, not yet converged. (T2)

## WHAT WE EXPLICITLY DO NOT CLAIM (put this on a slide)
- No mesh-independence / discretization-error bound yet (blocked; plan in hand).
- Coarse mesh; single time per case; laminar.
- Perturbation-run correlation is blocked until the true-steady runs finish.
- Upcomer recirculation is characterized (backflow 19-34%) but the onset/limit and a
  fitted correlation need more operating points (T2 runs + onset CFD).
- Solver-field dimensionless groups (Ra/Ri/Nu) use a nominal bore Lc and a fixed
  reference T; the test-section value carries a definitional offset we've documented
  and will reconcile before any published correlation. (T9)
