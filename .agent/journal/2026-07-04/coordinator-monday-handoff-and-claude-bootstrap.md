# Coordinator: Monday Handoff + Claude Bootstrap

**Date:** 2026-07-04 (Independence Day)
**Session type:** Handoff + documentation + job submission
**Author:** claude (AGENT-179 equivalent)

---

## 1. What happened today (2026-07-04)

### 1.1 Corrected Salt Q perturbation runs (AGENT-178 / codex)

Six previous launch attempts (3275388–3275436) failed due to cascading bugs in
the restart-field patch pipeline:
- launcher bootstrap error
- Slurm comma-array export bug
- broken post-OF `python` path in patcher
- collated `decomposedBlockData` frame corruption
- missing parent `dynamicCode/`

Final corrected submission: **3275448–3275451** (4 jobs, groups 1–4).
All 14 Salt Jin Q perturbation cases distributed across the 4 jobs.
At session end: groups 1–3 running, group 4 running (all 4 confirmed).

**Key requirement before using any result**: confirm each job wrote
`preflight_patch_audit_<job>.csv` AND that `mdot` actually moved from nominal
by ~Q^(1/3) and re-plateaued. Do NOT use a case that stayed at nominal mdot.

### 1.2 Physics decomposition of pressure drop (claude)

The 1D model previously had only one friction path (64/Re for all segments).
The user asked to decompose pressure drop correctly and compare multiple forms.

**Created:** `cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
- `SegmentDpBreakdown` dataclass (dp_fd, dp_entry, f_D_fd, f_D_apparent, Re, x_plus)
- `dp_F1`: 64/Re fully-developed laminar — no entry correction
- `dp_F3_hagenbach`: F1 + Shah (1978) Hagenbach K∞=1.33 at each segment entry
- `AVAILABLE_FORMS` registry + `compute_dp()` factory

**Modified:** `solver.py` — added `friction_form: str = "F1"` to `ScenarioConfig`;
`distributed_and_minor_losses()` now calls `compute_dp(friction_form, ...)` per
segment. Backward-compatible: default = "F1".

**Key finding:** Hagenbach explains 42–79% of excess f in the upcomer (short segment,
L=0.12m) but only 4–8% in the heater/cooler (long segments, L=0.35m). Residual
2–3× gap in heated/cooled vertical legs is NOT entry-length — it is
buoyancy-modified velocity profile (next F4 closure to implement).

**Solver impact:** F3h vs F1: mdot drops 13–19% (Salt 2–4). Moves in right direction
but insufficient to close the factor-2 gap vs CFD; need F4 buoyancy correction.

**Created:** `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py`
— comparison script that loads CFD momentum budget and computes F1, F3h per span.

**NOT implemented:** FRIC-FIT-001 (`log(f_D) = 5.23 − 0.948 log(Re) + 2.92 I[ts]`).
Investigation showed `target_value` in the training CSV is NOT standard Darcy f_D
(values ~46 for test section at Re≈97, physically implausible). Do not use until
normalization is resolved.

### 1.3 Documentation gap fixed

Claude was booting without the repo coordination context that Codex gets from
`AGENTS.md`. Root cause: no `CLAUDE.md` equivalent existed.

**Created:** `CLAUDE.md` at repo root — mirrors the Codex startup protocol for
Claude, including required reading order, current phase summary, open tasks,
key file paths, hard gotchas, and documentation landscape.

### 1.4 Gap analysis job submitted

**Job 3275531** (development queue, 45 min): per-leg friction gap diagnosis.
- insulation sweep (50 points × 3 salts × 2 radiation states)
- matched-T closure comparison
- per-leg friction test
- f(Re) fit (Salt 1 pending integration)

Outputs: `work_products/2026-07-04_jin_perleg_gap_analysis/`

---

## 2. Current running jobs (as of 2026-07-04 EOD)

| Job | Name | Partition | Status | What it does |
|---|---|---|---|---|
| 3265970 | ethan_w1234_ne5d | NuclearEnergy | RUNNING | Water cases (W1–4); freeze + postprocess when done |
| 3275322 | idv02362 | NuclearEnergy-dev | RUNNING | Interactive dev node (c318-009) |
| 3275363 | water_post_3265970 | development | PENDING (dependency) | Water postprocess — runs after 3265970 |
| 3275448–3275451 | corr_saltq_g1–g4 | NuclearEnergy | RUNNING | Corrected Salt Q perturbations |
| 3275531 | jin_perleg_gap | development | SUBMITTED | Per-leg gap analysis + insulation sweep |

---

## 3. Monday morning checklist

On Monday, before starting new work:

### Step 1: Check job outcomes

```bash
squeue -u andresfierro231
# Or check sacct for completed jobs:
sacct -u andresfierro231 --format=JobID,JobName%24,State,ExitCode,Elapsed --starttime=2026-07-04
```

**For perturbation jobs (3275448–3275451):**
```bash
# Check that mdot actually moved (if jobs are done):
ls jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/
# Look at postProcessing/*/0/flowRateInletValue* or equivalent mdot monitor
```

**For gap analysis (3275531):**
```bash
cat work_products/2026-07-04_jin_perleg_gap_analysis/slurm-jin_perleg_gap-3275531.out
ls work_products/2026-07-04_jin_perleg_gap_analysis/
```

### Step 2: If perturbation jobs completed correctly
- Run the operating-point gate: `python tools/analyze/assess_time_convergence.py --require-moved-from <nominal_mdot>`
- If any passes: feed it into the upcomer correlation (T10)
- If all fail: extend runtime and resubmit, or escalate to T13 design

### Step 3: If gap analysis (3275531) completed
- Review `work_products/2026-07-04_jin_perleg_gap_analysis/` outputs
- The insulation sweep results will show how sensitive mdot is to the wall h knob
- Use to calibrate the F4 buoyancy-modified closure next

### Step 4: Next 1D model implementation
The friction closure hierarchy needs **F4** next:
- **F4: Buoyancy-modified friction** for heated/cooled vertical legs
- Reference: Aicher & Martin (1997) laminar mixed-convection correction, or
  Martinelli & Boelter (1942) type Ri correction: `f = f_fd × (1 + C × Ri^n)`
- The 2–3× residual gap in the heater (lower_leg) and cooler (upper_leg) after F3h
  is the target. The downcomer (right_leg) also shows 1.4–2.8× residual.
- Implement in `friction_closures.py` as `dp_F4_buoyancy(Re, Ri, rho, v, L, D, is_entry)`
- Wire into solver as `friction_form = "F4_buoyancy"` on `ScenarioConfig`
- Richardson number Ri available from CFD; need to expose it in the 1D model
  (use Ri = Gr/Re² with local ΔT = T_wall - T_bulk from the solver's thermal state)

### Step 5: More friction forms from lit review
The user also asked to compare many correlation forms. Add these to `friction_closures.py`:
- Baehr & Stephan laminar (thermal entry correction)
- Churchill-Usagi composite
- Per-leg CFD multiplier lookup (already in `friction_multiplier_by_parent_segment`)
- Literature correlations from LitRev ch04

---

## 4. Physics decomposition roadmap (full picture)

The user's stated goal: *"correct your model so that it considers buoyancy, thermal
development, hydraulic development, minor losses, major losses, etc separately."*

| Term | Status | Where in solver | Next step |
|---|---|---|---|
| **Major losses** (distributed friction) | Partially modeled | `distributed_and_minor_losses()` | Add F4, more forms |
| **Minor losses** (K) | Implemented | `MinorLosses` + `_effective_friction_multiplier` | Renormalize bend-K (current values are upper bounds) |
| **Hydraulic entry** (Hagenbach) | Implemented (F3h) | `friction_closures.py` | Already wired |
| **Thermal entry** (developing Nu) | NOT modeled | Nu is constant per leg | Add Graetz-Lévêque or Shah composite |
| **Buoyancy body force** | Correctly separated | `buoyancy_pressure()` | Already correct |
| **Buoyancy-modified friction** | NOT modeled | Partially captured by F5 per-leg mult | F4 next |
| **Recirculation in upcomer** | NOT modeled (only patch bypass) | Treated as single-stream | Needs upcomer cell model |

**Buoyancy is already a SEPARATE term** in `buoyancy_pressure()` — this is correct.
Do NOT double-count it by adding a buoyancy term to the friction loop.

---

## 5. Documentation consolidation recommendation

Notes are currently spread across 5 locations:

1. `.agent/journal/YYYY-MM-DD/` — raw agent session notes (active, keep as-is)
2. `operational_notes/YY-YY/MM/` — durable method notes (active, keep as-is)
3. `journals/2026-06/` — curated daily journal (stopped 2026-06-30; archive only)
4. `work_products/*/README.md` — product-specific notes (active, keep as-is)
5. `reports/` — final analysis packages (active, keep as-is)

**Recommendation:**
- Treat `journals/2026-06/` as a read-only archive; no new entries.
- All new session notes → `.agent/journal/YYYY-MM-DD/`
- All new method/decision notes → `operational_notes/YYYY-MM-DD/`
- The BOARD.md + DECISIONS.md + AGENTS.md + CLAUDE.md combination now gives both
  Codex and Claude a good bootstrap context.
- The main remaining gap was CLAUDE.md — now created.

**No file moves needed** — the archive vs active split is already well-defined.
The problem was not structure, it was missing CLAUDE.md.

---

## 6. What Claude needs from Ethan on Monday

1. **T6 blocker**: Ethan needs to provide the NCC parametric mesh generator OR
   pre-built medium + fine polyMesh directories for Salt 2 and 4 Jin. Without these,
   GCI bounds cannot be computed. See `operational_notes/07-26/01/2026-07-01_T6_gci_blocker_ethan_request.md`.

2. **Perturbation run approval**: Once the corrected jobs (3275448–3451) finish,
   confirm whether the mdot movement is acceptable for the upcomer correlation.

3. **LitRev friction forms list**: The user mentioned comparing "many friction forms
   we had shown in the past from the lit review." Please point to the specific
   LitRev section or provide a list of the desired correlation names so they can be
   implemented in `friction_closures.py`.

4. **F4 Ri correction target**: Confirm the preferred Richardson-number correction
   form for the heated/cooled legs (e.g. Aicher & Martin, or other reference).

---

## 7. Honest assessment of model status

**What the 1D model gets right:**
- Buoyancy driver (separated correctly)
- Thermal closures for heater (HTC/Nu calibrated from CFD)
- Global mass-flow order of magnitude

**What it still gets wrong by a factor 2:**
- Per-leg friction in heated/cooled verticals: model predicts 64/Re (or with entry
  correction ~1.5× larger), CFD shows 2–3× fully-developed laminar
- Upcomer: no recirculation model; model treats it as simple forward flow
- Minor loss K: bend-K normalization problem makes current values unreliable as
  absolute loss coefficients

**Confidence in the comparison framework:**
- F1 vs F3h comparison is solid — both use the same CFD momentum budget for reference
- The residual-gap analysis is trustworthy for identifying where the next closure is needed
- FRIC-FIT-001 must not be used until its normalization convention is resolved
