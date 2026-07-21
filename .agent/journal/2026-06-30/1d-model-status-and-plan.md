# 1D Model Status, Plan & Parallel Work Map

Date: `2026-06-30`
Author: claude (AGENT-156)
Audience: ALL subsequent agents working on the TAMU loop 1D reduced-order model.
Purpose: one place to understand where the 1D closures stand, what each closure
needs, what blocks it, and which work can proceed in parallel without collision.

Guiding principles for this work (user-stated):
1. **Disclose confidence boundaries** — state assumptions, validity windows, and
   known issues in every artifact.
2. **Scientific rigor** — every decision carries an explicit recorded "why".
3. Heavy documentation + reusable scripts so work is resumable after a break.

---

## 0. Orientation — read these first

- This file (status + plan + parallel map).
- `operational_notes/06-26/30/2026-06-30_cfd_1d_closure_workflow.md` — how to run every tool;
  the OpenFOAM env + non-mutating reconstruction recipe.
- `operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md` — LOCKED segment map
  (owner-confirmed). `tools/analyze/validate_segment_map.py` enforces it.
- `operational_notes/06-26/30/2026-06-30_mainline_continuation_staging_plan.md` — where the
  mainline continuation data lives.
- `.agent/journal/2026-06-30/claude-inspection-cfd-1d-closure-postprocessing.md` —
  the original scientific critique that started this.
- 1D model itself: `../cfd-modeling-tools/tamu_first_order_model/Fluid/` (README +
  `tamu_loop_model_v2/`); closure contract consumed from
  `.../validation_data/ethan_cfd_informed_salt_v2/one_d_state_vector.csv`.

## 1. What the 1D model solves and consumes

Steady reduced-order natural-circulation loop. Unknowns: `mdot_loop` (buoyancy vs
hydraulic loss) and `T_bulk_node[j]` (energy march). Closure terms it needs, with
current status (from `one_d_state_vector.csv`):

| Closure | Symbol | Status today |
| --- | --- | --- |
| Apparent friction factor | `fD_seg[j]` | PARTIAL — defended only `lower_leg`, `test_section_span`, Re 80–174 |
| Straight pressure loss | `Deltap_straight_seg[j]` | follows `fD` |
| Section/total pressure | `p_rgh(s)`, `p0=p_rgh+½ρu²` | static + dynamic now correct (warmup + continuation) |
| Buoyancy head | `Deltap_buoyancy_loop` | from ρ(T)–elevation; OK |
| Thermal conductance | `UAprime_seg[j]` | PRIMARY surface admitted, but stale-v1 + coarse mesh |
| Heat-transfer coeff | `HTC_seg[j]` | SECONDARY; `R'_thermal = 1/UAprime` |
| Nusselt | `Nu_seg[j]` | direct use only `left_lower_leg`; Nu(Re,Pr) NOT identifiable |
| Heater/cooler | `Q_*_seg[j]` | imposed readable BCs |
| Lumped remainders | `Deltap_residual`, `UA_lumped_residual` | calibration-only |

Segment map (LOCKED, owner-confirmed): `lower_leg` = heated bottom leg
(=`heated_incline`); `upcomer` = `left_lower_leg`+`test_section_span`+`left_upper_leg`;
`downcomer` = `right_leg`; cooler on `upper_leg`. Beware `lower_leg` vs
`left_lower_leg` (different legs).

## 2. Reusable tooling already built (AGENT-156)

All read-only on existing data unless noted; run with SYSTEM python.

- `tools/ofenv/of12_env.sh` — OpenFOAM Foundation v12 env (reads the v13 cases;
  standard-BC fields only: p, p_rgh, U, phi, rho).
- `tools/analyze/assess_time_convergence.py` — steadiness from postProcessing
  monitors (mdot + gross wall duty); normalizes net heat by gross duty.
- `tools/analyze/represent_closures_per_case.py` — honest per-case f/Nu with
  Jin/Kirst axis split, laminar-reference excess factor, dof/overfit flags,
  Re-domain guard, Pr-identifiability check.
- `tools/analyze/reconcile_freeze_windows.py` — provenance: matches freeze-window
  times to on-disk trees (searches `staging/` AND `jadyn_runs/`).
- `tools/analyze/validate_segment_map.py` — enforces the CFD↔1D segment map.
- `tools/extract/sample_section_mean_pressure.py` — section-mean p_rgh + dynamic
  head + total pressure via raw cut-plane dump + SINGLE-LEG masking.
- `tools/analyze/diagnose_section_velocity.py` — velocity-anomaly diagnostic.
- `tools/analyze/test_claude_action_items.py` — 11 unit tests (all green).

Key facts established: cases are laminar, foamRun/OF13 collated; Salt 2/3/4 Jin are
stationary (flow + gross heat duty <0.2%; heat closes <0.1%), Salt 1 weaker
(−2.08%); apparent f is 3.5–70× laminar (form-loss-dominated); mainline
CONTINUATION data is staged under
`jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/runs/`.

## UPDATE 2026-06-30 (phase 4): B1 RESOLVED + thermal done + upcomer reframed

- **B1 (OF13 runtime) RESOLVED.** T reconstructs natively: `tools/ofenv/of13_env.sh`
  (OF13 build at /work/.../2026-06-02_openfoam13 + gcc/15.2.0 libstdc++ +
  libRCWallBC.so). Phase B is UNBLOCKED. Only B2 (coarse mesh) remains.
- **Thermal closures EXTRACTED** for mainline Salt 2/3/4 Jin (HTC/UA'/Nu/R'):
  `tools/extract/sample_segment_htc_uaprime.py`, `work_products/2026-06-30_claude_thermal_htc/`.
- **Friction Re** computable: `tools/analyze/salt_properties.py` (Jin mu) +
  `--auto-mu-jin`.
- **Upcomer is a REAL convection cell** (user direction), NOT a friction segment.
  New lane: model it with convection-cell (LeFrancois Nu(Ra,Pr)) + natural-
  circulation, fit a recirculation correlation in nondim groups (Ri=Gr/Re^2, Ra,
  Re, Pr). Tool `tools/extract/sample_upcomer_convection_cell.py`; plan
  `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md`. More CFD coming
  to map onset/limits.
- Results synthesis: `reports/2026-06/2026-06-30/2026-06-30_claude_closure_results/`.

## 3. The two hard blockers (B1 now resolved — see phase-4 update above)

- **B1 — OF13 runtime + `libRCWallBC.so` not on LS6.** Blocks ALL new
  `T`-dependent extraction (HTC, UAprime, Nu) and any solver re-run. Pressure and
  friction work around it via the stored `rho` field. Tracked in
  `imports/2026-06-02_openfoam13_runtime_source.json`.
- **B2 — coarse mesh only.** No mesh-independence bound on any f/Nu/UAprime;
  project rule says medium/fine required for publishable thermal closure.
  Protocol: `operational_notes/06-26/30/2026-06-30_mesh_independence_protocol.md`.

## 4. Phased plan

### Phase A — Hydraulic closure to closure-grade (UNBLOCKED; in progress)
- A1. Absolute per-segment area `A` and `D_h = 4A/P` from the single-leg masked
  cut (extend `sample_section_mean_pressure.py`).
- A2. Reconstruct salt3/salt4_jin CONTINUATIONS; rerun section pressures on all
  Salt-Jin continuations.
- A3. Re-derive `f(Re)` on the continuation window using measured `D_h` and
  monitor `u_bulk`; per-case, Jin-only, Re-clamped.
- A4. Per-station axis-aligned mask → usable corner pressures → minor-loss `K` at
  bends (separate reversible ½ρu² from form loss) → shrink `Deltap_residual`.

### Phase B — Thermal closure refresh (BLOCKED on B1)
- B1a. Recover OF13 runtime + `libRCWallBC.so`.
- B1b. Re-extract `UAprime`/`HTC`/`Nu` per segment on the continuation with
  enthalpy-flux-weighted (ρ·u·cp) bulk T; compute `R'_thermal = 1/UAprime`.
- B1c. Replace the stale v1 surfaces in the closure bundle (coordinate with the
  closure-bundle owner).

### Phase C — Uncertainty / mesh independence (BLOCKED on B1)
- C1. 3-level GCI study on Salt 2 & 4 Jin (envelope endpoints); discretization
  bands on f and Nu.

### Phase D — Integration into the 1D solver (depends on A/B)
- D1. Wire measured `D_h`, refreshed `f`, `UAprime`/`R'` into the 1D state per
  the locked segment map; clamp queries to the fitted Re window.
- D2. Re-fit `Deltap_residual` / `UA_lumped_residual` against the refreshed
  direct closures; report the residual fraction per case.

## 5. Parallel work map (who can run simultaneously without collision)

Distinct file scopes so multiple agents (Claude or Codex) can work at once. Each
agent should claim its row on `.agent/BOARD.md` and use NEW dated files.

| Lane | Scope (claim these) | Depends on | Can run in parallel with |
| --- | --- | --- | --- |
| **L1 Hydraulic geometry+friction** | `tools/extract/sample_section_mean_pressure.py` (Claude/AGENT-156-owned — coordinate), new `tools/analyze/derive_segment_friction.py`, `work_products/2026-06-30_claude_continuation_*`, `tmp/2026-06-30_claude_action_items/**` | A1→A2→A3 sequential within lane | L2, L3, L4 |
| **L2 Minor-loss / corner pressures** | new `tools/extract/sample_corner_minor_loss_sectionmean.py`, new work_products root | A4 (needs A1 mask idea, but separate file) | L1, L3, L4 |
| **L3 Thermal extraction prep** | new `tools/extract/sample_segment_htc_uaprime.py` (write + dry-run now; runs after B1), `operational_notes/06-26/30/2026-06-30_thermal_extraction_spec.md` | code now; execution after B1 | L1, L2, L4 |
| **L4 Runtime recovery** | `imports/` OF13 runtime manifest, build scripts under a new `tools/ofenv/` subdir | independent | all |
| **L5 Mesh-independence harness** | new GCI calculator `tools/analyze/compute_gci.py`, sbatch wrappers under a new dir | code now; execution after B1 | all |
| **L6 1D integration** | `../cfd-modeling-tools/tamu_first_order_model/Fluid/**` (separate repo — coordinate on that board) | needs A3/B1b outputs | L4, L5 |

Collision rules: do NOT edit `tools/extract/sample_leg_centerline_major_loss.py`
(codex/AGENT-155) or `tools/case_analysis_profiles.py` (shared). Registry/config
edits need coordinator approval. Each lane writes its own dated work_products and
journal note.

## 6. Immediate next steps (this session, AGENT-156)

Working L1 now: A1 (absolute D_h per segment) + A2 (salt3/salt4_jin continuation
section pressures) + A3 (continuation-based friction). L3 spec + L5 GCI calculator
authored now (code-only, runnable once B1 clears). See the dated work_products and
the continuation/velocity journal for results.
