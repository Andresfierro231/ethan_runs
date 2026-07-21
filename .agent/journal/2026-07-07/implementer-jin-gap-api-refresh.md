# Jin Gap Script — Full Fluid API Refresh

Date: `2026-07-07`
Task: `AGENT-183`
Role: Implementer

---

## Context

After AGENT-182 fixed `use_radiation` → `radiation_on`, the script was restarted
locally on c318-008 (PID 88711). It crashed again within step 1 with a second API
mismatch:

```
AttributeError: 'ModelResult' object has no attribute 'loop_mean_T_K'
```

The user requested a full API refresh. This entry documents the complete audit and fix.

---

## Files Inspected

| File | What was checked |
|------|-----------------|
| `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_gap_local.log` | Crash traceback |
| `../cfd-modeling-tools/.../solver.py:334` | `ModelResult` dataclass — all fields |
| `../cfd-modeling-tools/.../solver.py:233` | `SegmentState` dataclass — temperature fields |
| `../cfd-modeling-tools/.../solver.py:92` | `MinorLosses` dataclass — field names |
| `../cfd-modeling-tools/.../solver.py:1976` | `solve_case` signature |
| `../cfd-modeling-tools/.../config_loader.py` | `load_cases`, `load_scenario_groups` |

---

## Raw API Audit

**`ModelResult` fields (current):** `mdot_kg_s`, `velocity_main_m_s`, `reynolds_main`,
`friction_factor_main`, `deltaP_buoyancy_Pa`, `deltaP_losses_Pa`, `pressure_residual_Pa`,
`qhx_total_W`, `qambient_total_W`, `predicted_air_outlet_temperature_K`,
`start_temperature_K`, `end_temperature_K`, `temperature_periodicity_error_K`,
`sensor_predictions_K`, `sensor_prediction_provenance`, `segment_states`, `segment_df`,
`geometry_segments`, `geometry_sensors`, `geometry_refinement_label`, `sensor_registry_path`,
`effective_insulation_thickness_in`, `effective_air_flow_Lpm`, `effective_air_inlet_temperature_K`,
`root_status`, `root_rejection_reason`, `accepted_for_validation`, `validity_status`,
`validity_rejection_reason`, `max_bulk_temperature_K`, `min_rho_kg_m3`, ...

**`SegmentState` temperature fields:** `T_in_K`, `T_out_K`, `T_avg_K`, `s_start_m`, `s_end_m`

**`loop_mean_T_K` does NOT exist** in `ModelResult` — never added, not a renamed field.

---

## Interpretation: What is `loop_mean_T_K`?

The script comment says `CFD_LOOP_T = {2: 450.3, 3: 464.3, 4: 478.7}` is "approx mean
bulk T from momentum budget." The script uses `loop_mean_T_K` to find the insulation
thickness where the 1D model's loop temperature matches the CFD reference.

Best 1D proxy: **length-weighted mean of `SegmentState.T_avg_K`**:
```
loop_T = Σ(T_avg_K × ΔL) / Σ(ΔL)
```
This matches the CFD volume-weighted bulk T convention and accounts for varying segment
lengths. Fallback: `(start_temperature_K + end_temperature_K) / 2`.

Note: `start_T ≈ end_T ≈ 515.7 K` at ins=1.0in (periodicity condition met), while
the length-weighted mean is 512.1 K — the colder segments (downcomer, upper cooled
sections) pull the weighted average below the start/end values. This is physically
correct.

---

## Fix Applied

**Helper function added** to both script copies (after imports, before `ROOT =`):

```python
def _loop_mean_T_K(r) -> float:
    """Length-weighted mean bulk temperature over all loop segments."""
    segs = r.segment_states
    total_L = sum(s.s_end_m - s.s_start_m for s in segs)
    if total_L <= 0.0:
        return (r.start_temperature_K + r.end_temperature_K) / 2.0
    return sum(s.T_avg_K * (s.s_end_m - s.s_start_m) for s in segs) / total_L
```

**Two call sites replaced** (both in `run_insulation_sweep` and `step2_matched_closure`):
```
r.loop_mean_T_K  →  _loop_mean_T_K(r)
```

**Files changed:**
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py`
- `work_products/2026-07-04_jin_perleg_gap_analysis/run_jin_perleg_gap_analysis.py`

---

## Complete API Mismatch Table

| Script usage | Current API | Fix |
|---|---|---|
| `use_radiation=bool(rad)` | `ScenarioConfig.radiation_on` | Fixed AGENT-182 |
| `r.loop_mean_T_K` | No such field on ModelResult | Fixed AGENT-183 |
| `S.MinorLosses(k_90deg=0.0, k_20deg=0.0)` | `MinorLosses.k_90deg, k_20deg` | ✓ No change |
| `S.MinorLosses(major_loss_multiplier=..., ...)` | `MinorLosses.major_loss_multiplier` | ✓ No change |
| `replace(scn_base, ..., friction_multiplier_by_parent_segment=...)` | `ScenarioConfig.friction_multiplier_by_parent_segment` | ✓ No change |
| `S.solve_case(case, scn, ml)` | `solve_case(case, scenario, minor_losses)` | ✓ No change |
| `r.mdot_kg_s` | `ModelResult.mdot_kg_s` | ✓ No change |

---

## Commands Run

```bash
# Crash log inspection
cat work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_gap_local.log

# API audit
grep -n "loop_mean_T\|mdot_kg_s\|class ModelResult\|class SegmentState" \
  ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py

# MinorLosses and solve_case audit
grep -n "major_loss_multiplier\|k_90deg\|def solve_case" .../solver.py

# Smoke test (single solve + _loop_mean_T_K)
# Salt 2, ins=1.0in, rad=True, ml=MinorLosses(k_90deg=0, k_20deg=0)
# Result: solve 100.2s, mdot=0.021256, loop_T=512.11 K — PASS

# Restart background run
nohup python3 work_products/.../run_jin_perleg_gap_analysis.py > run_jin_gap_local.log 2>&1 &
# PID: 94224, started 2026-07-07 11:53 CDT
```

---

## Observations vs Interpretation

**Raw:** `_loop_mean_T_K` = 512.11 K at Salt 2, ins=1.0in; CFD_LOOP_T[2] = 450.3 K.  
**Interpretation:** The default scenario (ins=1.0in, rad=on) runs the loop too hot.
The insulation sweep will find the matched condition at lower insulation (thinner
insulation → more heat loss → lower loop T). The sweep ranges from 0 to 2.0 inches.

**Raw:** `start_temperature_K = end_temperature_K = 515.71 K`.  
**Interpretation:** Periodicity condition satisfied (∆T ≈ 0), confirming a consistent
thermally-coupled steady-state solution. `_loop_mean_T_K` (512 K) differs from start/end
(516 K) because the weighted average includes colder downstream segments.

**Raw:** 46 segments in `segment_states`.  
**Interpretation:** The loop model resolves 46 axial segments, providing enough spatial
resolution for the length-weighted T average to be physically meaningful.

---

## Blockers

None. Script is running.

## Next Steps

1. Check log ~15 min after start: `tail work_products/.../run_jin_gap_local.log`
2. Step 1 prints per-salt matched-T results after 102 solver calls (~2.8h).
3. After all 4 steps complete (~3.4h from 11:53 CDT → ~15:15 CDT), inspect outputs:
   - `jin_insulation_sweep.csv` — matched insulation thickness per salt
   - `matched_closure_compare_jin.csv` — default vs global-mean vs per-leg friction at matched T
   - `perleg_segment_dp_jin.csv` — ΔP budget per span at matched T
   - `f_re_fit_perleg.csv` — linear f/f_lam(1/Re) fit per leg
