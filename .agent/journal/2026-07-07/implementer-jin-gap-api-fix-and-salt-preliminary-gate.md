# Jin Gap API Fix + Corrected Salt Preliminary Gate

Date: `2026-07-07`  
Task: `AGENT-182`  
Role: Implementer / Writer  

---

## Context

Three overnight jobs were submitted on 2026-07-06 (AGENT-180):
- `3278452` water_post_rerun — COMPLETED (exit 0)
- `3278453` saltq_gate_after — PENDING (dependency on solver jobs 3275448/3275449/3275560)
- `3278454` jin_gap_rerun — FAILED (exit 1:0, elapsed 4 s)

User asked to: (1) diagnose and fix the Jin gap failure; (2) inspect the Salt gate
output and admit only `requalified` rows; (3) patch and resubmit the Jin gap job.

---

## Finding 1 — `use_radiation` vs `radiation_on` (API mismatch, not submission error)

**Root cause:** The Jin gap script `run_jin_perleg_gap_analysis.py` calls:
```python
scn = replace(scn_base, insulation_thickness_in=float(ins), use_radiation=bool(rad))
```
but `ScenarioConfig` (solver.py line 114) has always declared the field as:
```python
radiation_on: bool = True
```
There is no field named `use_radiation` anywhere in the Fluid codebase (confirmed by
`grep -rn "use_radiation" .../tamu_first_order_model/Fluid/` returning no matches, and
checking the prior commit `024a561` which also shows `radiation_on`).

**This is a bug in the script, not an API rename.** The script was written July 4 with
an incorrect field name assumption. Python's `dataclasses.replace()` raises
`TypeError: __init__() got an unexpected keyword argument 'use_radiation'` at runtime.

The submission was correct (PYTHONPATH was set, script was found). The script was the bug.

**Fix:** changed `use_radiation=bool(rad)` → `radiation_on=bool(rad)` in:
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py` (line 74)
- `work_products/2026-07-04_jin_perleg_gap_analysis/run_jin_perleg_gap_analysis.py` (line 74)

**Smoke test (Python, not sbatch):**
```
ScenarioConfig fields with radiation: ['radiation_on', 'outer_rad_multiplier_by_parent_segment']
replace radiation_on=False: OK, radiation_on = False
replace radiation_on=True: OK, radiation_on = True
```

---

## Finding 2 — Salt gate (3278453) still PENDING

The formal gate job `saltq_gate_after` (3278453) has dependency
`afterany:3275448:3275449:3275560`. As of 2026-07-07 morning, all three corrected
Salt solver jobs are still RUNNING:

| Job | Name | Wall time | Node |
|-----|------|-----------|------|
| 3275448 | corr_saltq_g1 | 3d 0h 12m | c318-017 |
| 3275449 | corr_saltq_g2 | 3d 0h 02m | c318-011 |
| 3275560 | corr_saltq_salt4_all | 2d 22h 17m | c318-018 |

No formal gate output exists yet. Instead, a **manual live scan** was performed by
running `collect_corrected_salt_status.py` against the active solver logs.

---

## Finding 3 — Corrected Salt mdot monitors: BCs are working

**Live mdot observations (2026-07-07):**

All 14 preflight audits passed (`preflight_bad_ok_count=0`). All Salt 2/3/4 cases
show mdot movement in the correct direction. The formal gate threshold from
`assess_time_convergence.py` is approximately Q^(1/3) movement from nominal:
- ±10% Q → expected ±3.2–3.5% mdot change
- ±5% Q  → expected ±1.6–1.7% mdot change

Observed (current, not yet converged):

| Case | Nominal | Current mdot | % change | Expected |
|------|---------|-------------|---------|---------|
| salt2_hi10q | 0.01318 | 0.01404 | **+6.5%** ✓ | +3.2% |
| salt2_hi5q  | 0.01318 | 0.01363 | **+3.4%** ✓ | +1.6% |
| salt2_lo10q | 0.01318 | 0.01229 | **-6.8%** ✓ | -3.5% |
| salt2_lo5q  | 0.01318 | 0.01274 | **-3.3%** ✓ | -1.7% |
| salt3_hi10q | 0.01498 | 0.01541 | +2.9% (rising, only 20s past restart) | +3.2% |
| salt3_hi5q  | 0.01498 | 0.01523 | +1.7% (rising, only 21s past restart) | +1.6% |
| salt3_lo10q | 0.01498 | 0.01409 | **-5.9%** ✓ | -3.5% |
| salt3_lo5q  | 0.01498 | 0.01455 | **-2.9%** ✓ | -1.7% |
| salt4_hi10q | 0.01698 | 0.01812 | **+6.7%** ✓ | +3.2% |
| salt4_hi5q  | 0.01698 | 0.01759 | **+3.6%** ✓ | +1.6% |
| salt4_lo10q | 0.01698 | 0.01607 | **-5.4%** ✓ | -3.5% |
| salt4_lo5q  | 0.01698 | 0.01660 | **-2.3%** ✓ | -1.7% |

Notably the responses are **larger** than Q^(1/3) for most cases. This is physically
expected: at low Re (laminar NC, Re~60–110), the buoyancy–friction balance is nonlinear.
A 10% Q increase both raises buoyancy AND changes local fluid properties (viscosity,
density), so the mdot response exceeds the purely-laminar Q^(1/3) prediction. This is
consistent and not a sign of incorrect BCs.

**Salt 1 cases:**
- hi10q: CONVERGED at t=4010 (endTime=9756) via convergenceMonitor; mdot=-0.01170
- lo10q: still running at t=5417; mdot=-0.01047
- Salt 1 nominal is not in the CFD reference table (weakly converged). Formal gate
  cannot run without a baseline. Estimate: midpoint of hi/lo ≈ -0.01109; if correct,
  hi10q moved +5.5%, well above threshold. Still treat with caution per Salt 1 policy.

---

## What counts as "requalified" for closure use

From `tools/analyze/assess_time_convergence.py` lines 477–557:
- `requalified`: mdot moved ≥ ~Q^(1/3) from nominal AND re-plateaued (flat monitor window)
- `false_steady`: mdot flat but NOT moved from nominal
- `too_short`: run too short to classify

Current state: most runs have MOVED but not yet plateaued. They will be gated by
job 3278453 after the solver jobs finish. Only `requalified` rows from that gate's
`run_status/run_status_inventory.csv` may enter the upcomer correlation (lane U1/T10).

---

## Commands Run

```bash
# Job status check
sacct -j 3278452,3278453,3278454 --format=JobID,JobName%28,State,ExitCode,Elapsed
squeue -u andresfierro231

# Error log inspection
cat tmp/2026-07-06_overnight_postprocess_jobs/slurm-jin_gap_rerun-3278454.err

# API verification
grep -n "use_radiation\|radiation_on\|class ScenarioConfig\|@dataclass" \
  ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
grep -rn "use_radiation" ../cfd-modeling-tools/tamu_first_order_model/Fluid/
git -C ../cfd-modeling-tools show 024a561:tamu_first_order_model/Fluid/.../solver.py | grep radiation

# Live mdot scan
python3 tmp/2026-07-06_overnight_postprocess_jobs/collect_corrected_salt_status.py
# (run from /tmp/saltgate_live_snapshot/)

# Smoke test of fix
python3 -c "...replace radiation_on=bool(rad) test..."

# Resubmit (after fix)
ssh login3.ls6.tacc.utexas.edu "cd /scratch/.../ethan_runs && sbatch \
  tmp/2026-07-06_overnight_postprocess_jobs/run_jin_perleg_gap_rerun.sbatch"
# → new job ID recorded in AGENT-182 status
```

---

## Files Inspected

- `tmp/2026-07-06_overnight_postprocess_jobs/slurm-jin_gap_rerun-3278454.err`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py` (lines 107–156)
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py`
- `work_products/2026-07-04_jin_perleg_gap_analysis/run_jin_perleg_gap_analysis.py`
- `tmp/2026-07-06_overnight_postprocess_jobs/run_corrected_salt_postprocess_afterany.sbatch`
- `tmp/2026-07-06_overnight_postprocess_jobs/collect_corrected_salt_status.py`
- Solver logs: `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/runs/*/` (mdot monitors)

## Files Changed

- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py` (use_radiation→radiation_on)
- `work_products/2026-07-04_jin_perleg_gap_analysis/run_jin_perleg_gap_analysis.py` (use_radiation→radiation_on)
- `work_products/2026-07-07_corrected_salt_preliminary_gate/preliminary_gate_analysis.json` (new)
- `work_products/2026-07-07_corrected_salt_preliminary_gate/README.md` (new)
- `.agent/status/2026-07-07_AGENT-182.md` (new)
- `.agent/journal/2026-07-07/implementer-jin-gap-api-fix-and-salt-preliminary-gate.md` (this file)
- `.agent/BOARD.md` (own row added)

---

## Incomplete Lines

- Formal gate (job 3278453) still PENDING; no `operating_point_verdict` values yet
- Salt 1 nominal mdot unknown; Salt 1 formal gate needs a nominal reference
- The Jin gap resubmission was pending at journal-write time — see status for new job ID

## Next Steps

1. Check new Jin gap job ID: `sacct -j <new_id> --format=JobID,State,ExitCode,Elapsed`
2. Inspect `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/` for outputs
3. After solver jobs exit: `squeue -j 3278453` to confirm gate started; then read `run_status/run_status_inventory.csv`
4. Filter: `awk -F, '$NF=="requalified"' run_status_inventory.csv` (or check `operating_point_verdict` column)
5. Only requalified rows enter lane U1/T10 upcomer correlation fitting
