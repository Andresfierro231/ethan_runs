# End-of-Day Handoff — 2026-07-07

**Date:** 2026-07-07  
**Agent role:** Coordinator / Writer  
**Task:** AGENT-201  
**Written by:** claude (end-of-session)

---

## How to use this file

Read this file first in tomorrow's session BEFORE touching any code.
Then read the files listed in "Priority reading order" below.
The session started as a crash-recovery from a previous session.

---

## Priority reading order (tomorrow morning)

Read in this order to rebuild context:

1. **This file** — full session narrative
2. **`.agent/BOARD.md`** — check for any new codex claims overnight
3. **`CLAUDE.md`** — standing rules (OF13 env, probe-CSV gotchas, no-login-node rule)
4. **`operational_notes/07-26/07/2026-07-07_cfd_postprocessing_closure_rigor_deep_dive.md`** — the master contract document for all closure work (updated today by AGENT-188/189/190)
5. **`work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`** — the key result: F3_shah ≈ best form
6. **`work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`** — F5 Ri fit: all c=0, why this matters
7. **`work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv`** — unified per-span pressure decomposition (corrected)

---

## Running SLURM jobs at end of day

```
JOBID    NAME                  STATE    TIME_ELAPSED  LIMIT    NODE
3275449  corr_saltq_g2         RUNNING  3d 09:20      5d       c318-011
3275448  corr_saltq_g1         RUNNING  3d 09:30      5d       c318-017
3275560  corr_saltq_salt4_all  RUNNING  3d 07:35      5d       c318-018
3279547  idv83624 (idev)       RUNNING  9:25          4d 4h    c318-008
```

**Gate job 3279646 (saltq_gate_0707) was CANCELLED** at 19:27:23 today (Elapsed = 00:00:00 — never ran).

**AGENT-191 (codex) re-submitted the gate as job 3280969** via `ssh login3`. It is currently PENDING with dependency `afterany:3275448:3275449:3275560`. This means **no manual gate re-submission is needed tomorrow** — job 3280969 will fire automatically when any of the corrected Salt jobs finishes.

Verify gate status tomorrow morning:
```bash
ssh login3.ls6.tacc.utexas.edu "squeue -j 3280969 -o '%i|%j|%T|%P|%M|%l|%E|%r'"
```

**Estimated job completion:** Jobs 3275448/3275449/3275560 have 5-day limits and were submitted 2026-07-04. They will expire by ~2026-07-09 morning at the latest.

**Interactive node c318-008** (idev job 3279547) still has ~18.5 hours of life remaining. This is the node for AGENT-198 (span endpoint T extraction, deferred) if that work is prioritized tomorrow.

---

## What happened today — full session narrative

### Context at session start (crash recovery)

Previous session had ended mid-work. Board showed AGENT-190 (codex, complete) as the most recent agent. The session was oriented via BOARD.md and status files.

### Codex agents already complete at session start

These were done by the codex agent pair before today's claude session:

| Agent | Task | Key output |
|---|---|---|
| AGENT-191 (codex) | F4/Ri calibration and solver gate | `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/` — 18-row calibration table; friction_closures.py hardened (F4 raises on unknown segment) |
| AGENT-192 (codex) | Time-window quasi-steady UQ tool | `work_products/2026-07-07_time_window_quasi_steady_uq/` — curates monitor windows into quasi-steady observations with oscillation-aware UQ, independence_group_id, and gate propagation |

### Jin per-leg gap analysis (pre-existing, completed earlier)

Job ran locally on c318-008 (PID 94224), completed ~14:54. All outputs in:
`work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/`

**Key finding:** At matched insulation thickness (S2: 0.25 in, S3/4: 0.30 in):
- F1 default: mdot error +9.7% / +16.2% / +18.0% (S2/S3/S4)
- Per-leg CFD friction applied: flips to −23.8% — gap REVERSES sign
- **Conclusion: the mdot gap is NOT primarily a friction issue. It is buoyancy/ΔT-driven.**

### AGENT-193: Unified Pressure Term Ledger

**What:** First unified per-segment pressure decomposition for Salt 2/3/4 Jin.  
**Who:** claude (Implementer)  
**Editable scope claimed:** `tools/analyze/build_pressure_term_ledger.py`, tests, `work_products/2026-07-07_pressure_term_ledger/`

**Method:** Joined three previously separate data sources:
1. `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` — de-buoyed friction + buoyancy per span
2. `work_products/2026-07-01_claude_segment_friction/segment_friction.csv` — arc lengths, D_h
3. `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv` — bend K values (S2/S3/S4)

**Key correction discovered:** The plan's residual formula `gross − buoyancy − distributed − dev − minor` was algebraically inconsistent with the momentum budget identity. Correct residual is the inertial term (≈ 0.1%). Development_loss and minor_loss are diagnostic columns, not part of the momentum balance residual.

**Outputs:**
- `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.csv` — 18 rows (3 cases × 6 spans), 22 columns
- `work_products/2026-07-07_pressure_term_ledger/pressure_term_ledger.json`
- `work_products/2026-07-07_pressure_term_ledger/README.md`
- `work_products/2026-07-07_pressure_term_ledger/summary.json`

**Key findings:**
- development_loss (Shah − F1): 17–107% of distributed per span — upcomer in deep developing-flow regime
- minor_loss at bends: 7–13% of distributed — non-negligible
- f_debuoyed round-trip error: < 1e-5

**Bug found and fixed later (AGENT-197):** Every span was treated as entry=True. Fixed in AGENT-197.

Tests: 9/9 → 11/11 after AGENT-197.

---

### AGENT-194: Heat Source/Sink Mechanistic Ledger

**What:** Per-segment patchwise heat ledger for Salt 2/3/4 Jin.  
**Who:** claude (Implementer)

**Method:** Read `postProcessing/wallHeatFlux/*/wallHeatFlux.dat` (area-integrated, column 5 = Q[W]) from continuations at `jadyn_runs/modern_runs/2026-06-18_convergence_and_jin_envelope_wave/`. Read BC types from `0/T` file (rcExternalTemperature, externalTemperature, zeroGradient).

**Outputs:**
- `tools/analyze/build_heat_source_sink_ledger.py`
- `tools/analyze/test_heat_source_sink_ledger.py`
- `work_products/2026-07-07_heat_source_sink_ledger/heat_source_sink_ledger.csv` — 24 rows
- `work_products/2026-07-07_heat_source_sink_ledger/README.md`
- `work_products/2026-07-07_heat_source_sink_ledger/summary.json`

**Key findings:**

| Case | Heater wall flux | BC-specified | Net balance |
|---|---|---|---|
| Salt 2 | 243.5 W | 265.7 W | 0.052% |
| Salt 3 | 273.2 W | 297.5 W | 0.105% |
| Salt 4 | 310.5 W | 337.6 W | 0.026% |

~9% gap between wall flux and BC-specified = insulation loss to ambient.

**Surprising finding: test section (pipeleg_left) is a NET HEAT SINK** (−5.7/−10.5/−16.8 W for S2/S3/S4) despite having an electrical heater BC. The hot upcomer fluid (456–485 K) loses heat to ambient through the quartz faster than the electric heater adds it. BC sign convention = "imposed_into_fluid" describes design intent, not actual direction.

**Known gap: enthalpy_change_W = NaN** throughout. Only mid-span T_bulk available from HTC CSV. Inlet/outlet T needed. See AGENT-198 (deferred).

Tests: 36/36.

---

### AGENT-195: Friction Closure mdot Comparison

**What:** Extended the friction forms comparison to include F3_shah_apparent and F4_leg_class in the live solver; produced mdot comparison table.  
**Who:** claude (Implementer)

**Method:** Extended `work_products/2026-07-04_friction_forms/run_friction_forms_compare.py`. Set insulation_thickness_in = 0.25 (S2) / 0.30 (S3/S4) from Jin gap analysis. Used `ScenarioConfig(friction_form="...", insulation_thickness_in=...)`.

**Also fixed:** Misleading docstring in `friction_closures.py` `dp_F3_hagenbach` — "over-estimates entry loss for x+ < 0.05" replaced with correct statement that K_∞ UNDERESTIMATES total ΔP at x+ < 1.

**Outputs:**
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
- `work_products/2026-07-07_friction_forms_comparison/README.md`
- `work_products/2026-07-07_friction_forms_comparison/summary.json`
- `imports/2026-07-07_friction_forms_mdot_comparison.json`

**KEY RESULT:**

| Form | Salt 2 err | Salt 3 err | Salt 4 err |
|---|---|---|---|
| F1 | +9.70% | +16.21% | +17.97% |
| F3_hagenbach | +3.50% | +6.69% | +5.69% |
| **F3_shah_apparent** | **−0.93%** | **+3.33%** | **+3.75%** |
| F4_leg_class | −23.19% | −23.57% | −24.66% |

**F3_shah_apparent is the best current form.** F4 over-stiffens by ~24% without Ri correction.

Tests: 45/45 Fluid tests pass.

---

### AGENT-196: Upcomer Recirculation Correlation

**What:** 3-point correlation of backflow_fraction vs Re from Salt 2/3/4 nominal data.  
**Who:** claude (Implementer/Writer)

**Data source:** Existing `work_products/2026-06-30_claude_upcomer_convection_cell/` (per-station backflow fractions, Ri, Ra).

**Dataset (TW7 / left_lower_leg representative station):**

| Case | Re | bf | Ri_median | Nu |
|---|---|---|---|---|
| salt_2_jin | 71.1 | 27.8% | 2.634 | 3.107 |
| salt_3_jin | 96.8 | 21.9% | 2.396 | 4.060 |
| salt_4_jin | 134.9 | 17.2% | 1.498 | 4.986 |

**Fit:** `bf = 0.054 + 15.93/Re` (OLS, 1 DOF). Both monotone checks pass.

**Outputs:**
- `tools/analyze/build_upcomer_correlation.py`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv`
- `work_products/2026-07-07_upcomer_correlation_v2/README.md`

**Honest limitations documented:**
1. 3-point OLS → parameter uncertainty O(1) for onset Re predictions
2. Upper upcomer (TP5/TW8/TP6) shows persistent ~30% backflow insensitive to Re — two-region structure not captured by single-station fit
3. Onset Re (~100–260 depending on route) is ~2× beyond calibration max (Re=135)

**Data needed to improve:** Corrected Q perturbation jobs 3275448–3275451.

Tests: 25/25.

---

### AGENT-197: Pressure Ledger Entry Flag Fix

**What:** Fixed Shah entry assumption applied unconditionally to all spans.  
**Who:** claude (Implementer)

**Bug:** `build_pressure_term_ledger.py` passed `is_segment_entry=True` for every span. The upcomer has 3 contiguous sub-spans; only the first (`left_lower_leg`) is a real entry. `test_section_span` and `left_upper_leg` receive developed flow → Shah entry assumption is physically wrong, causing `dev_frac > 1.0` for Salt 3/4.

**Fix:**
- Added `SPAN_IS_ENTRY = {"lower_leg": True, "left_lower_leg": True, "test_section_span": False, "left_upper_leg": False, "upper_leg": True, "right_leg": True}`
- `development_loss_pa = 0.0` for non-entry spans
- New `flow_reset_flag` column in output CSV (True/False)
- Regenerated all 4 output files in `work_products/2026-07-07_pressure_term_ledger/`

Tests: 11/11.

---

### AGENT-199: Solver.py F4 Stub Segments Fix

**What:** Added 4 missing horizontal manifold stubs to `_F4_LEG_CLASS_BY_PARENT_SEGMENT`.  
**Who:** claude (Implementer)

**Names confirmed from geometry.py:** Exact names `top_horizontal_inlet`, `top_horizontal_exit`, `bottom_horizontal_inlet`, `bottom_horizontal_exit` — matched expectations.

**Downstream-classification principle adopted** (from AGENT-195 runtime patch):

| Segment | Leg class | Feeds into |
|---|---|---|
| top_horizontal_inlet | cooler | cooler inlet |
| top_horizontal_exit | downcomer | downcomer top |
| bottom_horizontal_inlet | heater | heater inlet |
| bottom_horizontal_exit | upcomer | upcomer bottom |

Note: The plan's suggested assignment (cooler/cooler/downcomer/heater) was inconsistent. The downstream-classification principle is physically cleaner.

**Files changed:**
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` — 4 dict entries added with flow-direction comments
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py` — `TestF4StubMapping` class with 7 tests

Tests: 52/52 Fluid, 299/299 full suite.

---

### AGENT-200: F5 Richardson-Number-Corrected Friction Form

**What:** Implemented `dp_F5_ri_corrected()` in friction_closures.py; wired into solver.py.  
**Who:** claude (Implementer)

**Fit result:** 1-parameter forced-intercept OLS `phi = 1 + c * Ri_streamwise` per leg class. **All three leg classes (heater, cooler, downcomer) returned R² < 0 → c set to 0.0.** F5 currently reduces to F3_shah_apparent identically.

**Why R² < 0:** With 3 points and 1 forced-intercept parameter and 0 DOF, R² can be negative when the data trend is non-monotone or the variance around the fit line exceeds the total variance. This is a genuine data-limitation result — not a bug. AGENT-191 (codex) found the same thing earlier.

**Framework is complete and ready:**
- `_F5_RI_COEFFICIENTS` dict in friction_closures.py (c=0 for all classes currently)
- `dp_F5_ri_corrected(Re, rho, v, L, D, is_entry, Ri_streamwise, leg_class)` — fires UserWarning at every call
- Registered in `AVAILABLE_FORMS` as `"F5_ri_corrected"`
- `ri_table: Dict[str, float]` field added to `ScenarioConfig` in solver.py
- `_friction_closure_kwargs_for_segment` extended to dispatch F5 kwargs

**Path to unblocking F5:** Once corrected Q perturbation runs (3275448/3275449/3275560) qualify through the gate, expanded Ri range (Re ~40–200 instead of 68–135) should allow a non-degenerate fit. Re-fit is a 1-line change per leg class in `_F5_RI_COEFFICIENTS`.

**Outputs:**
- `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv`
- `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv`
- `work_products/2026-07-07_f5_ri_corrected/run_f5_mdot_comparison.py`
- `work_products/2026-07-07_f5_ri_corrected/README.md`
- `imports/2026-07-07_f5_ri_corrected.json`

Tests: 61/61 Fluid, 299/299 full suite.

---

## Final test suite state

```
299 passed in 14.61s
```

61 Fluid tests (friction_closures + solver) also pass separately.

---

## Complete new artifacts from today's session

### New tools
| Tool | What it does |
|---|---|
| `tools/analyze/build_pressure_term_ledger.py` | Joins momentum_budget + segment_friction + bend_minor_loss into unified per-span pressure ledger |
| `tools/analyze/build_heat_source_sink_ledger.py` | Per-patch wallHeatFlux integrals with BC types, sign convention, residual |
| `tools/analyze/build_upcomer_correlation.py` | Compiles 3-point upcomer dataset, fits bf=f(Re) |
| `tools/analyze/build_time_window_quasi_steady_observations.py` | Curates monitor windows into quasi-steady obs (codex, AGENT-192) |
| `tools/analyze/build_f4_ri_calibration_and_solver_gate.py` | F4/Ri calibration table + evidence freeze (codex, AGENT-191) |

### Modified tools
| Tool | Change |
|---|---|
| `../cfd-modeling-tools/.../friction_closures.py` | Added F5_ri_corrected; fixed F3h docstring; upcomer warning (prior session) |
| `../cfd-modeling-tools/.../solver.py` | Added ri_table to ScenarioConfig; F5 dispatch; 4 stub segments |
| `tools/analyze/build_pressure_term_ledger.py` | SPAN_IS_ENTRY dict; flow_reset_flag column; non-entry spans → dev_loss=0 |

### New work products
| Directory | Contents | Rows/Files |
|---|---|---|
| `work_products/2026-07-07_pressure_term_ledger/` | Per-span pressure decomposition S2/3/4 | 18 rows |
| `work_products/2026-07-07_heat_source_sink_ledger/` | Per-patch heat ledger S2/3/4 | 24 rows |
| `work_products/2026-07-07_friction_forms_comparison/` | mdot comparison F1/F3h/F3_shah/F4 | 12 rows |
| `work_products/2026-07-07_upcomer_correlation_v2/` | 3-point bf=f(Re) correlation | 3 rows |
| `work_products/2026-07-07_f5_ri_corrected/` | F5 fit summary + mdot comparison | — |
| `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/` | F4/Ri calibration table (codex) | 18 rows |
| `work_products/2026-07-07_time_window_quasi_steady_uq/` | Quasi-steady observation curation (codex) | 144 candidate windows |

---

## Key scientific findings summary

1. **Mdot gap is buoyancy-driven, not friction-driven.** Applying per-leg CFD friction at matched T reverses the error sign (+10–18% → −20–24%). F3_shah_apparent is the best current friction form.

2. **F3_shah_apparent is the recommended production closure** (−0.93% S2, +3.3% S3/S4). Use `friction_form="F3_shah_apparent"` in ScenarioConfig.

3. **F4_leg_class over-stiffens by ~24%** without a Ri correction. F5 framework is ready but c=0 until corrected Q runs expand the Ri calibration range.

4. **Test section is a net heat sink** (−5.7 to −16.8 W) despite having a heater BC. The hot upcomer fluid loses more heat to ambient through quartz than the heater adds.

5. **Upcomer has a two-region structure:** lower upcomer backflow decreases with Re (15–28%); upper upcomer shows persistent ~30% backflow insensitive to Re. A single-station fit cannot resolve both. Data-limited to 3 operating points until corrected Q jobs qualify.

6. **Shah entry assumption is invalid for mid-loop sub-spans.** `test_section_span` and `left_upper_leg` receive developed flow from `left_lower_leg` — `development_loss_pa = 0.0` is correct for these (fixed in AGENT-197).

7. **Pressure ledger residual formula required correction.** The plan's formula was algebraically inconsistent with the momentum budget identity. The correct closure check is the inertial term (≈ 0.1%).

---

## Open items for tomorrow

### Priority 1 — Monitor corrected Salt jobs + gate
- Check status of 3275448 (corr_saltq_g1), 3275449 (corr_saltq_g2), 3275560 (corr_saltq_salt4_all)
- **Gate job 3280969 is already queued** (AGENT-191/codex re-submitted it); verify it is still PENDING or has fired
- If gate completes: check its output for mdot movement (should move 3–5% from nominal per Q^(1/3))
- Command to check: `ssh login3.ls6.tacc.utexas.edu "squeue -u andresfierro231"`

### Priority 2 — Run gap analysis job 3275531 results
If job 3275531 (Jin per-leg gap analysis, submitted 2026-07-04) produced any postprocessing outputs, review them.

### Priority 3 — AGENT-198: Span endpoint T extraction (deferred)
Write script to run foamPostProcess at span boundary stations (first and last centerline label per span) using OF13 env on reconstructed cases. Enables computing `enthalpy_change_W` in heat ledger.
- Reconstructed cases: `tmp/2026-06-30_claude_action_items/recon_salt{2,3,4}_of13/`
- Reuse `enthalpy_flux_bulk_t()` from `tools/extract/sample_segment_htc_uaprime.py:576–633`
- Must run on c318-008 or new idev (current idev 3279547 has ~18.5h remaining)
- Do NOT source OF13 env when running Python afterward

### Priority 4 — F5 Ri re-fit
Once corrected Q perturbation runs qualify:
- Load expanded f4_ri_calibration_table with new operating points
- Re-fit `_F5_RI_COEFFICIENTS` per leg class (1 line per class in friction_closures.py)
- Re-run mdot comparison to see if F5 improves on F3_shah

### Priority 5 — Pressure ledger: development_loss validity audit
`left_upper_leg` development_loss is now 0.0 (correct for mid-loop sub-span). But: is the Shah entry for `test_section_span` from `left_lower_leg` correct? The test section has a different bore (20.9 mm vs 22.1 mm elsewhere) — there may be a geometry change at the junction that resets the boundary layer. This is a question for tomorrow's coordinator review.

### Priority 6 — Salt 1 qualification (TODO-SALT1-STEADY-QUAL)
Still on the board. Salt 1 cannot be admitted to closure fitting until qualified. Low priority until corrected Q jobs finish.

---

## Overnight runs needed

**NO immediate action required.**

Gate job **3280969** was already re-submitted by AGENT-191 (codex) tonight with `afterany:3275448:3275449:3275560` dependency. It will fire automatically when the corrected Salt jobs complete. Nothing needs to be manually submitted tonight.

**Optional overnight action:** If c318-008 (idv83624) is still alive tomorrow morning (~18.5h remaining), the AGENT-198 span endpoint T extraction could be submitted there. Low priority.

**No new CFD runs** are needed. The corrected Salt Q perturbations (3275448/3275449/3275560) are the critical path; gate job 3280969 will postprocess them automatically.

---

## Files changed by today's session (complete list)

### In ethan_runs repo:
- `tools/analyze/build_pressure_term_ledger.py` — new + updated (AGENT-193, AGENT-197)
- `tools/analyze/test_pressure_term_ledger.py` — new + updated
- `tools/analyze/build_heat_source_sink_ledger.py` — new (AGENT-194)
- `tools/analyze/test_heat_source_sink_ledger.py` — new
- `tools/analyze/build_upcomer_correlation.py` — new (AGENT-196)
- `tools/analyze/test_build_upcomer_correlation.py` — new
- `tools/analyze/build_time_window_quasi_steady_observations.py` — new (codex AGENT-192)
- `tools/analyze/test_time_window_quasi_steady_observations.py` — new
- `tools/analyze/build_f4_ri_calibration_and_solver_gate.py` — new (codex AGENT-191)
- `tools/analyze/test_build_f4_ri_calibration_and_solver_gate.py` — new
- `work_products/2026-07-07_pressure_term_ledger/` — new (regenerated by AGENT-197)
- `work_products/2026-07-07_heat_source_sink_ledger/` — new
- `work_products/2026-07-07_friction_forms_comparison/` — new
- `work_products/2026-07-07_upcomer_correlation_v2/` — new
- `work_products/2026-07-07_f5_ri_corrected/` — new
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/` — new (codex)
- `work_products/2026-07-07_time_window_quasi_steady_uq/` — new (codex)
- `work_products/2026-07-07_time_window_quasi_steady_contract/` — new (codex)
- `imports/2026-07-07_friction_forms_mdot_comparison.json` — new
- `imports/2026-07-07_f5_ri_corrected.json` — new
- `imports/2026-07-07_heat_source_sink_ledger.json` — new
- `.agent/BOARD.md` — updated (new agent rows 193–201)
- `.agent/status/2026-07-07_AGENT-193.md` through `_AGENT-201.md` — new
- `.agent/journal/2026-07-07/*.md` — all entries from today

### In cfd-modeling-tools repo:
- `tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py` — F5 added; F3h docstring fixed; F4 upcomer warning (prior); F4 requires explicit leg context (codex AGENT-191)
- `tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` — ri_table field; F5 dispatch; 4 stub segments added (AGENT-199); F4 routing hardened (codex AGENT-191)
- `tamu_first_order_model/Fluid/tests/test_friction_closures.py` — F5 tests (AGENT-200); stub mapping tests (AGENT-199)

---

## Gotchas to remember

1. **OF13 env required for T reconstruction** — source `tools/ofenv/of13_env.sh` + `module load gcc/15.2.0`. Do NOT source when running Python (swaps libstdc++).
2. **Probe CSV is schematic** — `lower_leg` in CSV = downcomer in mesh; `right_leg` in CSV = heater. Use mesh PCA centerlines.
3. **Characteristic Ri = section MEDIAN** not mean (differ by ~100×).
4. **Sbatch from compute nodes**: `ssh login3.ls6.tacc.utexas.edu "/usr/bin/sbatch <absolute_path>"`
5. **F5 always fires UserWarning** — expected behavior, not a bug.
6. **F4 now raises ValueError** on unknown segments (AGENT-191 hardening). Stubs are now fixed (AGENT-199).
7. **test_section_span and left_upper_leg** have `development_loss_pa = 0.0` (correct — receive developed flow). If you see them as 0 in the ledger, that's right.
8. **Gate job 3279646 was cancelled** — must re-submit when corrected Salt jobs finish.
