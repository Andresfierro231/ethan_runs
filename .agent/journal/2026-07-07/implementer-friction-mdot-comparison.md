# Implementer — Friction Closure mdot Comparison

Date: 2026-07-07
Role: Implementer
Task: AGENT-195

---

## Files Inspected

- `AGENTS.md` — non-negotiable rules, file-ownership policy
- `.agent/BOARD.md` — confirmed AGENT-195 row, scope, and read-only constraints
- `.agent/FILE_OWNERSHIP.md` — edit-path restrictions
- `.agent/ROLES.md` — role definitions
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — lines 190-220 docstring review; all available forms
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
  — ScenarioConfig fields, solve_case(), _F4_LEG_CLASS_BY_PARENT_SEGMENT (line 526),
    SolveWarmStart, ModelResult, SegmentState
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/jin_insulation_sweep.csv`
  — matched insulation (S2=0.25 in, S3/S4=0.30 in) and F1 reference errors
- `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/run_jin_perleg_gap_analysis.py`
  — load_cases/load_scenario_groups pattern, MinorLosses usage, CFD_MDOT values
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml`
  — Salt 2/3/4 case parameters

## Files Changed

- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — docstring only (lines 206-208): corrected misleading "CONSERVATIVE (over-estimates)"
    to "K_∞ = 1.33 underestimates total entry-length ΔP at x⁺ < 1"
- `work_products/2026-07-07_friction_forms_comparison/run_single_salt.py` (NEW)
- `work_products/2026-07-07_friction_forms_comparison/run_parallel_all_salts.py` (NEW)
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv` (NEW — 12 rows)
- `work_products/2026-07-07_friction_forms_comparison/summary.json` (NEW)
- `work_products/2026-07-07_friction_forms_comparison/README.md` (UPDATED — actual results)
- `.agent/status/2026-07-07_AGENT-195.md` (NEW)
- `.agent/journal/2026-07-07/implementer-friction-mdot-comparison.md` (this file)

## Commands Run

```bash
# Test after docstring fix:
cd /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model
python -m pytest tests/test_friction_closures.py -q
# → 45 passed

# Run full comparison (3 salts × 4 forms in parallel subprocesses):
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python3 work_products/2026-07-07_friction_forms_comparison/run_parallel_all_salts.py
# → 12 rows, 0 verify failures, wall time ~426 s
```

## Key Results

All F1 verification checks PASSED (within ±0.5% of Jin gap reference):

| Salt | F1 ref (%) | F1 actual (%) | delta |
|:----:|:----------:|:-------------:|:-----:|
| 2    |    +9.703  |      +9.703   | 0.000 |
| 3    |   +16.215  |     +16.215   | 0.000 |
| 4    |   +17.972  |     +17.972   | 0.000 |

Full mdot error comparison:

| Form             | Salt 2 err | Salt 3 err | Salt 4 err |
|:-----------------|:----------:|:----------:|:----------:|
| F1               |    +9.70%  |   +16.21%  |   +17.97%  |
| F3_hagenbach     |    +3.50%  |    +6.69%  |    +5.69%  |
| F3_shah_apparent |    -0.93%  |    +3.33%  |    +3.75%  |
| F4_leg_class     |   -23.19%  |   -23.57%  |   -24.66%  |

F4 per-leg dp (Salt 2, Pa): heater=20.2, cooler=17.2, downcomer=17.1, upcomer=9.4.
F1 per-leg dp (Salt 2, Pa): heater=11.1, cooler=11.0, downcomer=11.5, upcomer=11.0.
F4 heater+downcomer penalty is 2× the F1 value; upcomer is ~15% lighter.

## Obstacles and Resolutions

1. **Misleading docstring** in `dp_F3_hagenbach`: the old text said Hagenbach
   OVER-ESTIMATES the entry loss for x⁺ < 0.05. The correct statement is that K_∞ = 1.33
   UNDER-ESTIMATES total entry-length ΔP at x⁺ < 1 because it accounts for the
   momentum-defect contribution only; enhanced wall shear during profile development
   is captured by F3_shah_apparent but not by Hagenbach. Fixed per task spec.

2. **ValueError for unmapped stub segments**: AGENT-191 hardened solver.py to raise
   for any segment not in `_F4_LEG_CLASS_BY_PARENT_SEGMENT`. Four short (~25 mm)
   horizontal stubs exist in the TAMU geometry but were not in the dict. Since solver.py
   is READ-ONLY, applied runtime monkey-patch:
   ```python
   S._F4_LEG_CLASS_BY_PARENT_SEGMENT.update({
       "top_horizontal_inlet": "cooler",
       "top_horizontal_exit": "downcomer",
       "bottom_horizontal_inlet": "heater",
       "bottom_horizontal_exit": "upcomer",
   })
   ```
   Stubs are ~25 mm; combined effect on F4 dp is <1 Pa total.

3. **Solver performance ~100 s/call**: each solve takes ~100 s due to the
   thermal-periodicity outer loop. With 12 cases total, serial execution would take
   ~20 min. Solved by running 3 salt subprocesses in parallel (subprocess.Popen);
   all 3 salts complete in ~426 s total. Warm starts carry F1 solution to subsequent
   forms within each salt's sequential loop (helps for F3h/F3s; F4 solution is far
   from F3s so warm start has limited benefit there).

4. **SYS.PATH issue** in initial script: `ROOT = Path(__file__).resolve().parents[3]`
   was incorrect (gave projects_scratch instead of ethan_runs). Fixed to `parents[2]`
   (script lives 2 levels below ethan_runs root: work_products/dated-dir/script.py).

## Observations

- F3_shah_apparent is the best single-correlation predictor. It nearly eliminates the
  Salt 2 F1 error (-0.93%) but has a residual 3-4% over-prediction for Salt 3/4.
  The residual is consistent with either a temperature-dependence miss or insulation
  sensitivity not captured by the matched (rad=1) insulation.
- F4_leg_class uses CFD-fitted coefficients calibrated against the buoyancy-corrected
  de-buoyed friction momentum budget. In the 1D model these coefficients are applied
  in a steady-state laminar friction context without Ri correction, which causes
  consistent ~24% under-prediction of mdot across all three salts. The heater and
  downcomer coefficients are the dominant over-stiffening source.
- Per-leg dp for F1/F3h/F3s is nearly equal across all four legs (near-symmetric 64/Re),
  consistent with the loop geometry (all legs are approximately the same length).
  F4 breaks symmetry: heater (20 Pa) and downcomer (17-22 Pa) are heavily penalized
  relative to upcomer (9 Pa).

## Incomplete Lines of Investigation

- F4 + Ri correction (TODO-RI-CORRECTED-F4): if the Richardson-number buoyancy modifier
  is applied to reduce the heater/downcomer coefficient for the non-isothermally-heated
  1D model context, F4 may converge to CFD. Not implemented in this pass.
- Insulation sensitivity (±0.05 in) not explored here. The matched insulation from
  Jin sweep uses rad=1; mdot sensitivity to insulation at constant friction form
  is estimated at ~2% per 0.05 in from prior gap analysis.
- Only 3 Re points (Salt 2/3/4 Jin coarse mesh). F4 upcomer R²=0.02 (poor fit) noted
  in prior AGENT-191 work; conclusions about upcomer F4 behavior should be treated
  as preliminary.

## Next Steps

1. TODO-RI-CORRECTED-F4: implement Richardson-number buoyancy correction on F4 heater/cooler
   legs to test whether the ~24% F4 mdot deficit closes.
2. Extend comparison to corrected perturbation operating points once SLURM 3275448-3275451
   converge (T2 in MASTER TODO).
3. TODO-MODEL-FORM-BAKEOFF can consume `mdot_comparison.csv` as the friction comparison
   backbone once the observation table contract is established.
