# F5 Richardson-Number-Corrected Friction Closure — Implementation Session

Date: 2026-07-07
Role: Implementer
Task: AGENT-200
Owner: claude

---

## Files Inspected (Read-Only)

- `AGENTS.md` — coordination rules, file-ownership policy
- `.agent/BOARD.md` — confirmed AGENT-200 row claimed; Active table layout
- `.agent/FILE_OWNERSHIP.md` — ownership scope
- `.agent/ROLES.md` — role definitions
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/f4_ri_calibration_table.csv`
  — 18-row calibration table (Salt 2/3/4 × 6 spans): columns Re, Ri_streamwise, x_plus,
  f_corrected_over_flam, leg_class, span. Used as sole input for F5 OLS fit.
- `work_products/2026-07-07_f4_ri_calibration_and_solver_gate/ri_definition_audit.md`
  — Ri_streamwise definition: section median × cos(θ) for inclined legs; median because mean
  is ~100× inflated by near-zero velocity cells in recirculation.
- `work_products/2026-07-07_friction_forms_comparison/mdot_comparison.csv`
  — Reference mdot errors for F1/F3h/F3_shah/F4 (F3_shah: Salt 2 −0.93%, Salt 3 +3.33%, Salt 4 +3.75%).
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  — Pre-edit state: F1, F2, F3_hagenbach, F3_shah_apparent, F4_leg_class already present.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
  — Pre-edit state: ScenarioConfig frozen dataclass, `_friction_closure_kwargs_for_segment`,
  `distributed_and_minor_losses`.
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`
  — Pre-edit state: 52 tests, TestF4LegClass present.

---

## Files Changed

1. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
   — Added `_F5_RI_COEFFICIENTS`, `_f5_phi`, `dp_F5_ri_corrected`; updated AVAILABLE_FORMS
   and FORM_DESCRIPTIONS.

2. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
   — Added `ri_table: Dict[str, float]` field to ScenarioConfig; updated
   `_friction_closure_kwargs_for_segment` to accept `scenario` parameter and handle F5 branch;
   updated 2 call sites in `distributed_and_minor_losses`.

3. `../cfd-modeling-tools/tamu_first_order_model/Fluid/tests/test_friction_closures.py`
   — Added 9 F5 tests (TestF5RiCorrected class); updated 3 existing loop-over-AVAILABLE_FORMS
   tests to handle F5 kwargs with `warnings.catch_warnings()`.

4. `work_products/2026-07-07_f5_ri_corrected/f5_fit_summary.csv` — Created.
5. `work_products/2026-07-07_f5_ri_corrected/mdot_comparison_f5.csv` — Created.
6. `work_products/2026-07-07_f5_ri_corrected/run_f5_mdot_comparison.py` — Created.
7. `work_products/2026-07-07_f5_ri_corrected/README.md` — Created.
8. `work_products/2026-07-07_f5_ri_corrected/summary.json` — Created.
9. `.agent/status/2026-07-07_AGENT-200.md` — Created (this session).
10. `.agent/journal/2026-07-07/implementer-f5-ri-corrected.md` — This file.

---

## Commands Run (Exact)

### OLS Fit (computed in-session, not a standalone script)

For each non-upcomer leg class, from calibration CSV rows:

```
phi_target = f_corrected_over_flam / (fRe_darcy_shah(Re, x_plus) / 64)
c_ols = sum(Ri_i * (phi_i - 1)) / sum(Ri_i^2)   [forced intercept = 1]
R2 = 1 - sum((phi_i - (1 + c*Ri_i))^2) / sum((phi_i - mean(phi))^2)
```

### Test runs

```bash
cd /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools
python -m pytest tamu_first_order_model/Fluid/tests/test_friction_closures.py -v
# → 61 passed

cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q
# → 299 passed
```

### mdot comparison run

```bash
cd /scratch/09748/andresfierro231/projects_scratch/ethan_runs
python work_products/2026-07-07_f5_ri_corrected/run_f5_mdot_comparison.py
```

---

## Results and Observations

### OLS Fit Results

| leg_class | n | c_fitted | R²     | RMSE_phi | phi_mean | c_active | fit_quality     |
|-----------|---|----------|--------|----------|----------|----------|-----------------|
| heater    | 3 | 1.473    | -74.57 | 0.161    | 1.814    | 0.0      | poor_set_to_mean|
| cooler    | 3 | 0.608    | -27.50 | 0.102    | 1.535    | 0.0      | poor_set_to_mean|
| downcomer | 3 | 0.721    | -4.30  | 0.496    | 1.812    | 0.0      | poor_set_to_mean|
| upcomer   | — | —        | —      | —        | —        | 0.0      | excluded        |

R² < 0 for all three leg classes. The 1-parameter model (phi = 1 + c × Ri)
is worse than a constant-phi predictor for all classes. Root cause: within the
Salt 2-4 operating band (Re ≈ 60-135, Ri_streamwise ≈ 0.38-1.38), phi is
nearly independent of Ri_streamwise within each class. Per task instructions,
c is set to 0.0 for all classes (fit_quality="poor_set_to_mean").

This confirms the AGENT-191 (Codex) negative-R² finding in the earlier analysis.

### mdot Comparison

F5 ≡ F3_shah_apparent (delta = 0.0 kg/s) for all three salts, because c=0 for
all leg classes gives phi=1 everywhere. The mdot errors are unchanged:
- Salt 2: -0.93% (1D ≡ F3_shah)
- Salt 3: +3.33%
- Salt 4: +3.75%

F3_shah_apparent remains the recommended production closure.

### UserWarning Verified

Running `dp_F5_ri_corrected(Re=80, ...)` without `warnings.catch_warnings()` fires:
```
UserWarning: F5_ri_corrected is a candidate screen ...
```
This is expected behavior per the task brief.

---

## Errors Encountered and Fixes

1. **Edit conflict on solver.py**: First `_friction_closure_kwargs_for_segment` edit
   failed with "File has been modified since read." Resolved by re-reading lines 138-162
   to get the exact current content, then re-applying the edit.

2. **Loop-over-AVAILABLE_FORMS tests**: Existing tests that iterated `AVAILABLE_FORMS`
   and keyed on `"F4_leg_class": {"leg_class": "heater"}` would crash on F5 (which also
   needs `leg_class` plus `Ri_streamwise` and fires a `UserWarning`). Fixed by adding
   an elif branch for `"F5_ri_corrected"` with `{"Ri_streamwise": 0.0, "leg_class": "heater"}`
   and wrapping the F5 call with `warnings.catch_warnings()` + `simplefilter("ignore")`.

---

## Physical Interpretation

The dominant friction excess above F3_shah (phi ≈ 1.5-1.8) is explained by Re-
dependence (captured by F4_leg_class coefficients), not Ri-dependence. Three
operating points with a narrow Ri range per class (Ri_streamwise ≈ 0.38-1.38)
are insufficient to detect a Ri trend above the scatter level.

Implication: a proper Ri correction requires diverse heater power settings
(corrected Q-perturbation runs → wider Ri spread). The F5 framework is now in
place; updating _F5_RI_COEFFICIENTS["c"] after requalification is a one-line change.

---

## Incomplete Lines of Investigation

- No independent validation data (all 3 points used for fitting; 0 DOF per class).
- Ri_streamwise values are CFD-derived from calibration table; the 1D solver does not
  self-consistently compute Ri. This circularity is documented in README.md limitations.
- Upcomer friction correction remains unexplored (recirculation excluded from F5;
  handled separately by upcomer_correlation_v2 from AGENT-196).
- Whether heater phi ≈ 1.81 >> 1 implies a non-Boussinesq buoyancy mechanism (Ri²
  correction? fully-developed-limit correction?) is not resolved.

---

## Next Steps

1. **AGENT-181 gate**: when corrected Salt Q-perturbation runs requalify, re-run
   the F5 OLS fit with expanded Ri range (3+ operating points per class with
   distinct heater power → distinct Ri). Update `_F5_RI_COEFFICIENTS["c"]` to
   fitted value if R² ≥ 0 and c > 0.
2. **TODO-MODEL-FORM-BAKEOFF**: include F5 (as F3_shah placeholder) in the bakeoff
   comparison, with a note that re-fitting is pending gate requalification.
3. **F6 buoyancy-modified friction (Ri² correction?)**: if F5 still doesn't fit after
   expanded data, consider a physically-motivated Ri-correction form (Scheele-Hanratty,
   Jackson mixed convection, or fully-developed-limit correction for heated pipe).
