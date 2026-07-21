# End-of-Day Handoff: 2026-07-08

Date: `2026-07-08`
Agent Role: Coordinator / Writer (claude)
Task: End-of-session context transfer — no new analysis, documentation only.

**Purpose**: Capture full context from today's Claude session so analysis can
resume tomorrow without re-reading all source material. This supplements (does not
replace) the Codex daily rollup at
`.agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md`
(AGENT-212) and the Codex provenance closeout at
`.agent/journal/2026-07-08/codex-day-provenance-closeout.md` (AGENT-214).

---

## 1. What Claude Did Today (AGENT-210)

All work is under AGENT-210. Status: COMPLETE. Tests: 134/134 Fluid, 353/353 repo.

### 1.1 F6 friction closure: phi × F3_shah_apparent

**What**: Added `dp_F6_phi_re()` to `friction_closures.py` and `AVAILABLE_FORMS`.
The closure multiplies F3_shah_apparent apparent friction by a leg-class-specific
phi(Re) factor fitted from 9 calibration points (Salt 2/3/4 Jin, 3 leg classes).

**Power-law fits** (`phi = a × Re^b`, OLS log-log space):

| leg_class | a | b | method | calibration Re range |
|---|---|---|---|---|
| heater | 2.0505 | −0.0272 | power law | 68–123 |
| cooler | 1.9177 | −0.0502 | power law | 63–115 |
| downcomer | — | — | constant phi_mean=1.8112 | 61–118 |
| upcomer | — | — | fallback: phi=1.0 (F3 only) | — |

**Calibration data source**: `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`
(produced AGENT-200, 2026-07-07). Key column used: `f_corrected_over_flam`.
phi = f_corrected_over_flam / f3_shah_ratio, where f3_shah_ratio was computed
from Shah (1978) Eq. 15 applied to each span's Re and x+ = L/(D_h × Re).

**Why downcomer uses constant**: The phi increases with Re for the downcomer
(S2: phi=1.542 at Re=61; S3: phi=1.823 at Re=85; S4: phi=2.069 at Re=118).
This is Ri-driven, not Re-driven: S2 has Ri=1.375 (strong buoyancy aids
downfall → lower apparent friction), S3/S4 have Ri≈0.61. A Re power law for
the downcomer would be physically wrong; constant phi_mean=1.811 is a
conservative placeholder until Ri-corrected fitting is possible.

**F6 wired to solver**: F6 dispatch added in `_friction_closure_kwargs_for_segment`
in `solver.py`. Passes `leg_class` from `_F4_LEG_CLASS_BY_PARENT_SEGMENT`.

**Key limitation — F6 is NOT publication-grade**:
- 3 calibration points per fit, 2 free parameters → 1 DOF. Standard errors on
  `a` and `b` are not constrained by the data.
- No validation split. Reported errors are training errors only.
- Re extrapolation: calibration Re=62–123; design target Re=200–400 is 2–3×
  outside the calibration range. F6 extrapolates as a power law with no bound.
- Heater R²≈0.3: the trend is barely detectable; b=−0.027 is not statistically
  distinguishable from b=0.
- Downcomer phi=1.811 constant overpredicts S2 by ~18% (true phi=1.542 at S2).
- MinorLosses K reconciliation is PENDING: phi calibration is from straight-pipe
  cut planes (no corner contribution), so phi is a "pipe-only" multiplier. If the
  solver MinorLosses K values match the CFD-measured K values, no double-counting
  occurs. If they differ, there is a potential overcounting of corner losses.

**F6 files**:
- Implementation: `../cfd-modeling-tools/.../friction_closures.py` (added `_F6_PHI_RE_FITS`, `_f6_phi`, `dp_F6_phi_re`)
- Solver dispatch: `../cfd-modeling-tools/.../solver.py` (friction_form="F6_phi_re")
- Tests: `../cfd-modeling-tools/.../tests/test_friction_closures.py` (14 new tests, TestF6PhiRe)

---

### 1.2 Self-consistent Ri per segment in solver

**What**: Added `compute_segment_ri(state, segment, case) → float` to `solver.py`
and `segment_ri: Dict[str, float]` field to `ModelResult`. The Ri is computed from
solver-state quantities only — no CFD-derived Ri needed.

**Formula**:
```
V = Re × μ / (ρ × D_h)
|ΔT_wall_bulk| ≈ |Q_net| × R_i_prime / L_seg
β = 0.7497 / ρ   (Jin EOS: dρ/dT = −0.7497)
Ri = g × β × |ΔT| × D_h / V²
```

**Status**: Diagnostic only. Stored in `ModelResult.segment_ri` per segment name.
Does NOT yet feed back into friction computation.

**Answer to user question — "would self-consistent Ri fix the F5 fit?"**:
Removing circularity (no longer need CFD Ri) is necessary but not sufficient.
The fundamental problems remain: (1) still 3 operating points with 0 DOF once
you account for the 2-parameter fit; (2) Ri and Re still co-vary in natural
circulation at constant Q — you need different Q levels (T13 campaign) to break
the collinearity; (3) the dominant phi excess is NOT Ri-driven (confirmed by
minor loss study — see 1.3). Self-consistent Ri will become genuinely useful
once T13 provides 5–8 operating points spanning independent Re and Ri variation.

**Limitations**:
- ΔT_wall_bulk uses R_i_prime from the 1D thermal model's Nusselt correlation
  (not from CFD wall temperatures). In the laminar developing regime (Re=60–120),
  Gnielinski/Dittus-Boelter are extrapolated beyond their validity range; ΔT
  errors of ±50% are plausible.
- Circularity: when Ri eventually feeds back into F5, it will require a converged
  outer iteration between friction and thermal state.
- D_h mismatch: solver uses `segment.inner_diameter_in × 0.0254` for D_h.
  CFD uses global D_h=22.098 mm. Test section difference: 20.9 vs. 22.098 mm
  (5.7% → ~11% Ri bias).

---

### 1.3 Minor loss separation study

**What**: Ran local analysis (`work_products/2026-07-08_minor_loss_separation/`)
quantifying how much of the phi excess above F3_shah is attributable to the four
corner bends, using 50-50 attribution of each corner's K×q_dyn to adjacent spans.

**Results**:

| leg_class | phi_original (mean) | phi_pipe_only (mean) | corners explain |
|---|---|---|---|
| heater | 1.8135 | 1.6350 | 9.8% of span ΔP |
| cooler | 1.5352 | 1.3906 | 9.4% of span ΔP |
| downcomer | 1.8112 | 1.6514 | 8.8% of span ΔP |
| upcomer | 0.7584 | 0.6001 | 20.9% (unreliable — recirculation) |

**Main finding**: The dominant phi excess (~1.4–1.9×) above F3_shah_apparent is
NOT explained by the four corner bends. Residual phi_pipe_only = 1.39–1.65
remains after subtracting corner contributions. Physical candidates for the
residual: (1) Dean vortex secondary flow persistence in straight runs post-bend;
(2) buoyancy-driven azimuthal secondary flow in heated/cooled inclined legs.

**Codex review finding (AGENT-216)**: The minor loss separation has a
"control-volume contradiction" and should remain a sensitivity study until rebuilt.
The concern is that K values were measured at corner planes but the attribution
formula uses span-length quantities — there is an inconsistency in the control
volume definition. Use these results as motivation for further study, not as
validated physics claims.

**K values used** (CFD-measured, from `work_products/2026-07-01_claude_bend_minor_loss/`):

| Corner | K (S2) | K (S3) | K (S4) |
|---|---|---|---|
| corner_lower_left | 8.21 | 8.30 | 8.29 |
| corner_lower_right | 16.50 | 13.81 | 10.73 |
| corner_upper_right | 15.92 | 14.33 | 13.58 |
| corner_upper_left | 6.25 | 6.22 | 6.68 |

**Files**: `work_products/2026-07-08_minor_loss_separation/` (script, CSV, summary JSON, README)

---

### 1.4 Insulation cautionary note

**What**: Created `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md`
as a standing warning for future agents.

**Key fact**: CFD uses 1.4 in (35.56 mm) Calzite insulation on main piplegs and
bare 2.2 mm quartz on the test section. The 1D model's global `insulation_thickness_in
= 0.25–0.30 in` is a **temperature-matching compensating error** — NOT the physical
CFD insulation value. Using 1.4 in as the 1D global value OVERCOOLS the loop by ~60 K.

**Stopgap** (until per-segment insulation is implemented):
```python
outer_insulation_multiplier_by_parent_segment = {"pipeleg_left_04": 0.0}
insulation_thickness_in = 1.4
```

**Pending structural fix**: implement `insulation_thickness_by_parent_segment` dict in
`ScenarioConfig` so each segment has its own physical insulation value.

---

### 1.5 T13 run campaign proposal

**What**: Created `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md`.

**Goal**: Push Re to 200–400 to give F6 (and the future Ri fit) enough calibration
range and DOF.

**Q sweep from S3 anchor** (Q_S3 ≈ 298 W):

| Case label | Q (W) | Expected Re | Multiplier vs. S3 |
|---|---|---|---|
| T13-A | 595 | ~107 | 2× |
| T13-B | 1190 | ~161 | 4× |
| T13-C | 2380 | ~221 | 8× |
| T13-D | 4760 | ~305 | 16× |
| T13-E | 9520 | ~428 | 32× |

Scaling: mdot ∝ Q^(1/3) in natural circulation → Re ∝ Q^(1/3).
Re=200 requires Q ≈ 2400 W (8×S3); Re=300 requires Q ≈ 5000 W (17×S3).

**Gate**: T13 is blocked on T2/AGENT-181 gate (corrected Salt perturbation runs
3275448–3275451 must first confirm mdot actually moves with Q perturbation before
T13 can be submitted).

**Series A**: standard 1.4 in insulation, same geometry as S2/S3/S4 mainline.
**Series B** (optional): varied insulation to test Ri/Re collinearity breaking.

---

### 1.6 Authoritative geometry reference

**What**: Created `reference/geometry_reference.md` as a stable single-file
canonical reference for segment naming, flow direction, dimensions, upcomer
recirculation, test section, insulation, corner K values, and operating points.

**Also updated**: CLAUDE.md Section 6 gotcha #3 now includes a pointer to this file.

**Why**: Geometry facts were scattered across operational_notes with no single
authoritative index. Future agents should check `reference/geometry_reference.md`
FIRST before reading dated notes.

---

## 2. Full Context: What All Agents Did Today

*Cross-reference to `.agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md`
(AGENT-212) and `.agent/journal/2026-07-08/codex-day-provenance-closeout.md` (AGENT-214)
for Codex-side detail.*

| Agent | Owner | What was done | Key output |
|---|---|---|---|
| AGENT-202 | codex | CFD scenario contract: audited 0/T BCs, confirmed 1.4 in insulation in CFD, no volume radiation (qr absent) | `work_products/2026-07-08_cfd_scenario_contract/` |
| AGENT-203 | claude | Span endpoint bulk T extraction (s00/s04 cut planes); heater ΔT = +15.35/+15.79/+16.44 K for S2/S3/S4; upcomer recirculation 85-98% | `work_products/2026-07-08_span_endpoint_temperatures/` |
| AGENT-204 | claude | Ri characteristic length audit: confirmed D_h=22.098 mm global in CFD; test section 5.7% D_h overestimate; no volume radiation | `operational_notes/07-26/08/2026-07-08_ri_characteristic_length_audit.md` |
| AGENT-205 | codex | CFD/1D geometry and BC contract; Salt 1 status; corrected Salt gate status | `operational_notes/07-26/08/2026-07-08_cfd_1d_geometry_bc_contract_and_run_plan.md` |
| AGENT-206 | codex | Staged and submitted Salt 1 nominal continuation job 3282992 | `jadyn_runs/modern_runs/2026-07-08_salt1_nominal_continuation_candidate/` |
| AGENT-207 | codex | Test section heat contract; heat_enthalpy_residual_by_segment.svg | `work_products/2026-07-08_postprocessor_summary_charts/` (updated) |
| AGENT-208 | codex | Thermal boundary contract: prior 1D is 62–66 K too hot; loop ΔT 3.7–3.9 K too small | `work_products/2026-07-08_thermal_boundary_contract/` |
| AGENT-209 | codex | Thermal mismatch deep dive: current 1D cooler removes 46–54 W vs CFD 136–169 W; P1 best path: CFD cooler duty → MAE 4.5 K | `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/` |
| AGENT-210 | claude | F6 phi-vs-Re, Ri per segment, minor loss study, insulation note, T13 proposal, geometry reference | See Section 1 above |
| AGENT-211 | codex | Fixed-mdot 1D thermal replay: 21 run-plan rows, best path P1_cfd_cooler_duty_only (MAE=4.456 K); no path passes 2 K gate | `work_products/2026-07-08_cfd_informed_fixed_mdot_1d_runs/` |
| AGENT-212 | codex | Daily coordinator rollup + reusable agent prompt for tomorrow | `.agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md` |
| AGENT-213 | codex | Thermal interface power policy documented in DECISIONS.md; new TODO tasks added | `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md` |
| AGENT-214 | codex | Codex day provenance closeout; updated `journals/2026-07/2026-07-08_ethan_runs.md` | `.agent/journal/2026-07-08/codex-day-provenance-closeout.md` |
| AGENT-215 | codex | Opened TODO-HEAT-ENTHALPY-INTERFACE-LEDGER task | BOARD.md updated |
| AGENT-216 | codex | Rigor review of Claude's closure fits: diagnostic/candidate only, not publication-grade | `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md` |
| AGENT-217 | codex | Reorganized work_products by month/day with backward-compat symlinks | `work_products/2026-07/`, `work_products/2026-06/` |
| TODO-OBSERVATION-TABLE-CONTRACT | codex | 423 observation rows; 342 pressure, 81 thermal, 45 fit-eligible | `work_products/2026-07-08_closure_observation_table/` |
| TODO-PRESSURE-TERM-LEDGER | codex | 18 rows, 12 fit-eligible, 6 recirculation-excluded; explicit buoyancy/development/minor/residual decomposition | `work_products/2026-07-08_pressure_term_ledger/` |
| TODO-PATCHWISE-HEAT-LEDGER | codex | 24 rows; heater imposed > wallHeatFlux; cooler ≈ wallHeatFlux; test section net sink | `work_products/2026-07-08_patchwise_heat_ledger/` |
| TODO-POSTPROCESSOR-CHARTS | codex | 7 SVG figures ready for presentation | `work_products/2026-07-08_postprocessor_summary_charts/` |
| TODO-MINOR-LOSS-TWO-TAP | codex | 15 rows; K_apparent 6.2–16.5; K_local 1.1–8.7; test-section connector rows flagged as raw-extraction-required | `work_products/2026-07-08_minor_loss_two_tap/` |
| TODO-MODEL-FORM-BAKEOFF | codex | Starter bakeoff from 423 obs rows; best current mdot form = F3_shah_apparent (MAE 2.669%) | `work_products/2026-07-08_model_form_bakeoff/` |
| TODO-UPCOMER-ONSET | codex | 3 admitted rows; all classify as recirculation_cell_observed | `work_products/2026-07-08_upcomer_onset/` |

---

## 3. Current State of Key Quantities

### 3.1 Friction closure hierarchy (as of end-of-day)

| Form | Status | mdot MAE (S2/S3/S4) | Notes |
|---|---|---|---|
| F1 (64/Re) | candidate_screen | +9.7% to +18.0% | Underpredicts friction → high mdot |
| F3_shah_apparent | **current best** | −0.9% to +3.7% | Only 1 DOF free (length scale choice) |
| F3_hagenbach | candidate_screen | similar to F3_shah | Hagenbach entry term adds ~1–2% |
| F4_leg_class | candidate_screen FAILING | −24.7% to −23.2% | Over-stiffens; large negative mdot error |
| F5_ri_corrected | degenerate with F3 | same as F3 | c=0 all leg classes; failed Ri fit |
| F6_phi_re | prototype | not yet scored end-to-end | 3-point calibration; extrapolation risk |

**Critical**: F4 suppresses mdot by 23–25% because it applies a per-leg-class
multiplier that over-increases friction for all leg classes simultaneously. F4 was
intended to capture geometry-specific effects but the calibration does not have
enough DOF to separate geometry from operating conditions.

### 3.2 Thermal state

- Prior 1D (F3, default insulation): loop mean-T ~62–66 K above CFD. Loop ΔT
  ~3.7–3.9 K too small.
- Root cause: 1D cooler removes 46–54 W; CFD cooler removes 136–169 W. The 1D
  HX model is severely under-removing heat.
- Best fixed-mdot thermal repair: prescribe CFD cooler wallHeatFlux duty only
  (P1_cfd_cooler_duty_only) → MAE = 4.456 K, max = 6.219 K. Still fails 2 K gate.
- The thermal mismatch is NOT primarily a friction problem. Fixing the cooler
  duty path is the highest-leverage thermal action.
- **No path currently passes the strict 2 K mean-T + 1 K loop-ΔT gate.**

### 3.3 Active CFD jobs (as of 2026-07-08)

| Job | Case | Status | Purpose |
|---|---|---|---|
| 3275448–3275451 | Salt 1-4 corrected Q perturbations | Pending/running | T2: confirm mdot moves with Q |
| 3282992 | Salt 1 nominal continuation | Submitted, pending priority | Salt 1 convergence continuation |

**Gate**: No corrected Salt data can be used for closure fitting until AGENT-181
formally admits them. Watch for mdot movement in jobs 3275448–3275451. If mdot
moves, T13 can be designed around the confirmed Re-vs-Q scaling.

### 3.4 Upcomer regime

- All 3 admitted Salt cases: recirculation_cell_observed
- Backflow fraction: 27.8% (S2) → 17.2% (S4), decreasing with Re but never zero
- The upcomer should be modeled separately (AGENT-196 correlation: bf = 0.0539 + 15.93/Re)
  and is NOT included in F6 (falls back to F3 baseline, phi=1.0)
- Do NOT use the upcomer for standard pipe friction fitting until onset Re is bounded

---

## 4. Key Limitations (All Lanes)

**These must be stated before any presentation claim or paper use:**

1. **No mesh/GCI bounds**: TODO-MESH-UNCERTAINTY is still open. All friction,
   pressure, and thermal numbers from CFD are from a single mesh. Publication-grade
   coefficient claims are not possible without GCI.

2. **No held-out validation split**: F4, F5, F6 are all calibrated on the full
   3-point dataset (S2/S3/S4). All reported errors are training errors.

3. **F5 is degenerate**: Ri-corrected friction coefficients are zero; F5 behaves
   identically to F3_shah_apparent.

4. **F6 is 3-point extrapolating**: calibrated at Re=62–123, target Re=200–400.
   Not suitable for publication; suitable for scoping T13.

5. **Minor loss separation has control-volume inconsistency** (AGENT-216 review):
   K values are measured at corner planes but attribution uses span-level quantities.
   Treat as sensitivity study, not physics claim.

6. **Insulation mismatch**: 1D global 0.25–0.30 in is a compensating error, not
   physical. Per-segment insulation is not yet implemented.

7. **Corrected Salt perturbations unqualified**: jobs 3275448–3275451 not yet
   admitted. Do not use as closure evidence.

8. **Thermal mismatch not yet closed**: best path (P1) leaves 4.456 K MAE. The
   loop temperature is not quantitatively right until the cooler model is fixed.

9. **Upcomer onset not bounded from below**: AGENT-196 correlation extrapolates
   below Re=68. Onset Re is unknown; the loop may remain in the recirculation
   regime across all physical operating points.

---

## 5. Prioritized Next Steps for Tomorrow

### 5.1 Immediate (unblock downstream work)

**A. MinorLosses K reconciliation** *(1–2 hours)*
Check what K values the solver's `MinorLosses` class uses by default vs. the
CFD-measured K values in `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv`.
If they match: F6 phi_original (1.54–1.81) is the right value (no double-counting).
If they differ: need to either adjust phi or adjust the solver K values.
This must be resolved before any F6-based 1D run is cited.

**B. Check corrected Salt job status** *(15 minutes)*
```bash
ssh login3.ls6.tacc.utexas.edu "squeue -u $USER | grep -E '327544[89]|327545[01]|3282992'"
```
If 3275448–3275451 are complete: postprocess to check if mdot moved. If mdot
moved in any case, AGENT-181 gate may open and T13 can be submitted.

**C. Fix cooler model** *(HIGH priority — highest leverage thermal action)*
The 1D cooler/HX removes 46–54 W; CFD cooler removes 136–169 W. Options:
- Prescribe CFD cooler wallHeatFlux as fixed boundary condition (thermal replay mode)
- OR implement a proper cooler model using CFD Nu/HTC and correct UA'
See AGENT-209/211 outputs for the prescribed-duty approach and
`work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/` for analysis.
See `operational_notes/07-26/08/2026-07-08_thermal_interface_power_policy.md`
for the policy decision (use CFD wallHeatFlux, not idealized wattage).

### 5.2 Closure quality improvement

**D. Per-segment insulation in ScenarioConfig** *(medium effort)*
Implement `insulation_thickness_by_parent_segment` dict so the 1.4 in piplegs
and the bare test section can be modeled simultaneously. This removes the
compensating-error pattern and is a prerequisite for any thermal accuracy claim.
See `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md` for
the specification.

**E. F6 end-to-end solver run** *(short)*
Run the 1D solver with `friction_form="F6_phi_re"` on S2/S3/S4 and compare
mdot and pressure distribution to F3_shah_apparent. This test does not exist yet
(only unit tests of `dp_F6_phi_re()` function exist; no solver-level integration test).

**F. Sub-span friction profile** *(investigative)*
Check whether f_corrected at the s00/s02 vs. s02/s04 sub-intervals differs.
This would quantify Dean vortex entry effect on distributed friction and help
attribute the phi_pipe_only = 1.39–1.65 residual to entry vs. buoyancy-secondary
effects.

### 5.3 Extending the calibration basis

**G. T13 campaign submission** *(pending gate)*
Gate: T2/AGENT-181 must first confirm corrected Salt jobs moved mdot.
Once cleared: submit T13 series A (5 cases, Q = 595–9520 W from S3 anchor).
See `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md`.
This is the critical step to give F6 (and a future Ri fit) real predictive DOF.

**H. Targeted literature forms** *(TODO-TARGETED-LITREV-FORMS still open)*
Translate literature correlations (Shah, Baehr-Stephan, Petukhov, Gnielinski
mixed convection) into candidate equations with verified constants, validity
ranges, and branch conditions. Do NOT implement until constants are verified
from primary source.

### 5.4 Publication prerequisites (longer term)

**I. Mesh uncertainty / GCI** *(TODO-MESH-UNCERTAINTY, BLOCKED on external mesh)*
Needs Ethan to provide coarse/medium/fine mesh levels. Without GCI bounds,
all closure coefficient claims have unknown discretization uncertainty.

**J. Time-window uncertainty quantification**
Tag quasi-steady windows, drift, block means, autocorrelation for all admitted
cases. Currently assumed to be adequately converged; not formally quantified.

**K. Held-out validation split**
Once T13 data exists, split: S2/S3/S4 for fitting, T13 cases for validation.
Until then, no out-of-sample performance is known.

---

## 6. Files Produced or Modified Today (Claude scope)

### New files
| File | Purpose |
|---|---|
| `../cfd-modeling-tools/.../friction_closures.py` | F6_phi_re closure added |
| `../cfd-modeling-tools/.../solver.py` | compute_segment_ri(), segment_ri in ModelResult, F6 dispatch |
| `../cfd-modeling-tools/.../tests/test_friction_closures.py` | 14 F6 tests |
| `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md` | Standing insulation warning |
| `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md` | Re 200–400 campaign design |
| `work_products/2026-07-08_minor_loss_separation/` | Minor loss study (4 files) |
| `reference/geometry_reference.md` | Canonical geometry reference |
| `.agent/status/2026-07-08_AGENT-210.md` | AGENT-210 status |
| `imports/2026-07-08_f6_ri_segment_minor_loss.json` | Session import manifest |
| `.agent/journal/2026-07-08/implementer-f6-ri-segment-minor-loss-study.md` | Detailed AGENT-210 journal |

### Modified files
| File | What changed |
|---|---|
| `CLAUDE.md` | Section 6 gotcha #3 — pointer to `reference/geometry_reference.md` |
| `.agent/BOARD.md` | AGENT-210 row STATUS → COMPLETE |

---

## 7. Reading Order for Tomorrow's Agent

To pick up efficiently, read in this order:

1. `AGENTS.md` — coordination rules (required by protocol)
2. `.agent/BOARD.md` — current active rows (AGENT-211, 212 still active; claim a new row before editing)
3. This file (already done)
4. `reference/geometry_reference.md` — geometry facts
5. `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md` — before touching insulation
6. `.agent/journal/2026-07-08/coordinator-daily-analysis-rollup-and-presentation-agent-prompt.md` — full Codex side of today's work + presentation guidance
7. `work_products/2026-07-08_thermal_mismatch_remedy_deep_dive/README.md` — if working on thermal lane
8. `work_products/2026-07-08_model_form_bakeoff/README.md` — if working on friction closure lane
9. `operational_notes/07-26/08/2026-07-08_claude_literature_closure_fit_rigor_review.md` — before claiming any fit is publication-ready
10. `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md` — before submitting T13

**Do NOT start the day by running new CFD postprocessing.** The July 8 packages
are comprehensive. The highest-leverage next actions are: (A) MinorLosses K
reconciliation, (B) check corrected Salt job status, and (C) cooler model fix.
All three can be done with existing data.

---

## 8. Provenance Summary

| Work product | Source inputs | Trustworthiness |
|---|---|---|
| F6 phi calibration | Salt 2/3/4 Jin mainline (AGENT-162, 200) | Diagnostic; 3-point, no DOF |
| Ri per segment (solver) | 1D model state only | First-order estimate; ±50% possible |
| Minor loss study | bend_minor_loss (AGENT-162), momentum_budget (AGENT-162) | Sensitivity study; control-volume inconsistency |
| Model bakeoff (F3 best) | 423 observation rows, AGENT-195 friction comparison | Starter; training-error only |
| Thermal mismatch diagnosis | patchwise_heat_ledger, thermal_boundary_contract | Solid 3D→1D energy-balance diagnosis |
| Fixed-mdot thermal replay | CFD wallHeatFlux, Fluid solver | 4.456 K MAE; not gate-passing |
| Pressure decomposition | momentum budget, pressure term ledger | 3D postprocessing; admission-status gated |
| Corner K values | bend_minor_loss two-tap (AGENT-162, TODO-MINOR-LOSS-TWO-TAP) | K_apparent = upper bound; K_local = best available but not raw-tap corrected for test section |
| Salt 1 continuation (job 3282992) | June 25 base continuation tree | Pending; not yet admitted |
| Corrected Salt Q (jobs 3275448–3275451) | July 4 corrected staging | Pending gate; not yet closure evidence |
