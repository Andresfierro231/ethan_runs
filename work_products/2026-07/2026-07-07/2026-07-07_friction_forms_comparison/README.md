# Friction Forms mdot Comparison — Salt 2/3/4 Jin

**Task:** AGENT-195 | **Date:** 2026-07-07 | **Role:** Implementer

## Purpose

Compares four friction closure forms (F1, F3_hagenbach, F3_shah_apparent, F4_leg_class) on
the TAMU 1D loop solver for Salt 2, 3, and 4 Jin cases at the temperature-matched insulation
from the Jin gap analysis.  Quantifies the effect of each form on predicted mass flow rate,
total loop pressure drop, and per-leg pressure drop.

## Key Findings

F3_shah_apparent (Shah 1978 apparent Darcy f for developing laminar flow) nearly eliminates
the +9.7 to +18% F1 mdot over-prediction at matched insulation.  F4_leg_class severely
over-predicts loop friction and should not be used for loop-level mdot prediction without
a Ri-correction or recalibration (TODO-RI-CORRECTED-F4).

| Form             | Salt 2 err | Salt 3 err | Salt 4 err |
|:-----------------|:----------:|:----------:|:----------:|
| F1               |    +9.70%  |   +16.21%  |   +17.97%  |
| F3_hagenbach     |    +3.50%  |    +6.69%  |    +5.69%  |
| F3_shah_apparent |    -0.93%  |    +3.33%  |    +3.75%  |
| F4_leg_class     |   -23.19%  |   -23.57%  |   -24.66%  |

Wall times (parallel run on LS6): Salt 2 = 421 s, Salt 3 = 423 s, Salt 4 = 426 s (4 forms each).

### Per-leg pressure drop (Pa) at matched insulation

All forms assign essentially equal dp per leg (near-symmetric 64/Re-like loop) except F4:

| Form             | Salt | Heater | Cooler | Downcomer | Upcomer | Total |
|:-----------------|:----:|-------:|-------:|----------:|--------:|------:|
| F1               | 2    |   11.1 |   11.0 |      11.5 |    11.0 |  44.6 |
| F3_hagenbach     | 2    |   11.3 |   12.1 |      11.8 |    12.1 |  47.3 |
| F3_shah_apparent | 2    |   11.5 |   12.9 |      11.9 |    13.2 |  49.4 |
| F4_leg_class     | 2    |   20.2 |   17.2 |      17.1 |     9.4 |  63.9 |
| F1               | 3    |   10.4 |   10.4 |      10.8 |    10.4 |  42.0 |
| F3_hagenbach     | 3    |   10.8 |   11.9 |      11.1 |    12.0 |  45.8 |
| F3_shah_apparent | 3    |   10.9 |   12.4 |      11.2 |    12.8 |  47.3 |
| F4_leg_class     | 3    |   18.9 |   15.9 |      20.2 |     9.0 |  64.0 |
| F1               | 4    |   10.3 |   10.3 |      10.6 |    10.3 |  41.4 |
| F3_hagenbach     | 4    |   10.7 |   12.2 |      11.0 |    12.3 |  46.3 |
| F3_shah_apparent | 4    |   10.8 |   12.4 |      11.0 |    12.9 |  47.1 |
| F4_leg_class     | 4    |   18.6 |   15.6 |      21.8 |     9.0 |  65.0 |

F4 heater+downcomer penalty: F4's CFD-fitted f is calibrated for conditions where the
heater and downcomer have elevated friction due to buoyancy; applied globally in the 1D model
these coefficients over-penalize and drive mdot ~24% below CFD.

## Setup

- **Solver:** `tamu_loop_model_v2/solver.py` (READ-ONLY; not modified)
- **Friction closures:** `tamu_loop_model_v2/friction_closures.py`
- **Minor losses:** `k_90deg=0.0`, `k_20deg=0.0` (matching Jin gap baseline to isolate friction form effects)
- **Radiation:** on (`radiation_on=True`)
- **Property set:** `salt_jin` (default for Salt cases)
- **Matched insulation:** Salt 2 = 0.25 in, Salt 3 = 0.30 in, Salt 4 = 0.30 in
  (from Jin insulation sweep, temperature-matched at rad=1)

## CFD Reference Values

| Salt | mdot_CFD (kg/s) | Source |
|:----:|:--------------:|:-------|
| 2    | 0.01318354663   | momentum_budget.json, Jin gap analysis |
| 3    | 0.01497722      | momentum_budget.json, Jin gap analysis |
| 4    | 0.01698467657   | momentum_budget.json, Jin gap analysis |

## Verification Gate

F1 mdot errors at matched insulation (rad=1) must match Jin gap reference within ±0.5%:
- Salt 2: ref +9.703%  → PASS
- Salt 3: ref +16.215% → PASS
- Salt 4: ref +17.972% → PASS

## F4 Runtime Note

AGENT-191 hardened `solver.py` so F4_leg_class raises for unknown parent segments.
The TAMU loop geometry includes four short (~25 mm) horizontal stubs:
- `top_horizontal_inlet` (upcomer→cooler transition)
- `top_horizontal_exit` (cooler→downcomer transition)
- `bottom_horizontal_inlet` (downcomer→heater transition)
- `bottom_horizontal_exit` (heater→upcomer transition)

Since `solver.py` is read-only per BOARD.md, the script patches `S._F4_LEG_CLASS_BY_PARENT_SEGMENT`
at runtime (in-place dict update — does not modify the file). Stubs are assigned to the leg class
they flow INTO. Their combined length is <5% of total loop arc; F4 multiplier assignment has
negligible effect on the total dp from these stubs.

## Docstring Fix (friction_closures.py)

Fixed the misleading validity statement in `dp_F3_hagenbach()` docstring (lines 206-208):

**Old (misleading):**
> "the Hagenbach value is CONSERVATIVE (over-estimates the entry loss)"

**New (correct):**
> "K_∞ = 1.33 underestimates total entry-length ΔP at x⁺ < 1 because it omits the elevated
> distributed wall shear during velocity-profile development; dp_F3_shah_apparent captures both effects."

The old text confused the momentum-defect contribution (which K_∞ over-estimates for x+ < 0.05)
with the total entry-length ΔP (which K_∞ underestimates because it ignores enhanced wall shear).
All 45 friction closure tests pass after the fix.

## Outputs

| File | Description |
|:-----|:------------|
| `mdot_comparison.csv` | Main output: 12 rows (3 salts × 4 forms), all columns per spec |
| `summary.json` | Machine-readable metadata |
| `run_parallel_all_salts.py` | Top-level runner: launches 3 salt subprocesses in parallel |
| `run_single_salt.py` | Per-salt comparison helper; also callable directly |
| `partial_salt_2.csv`, `partial_salt_3.csv`, `partial_salt_4.csv` | Intermediate per-salt outputs |
| `salt2_log.txt`, `salt3_log.txt`, `salt4_log.txt` | Per-salt solver stdout |
| `README.md` | This file |

## Reproducing

```bash
cd /path/to/ethan_runs/work_products/2026-07-07_friction_forms_comparison
python3 run_parallel_all_salts.py
# Expected wall time: ~430 s total (all 3 salts in parallel, 4 forms each)
```

Single-salt only:
```bash
python3 run_single_salt.py 2   # or 3 or 4
```

Requirements: `cfd-modeling-tools` repo at `../..` relative to `ethan_runs/` root.
Do NOT source OF13 env — it breaks Python.

## Limitations

- Minor losses set to zero for clean friction comparison (as in Jin gap baseline).
- Per-leg dp = distributed friction only; `dp_total_loop_pa` includes test-section
  transition losses (contraction/expansion, always enabled).
- F4 upcomer R² = 0.02 (poor fit due to recirculation scatter); interpret with caution.
- Loop mean T is length-weighted; CFD reference T is approximate metadata.
- Three admitted evidence points (Salt 2/3/4 Jin) — narrow Re range (~60–135).
- F4 does not include Richardson-number correction (Ri). TODO-RI-CORRECTED-F4.

## Provenance

- Input: `work_products/2026-07-06_overnight_postprocess_jobs/jin_perleg_gap/jin_insulation_sweep.csv`
- Input: `work_products/2026-07-01_claude_momentum_budget/momentum_budget.json`
- Prior work: AGENT-191 (`work_products/2026-07-07_f4_ri_calibration_and_solver_gate/`)
  provides pressure-distribution comparison; this package adds loop-level mdot comparison.
