# F5 Richardson-Number-Corrected Friction Closure — Candidate Screen

Date: 2026-07-07
Task: AGENT-200
Role: Implementer
Owner: claude

## Purpose

Implement F5_ri_corrected: a Richardson-number correction on top of the
F3_shah_apparent baseline:

    dp_F5 = dp_F3_shah_apparent × phi(Ri_streamwise, leg_class)
    phi   = max(1.0, 1.0 + c × Ri_streamwise)

where c is fitted from de-buoyed CFD momentum budget data (Salt 2/3/4 Jin)
using 1-parameter OLS with a forced intercept of 1.

## Fit Method

Input: `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`

For each non-upcomer leg class (heater, cooler, downcomer):
- 3 operating points (Salt 2/3/4 Jin)
- Compute phi_target = f_corrected_over_flam / f_F3_shah_over_flam
  where f_F3_shah_over_flam = fRe_darcy_shah(Re, x+) / 64
  using Shah (1978) Eq. 15 constants
- Fit phi = 1 + c * Ri_streamwise via 1-parameter OLS (forced intercept = 1):
  c = sum(Ri_i * (phi_i - 1)) / sum(Ri_i^2)
- Upcomer excluded: recirculation cell invalidates single-stream entry assumption

## Key Finding: Screen Failed for All Leg Classes

| leg_class | c_fitted | R²       | RMSE_phi | phi_mean | c_active | fit_quality          |
|-----------|----------|----------|----------|----------|----------|----------------------|
| heater    | 1.473    | −74.57   | 0.161    | 1.814    | 0.0      | poor_set_to_mean     |
| cooler    | 0.608    | −27.50   | 0.102    | 1.535    | 0.0      | poor_set_to_mean     |
| downcomer | 0.721    | −4.30    | 0.496    | 1.812    | 0.0      | poor_set_to_mean     |
| upcomer   | N/A      | N/A      | N/A      | N/A      | 0.0      | excluded             |

R² < 0 for all three classes: the 1-parameter Ri model (forced intercept=1)
is worse than a constant-phi model for all leg classes. This means that within
the Salt 2-4 operating band (Re ≈ 60–135, Ri_streamwise ≈ 0.38–1.38), phi is
NEARLY INDEPENDENT of Ri_streamwise.

This confirms AGENT-191's (Codex) earlier finding of negative R² in some groups.

Consequence: all c values are set to 0.0 (fit_quality="poor_set_to_mean").
F5 reduces to F3_shah_apparent with phi=1 for all inputs.

## Physical Interpretation

The phi values do vary across leg classes (heater phi ≈ 1.81, cooler phi ≈ 1.54,
downcomer phi ≈ 1.81) but they are nearly independent of Ri_streamwise WITHIN
each class. This suggests that:
1. The dominant friction excess above F3_shah is explained by Re-dependence
   (captured by F4_leg_class), not Ri-dependence.
2. Three operating points with similar Ri range per class are insufficient
   to detect a Ri trend above the scatter level.
3. A proper Ri correction requires more diverse operating conditions
   (corrected Q-perturbation runs with different heater powers → wider Ri spread).

## mdot Comparison Results

| source_id                          | form             | mdot_pred   | mdot_cfd    | err_pct  |
|------------------------------------|------------------|-------------|-------------|----------|
| ...salt_test_2_jin...              | F3_shah_apparent | 0.01306131  | 0.01318355  | -0.93%   |
| ...salt_test_2_jin...              | F5_ri_corrected  | 0.01306131  | 0.01318355  | -0.93%   |
| ...salt_test_3_jin...              | F3_shah_apparent | 0.01547614  | 0.01497722  | +3.33%   |
| ...salt_test_3_jin...              | F5_ri_corrected  | 0.01547614  | 0.01497722  | +3.33%   |
| ...salt_test_4_jin...              | F3_shah_apparent | 0.01762115  | 0.01698468  | +3.75%   |
| ...salt_test_4_jin...              | F5_ri_corrected  | 0.01762115  | 0.01698468  | +3.75%   |

F5 ≡ F3_shah_apparent numerically (delta = 0.0 kg/s for all salts, confirmed
by run_f5_mdot_comparison.py). F5 does NOT improve on F3_shah.

## Limitations

1. 3-point OLS → 0 DOF → R² and RMSE are not meaningful goodness-of-fit metrics.
   Out-of-sample uncertainty is O(1).
2. Ri_streamwise is CFD-derived (from calibration table); the 1D solver does not
   self-consistently compute Ri. Using CFD Ri values in a 1D solver prediction
   introduces a fundamental circularity.
3. The forced intercept phi=1 at Ri=0 is physically motivated (F3_shah is the
   baseline) but it severely constrains the fit.
4. Upcomer excluded because left_upper_leg has f/f_lam < 1 (friction suppressed
   by recirculation), violating the single-stream assumption.
5. No independent validation data exists (all 3 points used for fitting).

## Re-fit Instructions

When corrected Q-perturbation data is requalified (after AGENT-181 gate):
1. Recompute phi_target for each new operating point
2. Re-run 1-parameter OLS per leg class
3. If R² ≥ 0 for a class and c > 0, update _F5_RI_COEFFICIENTS["c"] to the
   fitted value and change fit_quality to "ok"
4. Re-run mdot comparison and document whether F5 improves on F3_shah

## Files

- `f5_fit_summary.csv` — OLS fit results per leg class
- `mdot_comparison_f5.csv` — F3_shah vs F5 mdot for Salt 2/3/4
- `run_f5_mdot_comparison.py` — reproduces mdot comparison
- `README.md` — this file
- `summary.json` — machine-readable metadata

## Reproduce

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python work_products/2026-07-07_f5_ri_corrected/run_f5_mdot_comparison.py
# Tests:
cd ../cfd-modeling-tools && pytest tamu_first_order_model/Fluid/tests/test_friction_closures.py -v
```
