# Upcomer Recirculation Correlation Build

Date: `2026-07-07`  
Agent role: Implementer / Writer  
Task ID: AGENT-196

---

## Files inspected (read-only)

| File | Purpose |
|---|---|
| `AGENTS.md` | Repo rules and non-negotiable constraints |
| `.agent/BOARD.md` | Confirmed AGENT-196 row claimed; reviewed other active tasks |
| `.agent/FILE_OWNERSHIP.md` | Scope verification |
| `.agent/ROLES.md` | Role definitions |
| `operational_notes/06-26/30/2026-06-30_upcomer_convection_cell_model.md` | Physics basis, seed data table, onset extrapolation (Route A/B), MEDIAN Ri correction |
| `work_products/2026-06-30_claude_upcomer_convection_cell/upcomer_convection_cell_viscosity_screening_salt_test_{2,3,4}_jin_coarse_mesh.csv` | Backflow fraction, Ri, Ra, Pr, Re per station per case |
| `work_products/2026-07-01_claude_momentum_budget/momentum_budget.csv` | Bulk Re per span per case (authoritative for Re_upcomer) |
| `work_products/2026-06-30_claude_thermal_htc/segment_htc_uaprime_viscosity_screening_salt_test_{2,3,4}_jin_coarse_mesh.csv` | Nu, HTC per segment per case |
| `tools/extract/sample_upcomer_convection_cell.py` | Script that produced the upcomer cell CSVs (confirmed output already exists — did not rerun OF13 tool) |
| `work_products/2026-07-01_claude_allspan_convection/` | Checked: allspan data has more stations but no TW7 labels; used 2026-06-30 data instead |

## Files changed

| File | Action |
|---|---|
| `tools/analyze/build_upcomer_correlation.py` | Created — main correlation builder |
| `tools/analyze/test_build_upcomer_correlation.py` | Created — 25 pytest tests |
| `work_products/2026-07-07_upcomer_correlation_v2/upcomer_dataset.csv` | Generated output |
| `work_products/2026-07-07_upcomer_correlation_v2/upcomer_correlation_fit.csv` | Generated output |
| `work_products/2026-07-07_upcomer_correlation_v2/README.md` | Created — mechanism, limitations, reproduce |
| `work_products/2026-07-07_upcomer_correlation_v2/summary.json` | Generated output |
| `.agent/status/2026-07-07_AGENT-196.md` | Created — status file |
| `.agent/journal/2026-07-07/implementer-upcomer-correlation.md` | This file |

## Commands run (exact, reproducible)

```bash
# Generate outputs
python tools/analyze/build_upcomer_correlation.py

# Run targeted tests
python -m pytest tools/analyze/test_build_upcomer_correlation.py -v

# Run full suite
python -m pytest tools/analyze/test_*.py tools/extract/test_*.py -q
```

## Results and observations

### Dataset assembled

Representative station: TW7 (left_lower_leg, first cross-section).  
Re_upcomer from momentum budget (authoritative bulk Re, not section-median Re).  
Ri_median, Ra_median, Pr_median from section-MEDIAN (NOT mean — median ~100x smaller,
per AGENT-156/162 finding and model note §6b correction).

| Case | Re_upcomer | backflow_fraction | Ri_median | Ra_median | Nu_upcomer |
|---|---|---|---|---|---|
| salt_2_jin | 71.125 | 0.2778 | 2.634 | 213212 | 3.107 |
| salt_3_jin | 96.770 | 0.2188 | 2.396 | 365131 | 4.060 |
| salt_4_jin | 134.883 | 0.1719 | 1.498 | 450901 | 4.986 |

- backflow_fraction 17-28% matches AGENT-162 report of "15-33% falling with Re"
- Nu monotone increasing: 3.1 → 4.1 → 5.0 (physics check PASS)
- Ri_median values (2.6, 2.4, 1.5) are all >> 1 → buoyancy-dominated flow
  throughout calibration range (no transition observed yet)

### Fit

Model `bf = a + b/Re` (OLS, 1 DOF):
- a = 0.05389 ± 0.00065 (OLS SE, 1 DOF), ± 0.00090 (jackknife std)
- b = 15.931 ± 0.060 (OLS SE), ± 0.086 (jackknife std)
- sigma_hat = 0.000281 (1 DOF)
- The fit is nearly exact (3 points, 2 params) — uncertainty appears small but
  is genuinely not informative about out-of-sample prediction

The asymptote bf → a ~ 0.054 at Re → ∞ means the fit does NOT predict a
zero-crossing (onset). Onset Re estimates come from Route A/B extrapolation only.

### Onset Re

- Route A (lower-upcomer trend extrapolated to bf=0): ~240-260
- Route B (Ri ~ O(1) criterion, LitRev ch.14): ~100-235
- Current Salt 3 (Re=97) is at the lower edge of Route B — consistent with
  22% observed backflow (cell weakening but not off)
- The upper upcomer (TP5/TW8/TP6) maintains ~30% backflow at ALL Re — suggests
  a cooler-pinned persistent cell not captured by the single lower-station fit

### Test results

```
25/25 PASS (test_build_upcomer_correlation.py)
252/252 PASS (full test suite, no regressions)
```

## Incomplete lines of investigation

- **2-region upcomer model**: the lower upcomer (TW7/TP4) shows clear Re-sensitivity
  but the upper upcomer (TP5/TW8/TP6) does not. A single bf(Re) correlation cannot
  represent both. Left as open for when more data (T2 corrected Q runs) arrive.
- **Characteristic Ri audit**: the solver-written Ra/Ri fields use a specific Lc and
  DeltaT definition that has not been verified against the case setup (NEEDS-AUDIT
  flag from 2026-06-30 model note §7). Used Ri_section_median as-is.
- **Recirculation_intensity metric**: also present in the CSV (0.05-0.07 range) but
  not included in the correlation. It represents reverse volumetric flux / forward flux.
  Would need to be reconciled with backflow_area_fraction for a vector-based correlation.
- **Gr-based forms**: the model note proposes `bf ~ f(Ri)` or `f(Ra/Re^p)`.
  With 3 points and Ri variation small (1.5-2.6), a Ri-based power law cannot be
  distinguished from a Re-only model. Deferred to post-T2-qualification data.

## Next steps

1. Monitor corrected Q jobs (SLURM 3275448-3275451) via AGENT-185 gate tool
2. Once T2 qualification passes, re-run this script with expanded dataset
   (add hi/lo Re perturbation points) to reduce parameter uncertainty and
   constrain onset Re
3. Consider 2-region model if upper-upcomer backflow remains Re-insensitive
4. Perform Ri/Ra characteristic definition audit (need to check solver case setup)
