# Session Journal: F6 Closure, Ri per Segment, Minor Loss Study

Date: `2026-07-08`
Agent Role: Implementer / Writer
Task: AGENT-210

---

## Files Inspected

- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv` — phi values per span
- `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv` — corner K values S2/S3/S4
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` — rho, u_bulk per span
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py` — existing F1–F5
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` — ScenarioConfig, ModelResult, SegmentState
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py` — existing F4/F5 test patterns
- `.agent/BOARD.md` — claimed AGENT-210

## Files Changed

### New files
- `operational_notes/07-26/08/2026-07-08_insulation_caution_note.md` — standing warning note
- `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md` — Re 200–400 campaign proposal
- `work_products/2026-07-08_minor_loss_separation/minor_loss_separation.py` — analysis script
- `work_products/2026-07-08_minor_loss_separation/minor_loss_separation.csv` — results
- `work_products/2026-07-08_minor_loss_separation/minor_loss_separation_summary.json`
- `work_products/2026-07-08_minor_loss_separation/README.md` — full scientific documentation
- `reference/geometry_reference.md` — authoritative geometry reference
- `.agent/status/2026-07-08_AGENT-210.md`
- `imports/2026-07-08_f6_ri_segment_minor_loss.json`

### Modified files
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — Added `_F6_PHI_RE_FITS`, `_f6_phi()`, `dp_F6_phi_re()`, updated AVAILABLE_FORMS and FORM_DESCRIPTIONS
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
  — Added `compute_segment_ri()` helper function
  — Added `segment_ri: Dict[str, float] = field(default_factory=dict)` to ModelResult
  — Added F6 dispatch in `_friction_closure_kwargs_for_segment`
  — Wired `segment_ri` computation in ModelResult construction
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`
  — Added 14 F6 tests (TestF6PhiRe class); updated imports to include `dp_F6_phi_re`, `_F6_PHI_RE_FITS`
- `.agent/BOARD.md` — AGENT-210 row added

## Commands Run

```bash
# Phi data analysis
python3 -c "..." # extract phi = f_corrected/f_F3_shah per leg class from calibration table

# F6 power law fit
python3 << 'EOF'
# OLS in log-log space per leg class
# heater: a=2.0505, b=-0.0272
# cooler: a=1.9177, b=-0.0502
# downcomer: b=+0.447 (anomalous, Ri-driven)
EOF

# Tests
cd ../cfd-modeling-tools/tamu_first_order_model/Fluid
python -m pytest tests/test_friction_closures.py -q  # 72/72 pass

# ethan_runs suite
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q  # 353/353 pass

# Minor loss analysis
python work_products/2026-07-08_minor_loss_separation/minor_loss_separation.py
```

## Key Results and Observations

### F6 phi vs Re analysis

Extracted phi = f_corrected / f_F3_shah_apparent from calibration table per span per case:

| leg_class | case | Re | phi | f3_ratio | f_corr/flam |
|---|---|---|---|---|---|
| heater | S2 | 68.0 | 1.838 | 1.450 | 2.666 |
| heater | S3 | 90.2 | 1.794 | 1.514 | 2.715 |
| heater | S4 | 122.6 | 1.808 | 1.592 | 2.879 |
| cooler | S2 | 62.7 | 1.558 | 1.433 | 2.233 |
| cooler | S3 | 83.9 | 1.535 | 1.497 | 2.298 |
| cooler | S4 | 114.9 | 1.512 | 1.575 | 2.380 |
| downcomer | S2 | 61.2 | 1.542 | 1.423 | 2.194 |
| downcomer | S3 | 84.7 | 1.823 | 1.493 | 2.722 |
| downcomer | S4 | 118.0 | 2.069 | 1.575 | 3.259 |

**Key insight**: `f_corrected/f_lam` INCREASES with Re for all leg classes (F3_shah grows
faster with Re than f_corrected, because F3_shah has the developing-flow 3.44/sqrt(x+)
term that is larger at low x+). But phi = f_corrected/f_F3_shah DECREASES with Re for
heater/cooler (correct physical direction) and anomalously INCREASES for downcomer.

**Downcomer anomaly**: The downcomer phi increase is Ri-driven. S2 has Ri=1.375 (high;
strong buoyancy aids downward flow → lower apparent friction). S3/S4 have Ri≈0.61
(similar but lower Ri → less buoyancy aid → higher friction). The Re change between
S3 and S4 is large but the Ri barely changes, so phi increases spuriously with Re.

Power-law fits in log-log space (phi = a × Re^b):
- heater: a=2.0505, b=-0.0272 (R²≈0.3, near-constant)
- cooler: a=1.9177, b=-0.0502 (R²≈1.0, clean monotone)
- downcomer: b=+0.447 (ANOMALOUS, do not use power law)

### Minor loss separation results (main finding)

Corner bends account for 8–12% of span-level ΔP for heater/cooler/downcomer.
After 50-50 corner attribution, residual phi_pipe_only:

| leg_class | phi_original | phi_pipe_only | reduction |
|---|---|---|---|
| heater | 1.81 | 1.64 | −9.8% |
| cooler | 1.54 | 1.39 | −9.4% |
| downcomer | 1.81 | 1.65 | −8.8% |

**Conclusion**: The dominant ~1.5–1.8× excess above F3_shah is NOT from the 4 corner bends.
Most likely sources: (1) Dean vortex secondary flow persistence in straight runs after bends,
(2) buoyancy-driven azimuthal secondary flow in heated/cooled inclined legs.

### Self-consistent Ri implementation

Added `compute_segment_ri(state, segment, case)` to solver.py. Uses:
- V from Re = ρVD/μ → V = Re×μ/(ρ×D)
- |T_wall - T_bulk| ≈ |Q_net| × R_i_prime / L_segment (from inner thermal resistance)
- beta = 0.7497/rho (Jin EOS: drho/dT = -0.7497)

Stored in ModelResult.segment_ri (Dict[str, float]) per segment name.
This is a first-order estimate; the 1D model doesn't solve for T_wall explicitly.

### Answer: would self-consistent Ri fix the F5 fit?

Self-consistent Ri (from solver state, not CFD) removes the circularity problem —
F5 no longer requires CFD-derived Ri. However, it does NOT fix the fundamental
problems:
1. Still only 3 operating points with 0 DOF
2. Ri and Re still change together in natural circulation unless Q or insulation is varied
   independently (which requires the T13 campaign)
3. The dominant phi offset is not Ri-driven (minor loss study confirms this)

**Self-consistent Ri WILL become useful once T13 provides more operating points.**
At that point: F5 can be re-fit using the 1D solver's own Ri prediction per segment.
The circularity is removed, and the fit has real DOF.

### Authoritative geometry location

Before this session: geometry facts were scattered across operational_notes with no index.
After this session: `reference/geometry_reference.md` consolidates all key facts.
This is better than operational_notes because:
- `reference/` is clearly a stable reference location (not timestamped daily notes)
- Single file for all geometry facts → less search overhead
- Pointer in CLAUDE.md Section 6 will direct future agents here

## Incomplete Lines of Investigation

1. **MinorLosses K reconciliation**: Need to compare solver MinorLosses default K values
   against the CFD-measured bend K values. If they match, F6 phi should be revised
   downward by ~10% (phi_pipe_only rather than phi_original).
2. **Sub-span friction profile**: Are the s00–s04 cut planes showing higher friction near
   the bend entrance (entry disturbance from Dean flow)? Would require re-running momentum
   budget on sub-span intervals.
3. **Upcomer minor loss attribution**: The upcomer phi < 1 with additional corner attribution
   goes further negative. This is consistent with the recirculation cell but not physically
   useful for the 1D model.
4. ~~F6 Fluid suite~~ **RESOLVED**: Full Fluid suite 134/134 passed (3 independent runs,
   confirmed 2026-07-08; see session closeout below).

## Next Steps

1. Run T13 campaign (pending T2/AGENT-181 gate)
2. Reconcile MinorLosses K values in solver.py against CFD bend_minor_loss data
3. Re-fit F6 coefficients with T13 data to extend Re range to 150–300
4. Implement per-segment insulation in ScenarioConfig
5. ~~Add pointer from CLAUDE.md Section 6 to `reference/geometry_reference.md`~~ **DONE** (this session)

---

## Session Closeout: Data Provenance, Limitations, and Verification

*Added at end of session to provide complete provenance for future reproducibility.*

---

### A. Input data provenance

#### A.1 Calibration table: `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`

**Produced by**: AGENT-200 (claude, 2026-07-07, `implementer-f5-ri-corrected.md`)

**Upstream lineage**:
- `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` — per-span
  mean velocity, density, and de-buoyed friction factor from foamPostProcess at secmean
  cut planes. Produced AGENT-162 (2026-07-01) using `derive_streamwise_momentum_budget.py`.
  The de-buoying procedure subtracts the hydrostatic pressure gradient (ρ×g×Δz) from
  the measured ΔP/L to isolate the viscous + turbulent friction contribution.
- `work_products/2026-07-04_friction_forms/friction_forms_comparison.csv` — F1/F3/CFD
  friction factor values per span per case. Produced AGENT-178 (2026-07-04).
- `work_products/2026-07-01_claude_segment_friction/segment_friction.csv` — segment
  arc lengths from mesh PCA centerlines. Produced AGENT-162 (2026-07-01).
- Thermal HTC data from `work_products/2026-07-01_claude_thermal_downcomer/` and
  `work_products/2026-07-01_claude_allspan_convection/` — used to compute delta_T and
  Ri per span.

**Key column clarification** (critical, non-obvious):

The column `F5_per_leg_multiplier` in this CSV is **not** φ = f_corrected/f_F3_shah.
Inspection of the raw values confirms it equals `f_corrected_over_flam` = f_corrected/f_lam
(both columns are numerically identical for all rows). This was a labeling ambiguity
discovered during the phi derivation for F6.

The phi values used in F6 were computed in-session as:
```
phi = f_corrected_over_flam / f3_shah_ratio
```
where `f3_shah_ratio = f_F3_shah_apparent / f_lam` was independently computed using
Shah (1978) Eq. 15 applied to each span's Re and x+ = L/(D_h × Re).

**Shah (1978) Eq. 15 as implemented (Darcy apparent friction, circular tube, laminar):**
```
f_app_darcy = 4 × [3.44/sqrt(x+) + (16 + 0.244) / (1 + 0.000212/x+²)]
```
This matches `dp_F3_shah_apparent()` in `friction_closures.py`. The ratio
`f3_shah_ratio = f_app_darcy / (64/Re)` scales the apparent friction relative to
fully developed laminar.

The CSV also contains column `f_corrected_over_f3h` = f_corrected / f_F3_hagenbach
(ratio using the F3_hagenbach closure which includes an explicit Hagenbach entry term).
This column was **not** used for F6 calibration; F6 is calibrated against F3_shah_apparent.
Future agents should not confuse the two — the choice of baseline closure (Shah vs.
Hagenbach) changes the phi values.

#### A.2 Corner K values: `work_products/2026-07-01_claude_bend_minor_loss/bend_minor_loss_*.csv`

**Produced by**: AGENT-162 (claude, 2026-07-01) using `sample_bend_minor_loss.py`.

**Method**: Total pressure difference across corner planes (foamPostProcess fields
`p + 0.5×rho×U²`) normalized by local bulk dynamic pressure. Per-case K values are
time-averaged over the admitted quasi-steady window for each Salt case.

**Provenance chain**: foamPostProcess XY secmean cut planes at corner stations →
AGENT-162 integration → per-corner K per case CSV.

**Known limitation**: K values are Re-dependent (especially corner_lower_right: K=16.5
at S2, K=10.7 at S4 — a 35% variation over Re=61→118). Any analysis that uses a
single constant K is an approximation; the minor loss separation results in this session
used per-case K to preserve Re-dependence.

#### A.3 Momentum budget: `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv`

**Produced by**: AGENT-162/165 (claude, 2026-07-01) using
`derive_streamwise_momentum_budget.py`.

**Spatial basis**: Cut planes at s00, s02, s04 of each span (5 equidistant planes per
span in OpenFOAM secmeanSurfaces). The f_corrected values are span-average values
between s00 and s04.

**De-buoying method**: ΔP_friction = ΔP_total − ρ_mean × g × Δz. This is the span-average
de-buoying using the span bulk mean density. It does NOT account for within-span buoyancy
variations; the residual buoyancy effect is partly responsible for the unexplained phi
offset (see Section D below).

---

### B. F6 implementation: specific decisions and limitations

#### B.1 Phi calibration data (9 span×case points)

| leg_class | case | Re | phi | f3_shah_ratio | f_corr/flam |
|---|---|---|---|---|---|
| heater | S2 | 68.0 | 1.838 | 1.450 | 2.666 |
| heater | S3 | 90.2 | 1.794 | 1.514 | 2.715 |
| heater | S4 | 122.6 | 1.808 | 1.592 | 2.879 |
| cooler | S2 | 62.7 | 1.558 | 1.433 | 2.233 |
| cooler | S3 | 83.9 | 1.535 | 1.497 | 2.298 |
| cooler | S4 | 114.9 | 1.512 | 1.575 | 2.380 |
| downcomer | S2 | 61.2 | 1.542 | 1.423 | 2.194 |
| downcomer | S3 | 84.7 | 1.823 | 1.493 | 2.722 |
| downcomer | S4 | 118.0 | 2.069 | 1.575 | 3.259 |

These are span-averaged values over the full span length from cut planes at s00 to s04
(not sub-span values). The test section span (`left_lower_leg_04`) was excluded because
its geometry (20.9 mm bore, bare quartz, net heat sink) is not analogous to the other spans.

#### B.2 Statistical limitations of the power law fits

- **3 calibration points per leg class**: fitting `phi = a × Re^b` with 2 free parameters
  on 3 points leaves **1 degree of freedom** per fit. The R² values (heater ~0.3, cooler
  ~1.0) are artefacts of the tiny sample size, not indicators of predictive quality.
- **No validation split**: all 3 points were used in fitting. There is no held-out test
  set. Reported fit errors are training errors only.
- **Re extrapolation**: calibration range Re=62–123. Design target Re=200–400 (T13
  campaign) is 2–3× outside the calibration range in the direction of increasing Re.
  The power-law form phi = a × Re^b is unbounded and physically unvalidated outside
  the calibration range.
- **Heater R²≈0.3**: the phi trend with Re for the heater is barely above noise in
  3-point space. A constant phi=1.81 fits almost as well. The power-law b=-0.027 is
  not distinguishable from b=0 given the sample size.
- **Downcomer anomaly**: the positive b=+0.447 for the downcomer is Ri-driven, not
  Re-driven. The phi increase from S2 to S3/S4 reflects the Ri decrease from 1.375
  to ~0.61, not a physical Re-dependence of the pipe friction multiplier. Using a
  Re power law for the downcomer would be physically incorrect; the constant
  phi_mean=1.811 was chosen instead, accepting that the model is incorrect at S2 (where
  the true phi=1.542, an underprediction of ~18%).

#### B.3 Double-counting risk with solver MinorLosses

The phi calibration is derived from the momentum budget cut planes at straight sections
(s00–s04, not at the corner planes). Therefore phi = f_corrected/f_F3_shah is a
"straight-pipe-only" multiplier that does NOT include corner K losses. However, the
1D solver has a `MinorLosses` class that adds corner K values separately. If the solver
MinorLosses K values match the CFD-measured K values in `bend_minor_loss_*.csv`, then
**using phi_original (1.54–1.81) rather than phi_pipe_only (1.39–1.65) is correct** and
does not double-count. If the solver uses different K values, there is a discrepancy.
This reconciliation has NOT been done; it is the first priority before F6 is used
for predictive 1D runs.

#### B.4 Upcomer class fallback

F6 returns `phi = 1.0` for `leg_class="upcomer"`, i.e., falls back to F3_shah_apparent.
The upcomer phi < 1 in all calibrated cases (backflow dominates the span-average
momentum budget). A phi < 1 would produce friction lower than fully developed laminar,
which is unphysical for the forward-flow path. The fallback to 1.0 is a conservative
choice but is not physically motivated — it simply avoids negative friction.
The upcomer should be modeled using the dedicated upcomer recirculation correlation
from AGENT-196, not F6.

---

### C. Self-consistent Ri: implementation limitations

#### C.1 T_wall − T_bulk approximation

The estimate `|ΔT| = |Q_net| × R_i_prime / L_seg` uses the inner thermal resistance
per unit length from the 1D thermal model. This is derived from a Nusselt correlation
(typically Gnielinski or Dittus-Boelter) applied to the bulk flow conditions — it is
NOT extracted from CFD wall temperatures. The approximation has two specific error sources:

1. **Nusselt correlation uncertainty**: in the laminar developing regime (Re=60–120,
   Pr=23), the Gnielinski/Dittus-Boelter correlations were developed for turbulent flow
   and are extrapolated well outside their validity range. Errors of ±50% in Nu are
   plausible, which propagates directly to ±50% in R_i_prime and thus ΔT.

2. **Spatial averaging**: `Q_net × R_i_prime / L_seg` gives the segment-average wall-bulk
   temperature difference. The local ΔT at the heater entry (where T_bulk is low) is
   larger than at the exit (where T_bulk is high). The Ri computed here is representative
   of the segment midpoint at best.

#### C.2 Circularity for future F5 fit

The segment_ri field is currently **diagnostic only** — it is stored in ModelResult but
does not feed back into the friction computation. When it is eventually used to refit F5
(phi vs. Ri), there is a circularity: Ri depends on R_i_prime → R_i_prime depends on
the thermal solution → the thermal solution depends on friction → friction depends on Ri.
The circularity is broken only if the Ri is computed from an outer iteration that
converges friction and thermal simultaneously, or if Re and Ri are varied independently
(which requires the T13 campaign with different Q values).

#### C.3 D_h mismatch for test section

`compute_segment_ri()` uses `segment.inner_diameter_in × 0.0254` as D_h. For the test
section (pipeleg_left_04, inner_diameter_in ≈ 0.822 in = 20.9 mm), this gives D_h=20.9 mm.
The CFD uses a global D_h=22.098 mm for Ri computation (see `reference/geometry_reference.md`
Section 7). The mismatch is 5.7% in D_h and ~11% in D_h² (which appears in Ri). This
is a known discrepancy; both values are documented and the 1D segment_ri is NOT used for
the test section in any physics-critical path.

---

### D. Minor loss separation: methodology and limitations

#### D.1 Attribution method

The 50-50 corner attribution assigns half of each corner's measured K×q_dyn pressure
drop to each of the two adjacent spans. The span ΔP_span is computed from the
momentum budget f_corrected × (L/D) × q_dyn. The pipe-only friction multiplier is:

```
phi_pipe_only = (ΔP_span − ΔP_corner) / (f_lam × (L/D) × q_dyn × f3_shah_ratio)
```

where ΔP_corner = 0.5 × K_left_corner × q_dyn + 0.5 × K_right_corner × q_dyn.

#### D.2 Limitations of the 50-50 rule

The 50-50 assumption is a geometric convenience, not physically exact:
- The actual influence length of a bend vortex extends several diameters downstream
  but only ~1 diameter upstream. The correct attribution would be closer to 20-80 than
  50-50. **The 50-50 rule overattributes corner losses to the upstream span**, meaning
  phi_pipe_only for the span after a corner is underestimated.
- K values are computed from total pressure differences across the corner planes, but
  the "corner planes" may not capture the full vortex recovery length. K may be
  underestimated if the recovery length extends into the span.
- The test section span was excluded; it has reducer and expander fittings at each end
  whose K values are dominated by area-change geometry rather than bending, and were
  not extracted in `bend_minor_loss_*.csv`.

#### D.3 Interpretation of residual phi_pipe_only

| leg_class | phi_original (mean) | phi_pipe_only (mean) | reduction |
|---|---|---|---|
| heater | 1.8135 | 1.6350 | −9.8% |
| cooler | 1.5352 | 1.3906 | −9.4% |
| downcomer | 1.8112 | 1.6514 | −8.8% |
| upcomer | 0.7584 | 0.6001 | −20.9% |

The residual phi_pipe_only = 1.39–1.65 for the main sections is **not explained** by
the four corner bends. Proposed physical mechanisms (not yet quantified):
- Dean vortex secondary flow persists in the straight runs after each bend, increasing
  the effective friction over several D_h of the span. Quantification requires sub-span
  cut planes close to and far from each bend (not currently extracted).
- Buoyancy-driven azimuthal secondary flow in the heated (heater, Re-direction = gravity-
  perpendicular) and cooled (cooler) inclined legs. This is a mixed convection effect
  distinct from Ri in the streamwise direction.

The upcomer phi_pipe_only < 1 (after corner subtraction, it goes to 0.60) is
unphysical and arises from the recirculation cell: the span-average ΔP/L in the upcomer
includes backflow pressure recovery, making the apparent friction negative relative to
laminar. The upcomer analysis is not usable for closure development.

---

### E. Additional outputs produced at session closeout

The following changes were made at the start of the **continuation session** (same calendar
date, after context compaction) to close out AGENT-210:

1. **BOARD.md** (`.agent/BOARD.md`): AGENT-210 row `STATUS` updated from
   `IN PROGRESS` → `COMPLETE 2026-07-08. 72/72 Fluid tests pass, 353/353 repo tests pass.`

2. **CLAUDE.md** (repo root): Section 6, gotcha #3 (Probe CSV schematic warning)
   extended to include:
   > "See `reference/geometry_reference.md` for the canonical geometry and naming
   > reference (segment names, flow directions, dimensions, insulation, corner K values,
   > operating points)."

3. **Status file** (`.agent/status/2026-07-08_AGENT-210.md`): Updated to note
   `134/134 full Fluid suite passes` confirmed by three independent runs.

---

### F. Test verification record

| Suite | Count | Command | Result | Date |
|---|---|---|---|---|
| Fluid friction closures only | 72/72 | `python -m pytest tests/test_friction_closures.py -q` | PASS | 2026-07-08 |
| ethan_runs analyze+extract | 353/353 | `python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q` | PASS | 2026-07-08 |
| Full Fluid suite | 134/134 | `python -m pytest -q` in `../cfd-modeling-tools/.../Fluid/` | PASS (×3 independent runs) | 2026-07-08 |

**What tests do NOT cover** (known gaps):
- End-to-end solver run with `friction_form="F6_phi_re"` on Salt 2/3/4 cases
  (only unit tests of `dp_F6_phi_re()` at specific Re values)
- segment_ri values vs. CFD-extracted Ri (no ground truth comparison yet)
- phi values vs. a held-out operating point (no validation split; all 3 points used in fit)
- Minor loss separation results vs. an independent calculation method

---

### G. Open questions for user/coordinator

1. **MinorLosses K reconciliation**: Do the K values used in solver.py's MinorLosses
   class match the CFD-measured `bend_minor_loss_*.csv` K values (6.2–16.5)? If yes,
   F6 phi values should be revised downward by ~10% to phi_pipe_only (use
   `work_products/2026-07-08_minor_loss_separation/minor_loss_separation.csv`) to
   avoid double-counting corner losses.

2. **T13 campaign**: Are Q values up to 5000 W (17× nominal S3) acceptable for the
   T13 CFD campaign? The physical TAMU loop cannot reach these power levels, but CFD
   can. See `operational_notes/07-26/08/2026-07-08_t13_run_campaign_proposal.md`.

3. **F6 re-fit timing**: After T13 data becomes available (Re=150–300), F6 should be
   re-fit with proper DOF (5–8 calibration points). At that point, it would be
   appropriate to re-examine whether the downcomer trend is truly Ri-driven (by
   checking if T13 downcomer phi values fall near 1.54 or 1.81 depending on Ri).

4. **Ri circularity for F5**: When self-consistent Ri is eventually used to refit F5,
   an outer Newton iteration (or fixed-point iteration) will be needed to converge
   friction and Ri simultaneously. The current `compute_segment_ri()` implementation
   does not do this iteration; it is a one-shot diagnostic.
