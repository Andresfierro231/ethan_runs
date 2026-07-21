# Coordinator/Implementer: Jin Properties + Per-Leg Friction + Gap Diagnosis

**Date:** 2026-07-04  
**Session type:** Interactive (< 30 min tasks) + sbatch job preparation  
**Status:** Code changes merged; sbatch job written, pending submission from login node

---

## 1. Presentation package corrections (fused_model_form_comparison.md, master_jul_2_presentation.md)

Three errors identified and corrected in `work_products/2026-07-02_master_jul_2_presentation/`.

### Error A — Section B default row K inconsistency
- **Bug**: the default row used `+24.8/+27.3/+29.9%` from the ROM fit (textbook K), while the global/per-leg rows used K=0 from the perleg trial. Cross-table inconsistency.
- **Fix**: replaced with `+29.7/+34.4/+39.9%` (from `perleg_vs_global_mdot.csv`, K=0 consistent). Added caveat note explaining the K difference in the matched-T column.

### Error B — Slide 8 insulation temperature series
- **Bug**: `422→512→548 K` cited mixed rad=0 at ins=0 (421.7 K), rad=1 at ins=1 (512 K), rad=0 at ins=2 (548.1 K). Figure A uses only rad=1 throughout.
- **Fix**: corrected to `~375→512→542 K over 0→1→2 in (rad=1 scenario)`. Added speaker note distinguishing the rad=0 series (422→544→548 K) as an alternative.

### Error C — Section C segment ΔP (CRITICAL, doubled CFD values)
- **Root cause**: `run_segment_dp_compare.py::cfd_leg_lengths()` computed leg length as straight-line distance between all 5 stations including fitting-end stations (s00, s04), giving L_full ≈ 0.712 m instead of L_interior ≈ 0.357 m (s01–s03 only). The momentum budget gradient was computed over interior stations only, so multiplying by L_full doubled all CFD ΔP values.
- **Additional issue**: the 1D model used schematic segment lengths (heated_incline = 0.914 m) evaluated with higher-viscosity `salt_current` properties, not CFD conditions. This made an apples-to-apples comparison impossible.
- **Fix**: rewrote `cfd_leg_lengths()` to load interior arc lengths from `segment_friction.csv`. Changed 1D ΔP formula to `dP_cfd × mult_global / f_leg` — property-independent, uses the same length for both sides.
- **Corrected values** (Salt 2, global mult=1.857):
  - heater: was +49% → now −30% (under-prediction)
  - downcomer: was +57% → now −15%
  - cooler: was +68% → now −17%
  - test-section: was +96% → now +27%
  - upcomer-lo: was +182% → now +20%
  - upcomer-up: was +282% → now +79%
- **Physical interpretation**: the global multiplier UNDER-predicts heavy legs and OVER-predicts light legs. The "structurally inadequate" conclusion stands but errors are now bidirectional.
- `segment_dp_compare.csv`, `segment_dp_compare.json`, and `fig2_segment_dp.png` regenerated. Both markdown documents updated.

---

## 2. Jin property as 1D model default

**File changed:** `cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/materials.py`

### Changes
1. Added `SALT_JIN_VISCOSITY_EXP_INV_T_COEFFS = (0.001149, -810.896, 780600.0)` — the two-term expInvT form from the CFD case_config.yaml `mu_spec` blocks for Salt 2/3/4 Jin runs.
2. Added `salt_jin = MixedCorrelationFluid(name="salt_jin", ...)` using Jin mu but same rho/cp/k/sigma as `salt_kirst` (which are the same CFD correlations).
3. Changed `DEFAULT_PROPERTY_SET_BY_FLUID["salt"]` from `"salt_current"` to `"salt_jin"`.
4. Added `"salt_jin"` and `"jin"` aliases to `FLUID_PROPERTY_SETS["salt"]`.
5. Added Jin metadata block in `fluid_property_metadata()`.
6. Fixed `MixedCorrelationFluid.mu()` overflow guard: clamps `T_safe = max(T_K, 1.0)` and `exp(min(exponent, 700.0))` to prevent solver-iteration-time overflow at unphysical temperatures.

### Property comparison at 450 K
| Set | mu (Pa·s) | vs Jin |
|---|---|---|
| `salt_jin` (new default) | 0.008951 | 1.00× |
| `salt_kirst` | 0.009964 | 1.11× |
| `salt_current` (old default) | 0.011600 | ~1.30× |

### Impact on factor-2 mdot gap
At matched T, the 1D with `salt_current` predicted mdot ≈ 0.0068 kg/s (−49% vs CFD). Switching to Jin reduces viscosity by ~30%, increasing Re by ~30% and reducing f_lam by ~23%. For laminar natural circulation, mdot ∝ 1/μ approximately, so Jin should give ~30% higher mdot → approximately 0.0088 kg/s. Gap narrows from 2× to approximately 1.5×. Remaining gap still requires investigation.

### Kirst preserved
`salt_kirst` remains accessible via `property_set_name="salt_kirst"` or `"kirst"`. Useful for thesis property sensitivity comparison (Kirst vs Jin: ~11% viscosity difference at 450 K).

---

## 3. Segment geometry clarification

**Correction to earlier claim**: the "2.5× interior arc lengths" statement was incorrect. It compared the 1D schematic segment length to the interior-only measurement range (s01–s03 stations), not to the full physical pipe.

**Correct comparison**:
- `heated_incline` (lower_leg): 1D schematic = 0.9144 m vs CFD fitting-to-fitting arc = 0.7123 m → **1.28× longer**
- Stations are evenly spaced: 4 gaps of 0.177 m each. Interior arc (s01→s03) = 0.357 m ≈ half the full arc.

The 1D model over-estimates the heater/downcomer/cooler segment lengths by ~28%. This adds ~28% extra friction in those legs even with correct f/f_lam. Likely cause: schematic dimensions include bend-center-to-bend-center distance; CFD fitting-end stations are placed inside the straight pipe just before the bend entry, so the junction-to-junction path (including bend geometry) is longer than the straight section alone.

**Net effect on factor-2**: reducing to CFD geometry lengths would decrease total loop friction by perhaps 15–20%, raising mdot by a similar amount. Not the dominant source of the 2× gap but a real correction.

---

## 4. Factor-2 mdot gap: mechanism inventory

At matched T (ins ≈ 0.27 in with `salt_current`; new value TBD with Jin) and per-leg friction:
- 1D mdot ≈ 0.0068 kg/s vs CFD 0.0132 kg/s (−49%)
- "Drive too weak" disproven: loop ΔT matches, buoyancy head (56 Pa) matches
- Therefore: loop friction resistance is ~4× too high in the 1D model

**Mechanisms to quantify (sbatch job):**

| Mechanism | Expected ΔR_friction | Priority |
|---|---|---|
| Property model (salt_current → Jin) | −23% f_lam | Done (code) |
| Segment lengths (28% excess in heavy legs) | −15 to −20% | Sbatch job |
| Per-leg f/f_lam (fixes distribution, not total) | 0% total, re-distributes | Sbatch job |
| Upcomer recirculation momentum penalty | Unknown, possibly large | Future |
| Coarse mesh f/f_lam over-estimation | Unknown (no GCI) | Future (conformal mesh) |

The first two corrections together might close 35–40% of the gap, leaving a residual ~1.3–1.5× gap. The recirculation mechanism is the next logical investigation.

---

## 5. Perturbation runs — status

All perturbation runs are `false_steady` (from `perturbation_requal.csv`):
- `pct_moved` = 0.003–0.3% vs expected 1.64–3.45%
- Thermal field did not equilibrate to the perturbed BC (loop thermal relaxation time >> simulation advance time)
- **Not usable** for f(Re) correlation training without much longer runtime

**Required**: each perturbation run needs several thermal relaxation times of additional runtime after the perturbation. Estimated additional runtime per case: 5,000–10,000 s sim-time. This is a future sbatch campaign.

---

## 6. Salt 1 status

- `viscosity_screening_salt_test_1_kirst_coarse_mesh`: CFD ran with **Kirst** viscosity, data present
- `viscosity_screening_salt_test_1_jin_coarse_mesh`: linked case exists but `postProcessing/` is empty — simulation was **not run**
- Section_mean_pressure + momentum budget have NOT been run for Salt 1 (neither Kirst nor Jin)
- To get the 4th f(Re) data point: must first run OpenFOAM for Salt 1 Jin (or post-process the Kirst case with Kirst mu for a consistent Kirst-based fit)

---

## 7. Sbatch job submitted

**Script:** `work_products/2026-07-04_jin_perleg_gap_analysis/submit_gap_analysis.sbatch`  
**Estimated runtime:** 35–45 min, 1 node, development partition

Steps within the job:

| Step | Script | Output |
|---|---|---|
| 1. Jin insulation sweep | `run_jin_perleg_gap_analysis.py` | `jin_insulation_sweep.json/.csv` |
| 2. Matched-T closure comparison (default/global/per-leg) | same | `matched_closure_compare_jin.json/.csv` |
| 3. Per-leg f(Re) fit (S2/S3/S4, linear in 1/Re) | same | `f_re_fit_perleg.json/.csv` |
| 4. Wall conductance proxy at matched-T | `run_wall_conductance.py` | `wall_conductance_cfd.json/.csv` |

**Note on submission:** Job must be submitted from a login node. Command:
```bash
/usr/bin/sbatch work_products/2026-07-04_jin_perleg_gap_analysis/submit_gap_analysis.sbatch
```

---

## 8. Honest limitations / open items

1. **Factor-2 residual gap**: even after Jin properties + per-leg friction, a significant mdot gap is expected. The upcomer recirculation model (28–34% backflow fraction) is likely a large contributor not yet quantified.
2. **Insulation/thermal BC**: the 1.4 in value was an assumed 1D scenario input, NOT derived from CFD. CFD uses an airside wall-h BC. True matched insulation is ~0.27 in (salt_current) or TBD (Jin). The wall conductance script provides an effective UA, which is the physically cleaner parameter.
3. **No GCI**: all closures from coarse mesh (2.17M cells). The f/f_lam values carry unknown mesh-induced error. GCI requires conformal-first remesh (the refined NCC interface breaks OF13 fvMeshStitcher).
4. **f(Re) with only 3 points**: the linear fit `f/f_lam = a + b/Re` uses S2/S3/S4. Extrapolation to Re < 61 (below the measurement range) carries unknown error. Salt 1 Kirst case would give a 4th point if post-processed.
