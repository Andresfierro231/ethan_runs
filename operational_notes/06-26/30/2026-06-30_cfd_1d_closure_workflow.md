# CFD → 1D Closure Workflow (AGENT-156 action-item package)

Date: `2026-06-30`
Owner: claude (AGENT-156)
Status: durable workflow note — START HERE to resume this work after a break.

This note is the single entry point for the post-inspection action-item work. It
records (a) the environment, (b) every reusable script and how to run it, (c)
what each produced, and (d) what remains. It is written so that after a weekend
you can re-run any step from a cold start.

Guiding principles for this work (user-stated, 2026-06-30):
1. **Disclose confidence boundaries** — every artifact states assumptions,
   validity windows, and known issues.
2. **Scientific rigor / justification** — every decision has a recorded "why".

Source review that motivated this: `.agent/journal/2026-06-30/claude-inspection-cfd-1d-closure-postprocessing.md`.

---

## 0. Environment (reproducible)

On an LS6 compute node (NOT a login node):

```bash
source tools/ofenv/of12_env.sh   # loads intel/24.1 impi/21.12 openfoam/12
of12_assert_ready                # verifies reconstructPar/foamPostProcess
```

DECISION + WHY: the cases are OpenFOAM Foundation **v13** collated
(`decomposedBlockData`, binary, `processors64/`) with a private custom BC
(`libRCWallBC.so`) that is not installed on LS6. LS6 provides Foundation
`openfoam/12`, the same fork, whose utilities read v13 fields for **standard
boundary conditions**. We therefore reconstruct/sample only `p p_rgh U phi rho`
(plus solver-written `Re Pr Nu Gr Ra Ri`). `T` carries the custom BC and CANNOT
be reconstructed here. Density for buoyancy/HTC work uses the stored `rho`
field, so `T` is not needed for pressure work.

IMPORTANT gotcha: loading the OF (intel/24.1) toolchain swaps out system
python3.9 and breaks our Python scripts. So: run the Python tools with the
**system** python (do not source the OF env in that shell). The tools that need
OpenFOAM (`sample_section_mean_pressure.py`) source the env only inside a
subshell for the `foamPostProcess` call.

---

## 1. Non-mutating reconstruction recipe (needed for items #1/#4)

Native solver outputs must never be mutated (AGENTS rule). We reconstruct into a
**scratch case** that symlinks the decomposed data and writes reconstructed time
dirs into scratch. The v12/v13 `faceZones` format differs (v13 drops the `type`
keyword), so we OMIT zone files from the scratch mesh (zones are only used by the
mdot monitors, irrelevant to pressure sampling); `fvMesh` then builds with empty
zones.

Reference working scratch case: `tmp/2026-06-30_claude_action_items/recon_salt2_jin/`
built as:
- `constant/` = real dir, symlinks to non-mesh dictionaries only
  (`physicalProperties momentumTransport thermophysicalTransport g fvModels fvConstraints`).
- `processors64/constant/polyMesh/` = symlinks to `boundary faces neighbour owner
  points *ProcAddressing` ONLY (NO `faceZones cellZones sets`).
- `processors64/<time>` and `processors64/0` symlinked.
- `system/` = minimal self-contained `controlDict` (no `functions`, no `libs`),
  symlinked `fvSchemes fvSolution decomposeParDict`.
- Run: `reconstructPar -case <scratch> -time <t> -fields '(p_rgh U rho)'`
  (~3-5 min on 1 core for the ~2.17M-cell coarse mesh; the mesh re-stitches the
  10 non-conformal couplings on each utility run).

> If a reconstruction is interrupted it leaves a truncated `constant/polyMesh/points`;
> delete `constant/polyMesh` and the partial time dir before retrying.

---

## 2. The eight action items — scripts, status, results

| # | Tool / artifact | Status | Headline result |
| - | --- | --- | --- |
| 1 | `tools/extract/sample_section_mean_pressure.py` | workflow DONE; numbers partial | Section-mean static `p_rgh` per station obtained; **dynamic head NOT yet trusted** (velocity flux anomaly, see below) |
| 2 | `tools/analyze/assess_time_convergence.py` | DONE + run | Salt 2/3/4 Jin stationary in flow AND gross heat duty (<0.2%); Salt 1 quasi-stationary |
| 3 | `tools/analyze/represent_closures_per_case.py` | DONE + run | Apparent f is 3.5–4×/~70× laminar; ~20% of Re spread is Jin/Kirst; fits dof≤1; Pr collinear w/ Re |
| 4 | folded into #1 (measured bore area) + proposed patch §4 | partial | Measured median bore ≈ 7.9e-4 m², ~2.2× the mdot-faceZone reference used by the legacy extractor |
| 5 | `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md` | protocol DONE | Needs runtime + custom BC; sbatch-scoped (>1 h) |
| 6 | `tools/analyze/reconcile_freeze_windows.py` | DONE + run | 13/14 freeze-window lanes unverifiable from staged data |
| 7 | `tools/analyze/validate_segment_map.py` + segment-map note | DONE + run | Only `upcomer` truly ambiguous; `heated_incline` provisional |
| 8 | proposed patches §4 below | documented | Standalone fixes; to be landed by extractor owner |

Run commands (system python, from repo root):

```bash
python tools/analyze/assess_time_convergence.py --paper-grade-salt-jin
python tools/analyze/represent_closures_per_case.py
python tools/analyze/reconcile_freeze_windows.py
python tools/analyze/validate_segment_map.py
# item #1 (needs a reconstructed case from §1):
python tools/extract/sample_section_mean_pressure.py \
  --case-dir tmp/2026-06-30_claude_action_items/recon_salt2_jin --time 2431 \
  --source-id viscosity_screening_salt_test_2_jin_coarse_mesh
python -m pytest tools/analyze/test_claude_action_items.py -q
```

Outputs land in `work_products/2026-06-30_claude_*/`. Synthesis: `reports/2026-06/2026-06-30/2026-06-30_claude_action_items_summary/README.md`.

---

## 3. Cross-cutting provenance note (UPDATED in phase 2)

Per the repo run-classification rule, **continuation runs are mainline**. The
canonical `staging/` tree holds the **parent warmup** (salt2_jin → 2431 s), but
the **mainline continuation field data IS staged locally** under
`jadyn_runs/.../2026-06-18_convergence_and_jin_envelope_wave/runs/` (salt2→7915,
salt3→7618, salt4→10000, salt1→4026). It was simply not registered in
`staging/`/`registry`. So:
- #2 convergence has now been run on BOTH the warmup and the mainline
  continuation; Salt 2/3/4 Jin are stationary in both (consistent steady state).
- #1 section-mean pressure has been rerun closure-grade on the salt2_jin
  continuation (t=7915), matching the warmup result.
- Registering continuation runs into the canonical registry is a coordinator
  decision (shared file): see `2026-06-30_mainline_continuation_staging_plan.md`.

---

## 4. Proposed patches for the owner-held extractor (items #4, #8)

`tools/extract/sample_leg_centerline_major_loss.py` is owned by codex
(AGENT-155); AGENT-156 did NOT edit it. The following are proposed, justified
changes to land there later (each is independently implemented or prototyped in
the new tools so the owner can copy the logic):

- **#4 measured area**: replace the idealized circular `flow_area_geom_m2`
  (`D_h=P/π`, `A=P²/4π`) with the measured cut-plane area (median of clean
  cross-sections), already computed by `sample_section_mean_pressure.py`. The
  measured median bore (~7.9e-4 m²) differs from the perimeter-derived circle by
  ~2.2×, which propagates quadratically into `f` via `u²`.
- **#8a signed wall shear**: use `tau_mean_signed` (not `tau_mean_abs`) in the
  shear-route `f = 8τ_w/(ρu²)` so recirculation does not inflate drag.
- **#8b enthalpy-flux bulk T**: weight the mixed-mean bulk temperature by
  `ρ·u·cp` (not `ρ·u`); salt `cp` is strongly T-dependent. (Affects HTC.)
- **#8c document `qr` exclusion**: the `wallHeatFlux` FO has no radiative column;
  state explicitly that HTC is convective-only for `rad_on` cases.
- **#8d NaN handling**: replace positional NaN-token interpolation in
  reconstructed `T` with time-exclusion + a logged dropped-count.
- **#8e stale surfaces**: the v2 UA'/HTC surfaces are verbatim v1 copies; version
  them explicitly or refresh.

---

## 5. Phase-2 resolutions (2026-06-30) and remaining steps

RESOLVED in phase 2 (see `.agent/journal/2026-06-30/coordinator-implementer-claude-continuation-and-velocity.md`):

- **#1 velocity flux anomaly — ROOT-CAUSED + FIXED.** `cuttingPlane`'s `bounds`
  keyword is silently ignored by OpenFOAM **Foundation**, so phase-1 planes
  spanned the whole domain and averaged TWO counter-flowing legs (velocity
  cancelled to ~0; area ~2.2× bore; section-mean p_rgh also contaminated). Fix:
  single-leg radius masking on the raw `.xy` dump (`sample_section_mean_pressure.py`
  rewritten; `diagnose_section_velocity.py` records the evidence). Verified: clean
  stations now have flow alignment 0.99–1.00, u_bulk ≈ 0.0135 m/s, dynamic head
  ≈ 0.18 Pa (small but real, ~1% of the ±20 Pa p_rgh swings).
- **#6 mainline continuation — LOCATED + VERIFIED.** The continuation field data
  is staged locally under `jadyn_runs/.../2026-06-18_convergence_and_jin_envelope_wave/runs/`
  (NOT `staging/`). `reconcile_freeze_windows.py` now searches both → 8/14 lanes
  verifiable (all nominal continuation + water; remaining 5 are hiq/loq
  perturbation lanes). Convergence (#2) rerun on the four Salt-Jin continuations:
  Salt 2/3/4 stationary (heat closes <0.1%), Salt 1 −2.08%. Section-mean (#1)
  rerun closure-grade on the salt2_jin continuation (t=7915) — consistent with
  warmup. Registry registration deferred to coordinator: see
  `operational_notes/06-26/30/2026-06-30_mainline_continuation_staging_plan.md`.

REMAINING:
1. Reconstruct salt3_jin / salt4_jin continuations and rerun #1 (same recipe; run
   reconstructPar in ONE foreground call — backgrounded runs get killed mid-merge).
2. Re-derive friction/Nu closure inputs from the continuation window (feeds the
   closure bundle; coordinate with that owner).
3. Per-station pipe-axis-aligned mask so corner (TP) stations are usable (TW
   mid-leg stations are already clean).
4. Mesh-independence study (item #5 protocol) once OF13 runtime + libRCWallBC.so
   are recovered.
