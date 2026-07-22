# Upcomer Recirculation Correlation v2

**Date:** 2026-07-07  
**Task:** AGENT-196  
**Owner:** claude (Implementer/Writer)  
**Tool:** `tools/analyze/build_upcomer_correlation.py`  
**Status:** Complete (3-point calibration; awaiting T2 corrected Q jobs for Re expansion)

---

## Purpose

Build the best-possible 3-point upcomer recirculation correlation from existing
Salt 2/3/4 Jin nominal CFD data, with honest uncertainty bounds and a documented
physical mechanism.

---

## Physical Mechanism

The upcomer is the vertical upward-flow test section (`pipeleg_left` =
`left_lower_leg + test_section_span + left_upper_leg`) made of quartz.

**Why the recirculation cell forms:**

1. The heater outlet (`lower_leg`, inclined ~21 deg from horizontal) delivers
   buoyant, high-temperature molten salt to the bottom of the vertical test
   section. The fluid enters the upcomer with a significant thermal excess over
   the locally stationary fluid above.

2. The quartz test section is nearly adiabatic (high wall thermal resistance;
   no external cooling). The fluid near the wall does not cool significantly,
   so the vertical temperature stratification is maintained.

3. A density inversion forms: hot buoyant fluid at the bottom, cooler (denser)
   fluid above. This is the classical Rayleigh-Benard instability geometry —
   a gravitationally unstable configuration. The instability drives a
   recirculation cell (upward near the tube center where the hot fluid rises,
   downward near the wall where cooler fluid descends, or vice versa depending
   on the radial temperature profile).

4. The cell weakens as Reynolds number increases: stronger forced convection
   (inertia) suppresses the buoyant overturning. This is the classic
   mixed-convection competition: `Ri = Gr/Re^2` is the buoyancy-to-inertia
   ratio. When `Ri >> 1`, buoyancy dominates; as Re grows, Ri falls and
   forced convection wins.

5. The cell persists in the **lower** upcomer (`left_lower_leg`) where the
   buoyancy input is strongest, and a **nearly constant** backflow fraction
   (~30%) persists in the **upper** upcomer (`test_section_span`,
   `left_upper_leg`) even at the highest CFD Re — suggesting a persistent,
   near-cooler-pinned cell structure that may require a 2-region model.

**Literature basis:**  
LitRev ch.14 (mixed-convection onset), Jackson-Cotton-Axcell criterion
(turbulent, cited for physics only — flow is laminar here).  
Onset screen: `Ri = Gr/Re^2 ~ O(1)` for mixed-convection transition.

---

## Onset Re Extrapolation

Two independent routes bracket the onset Re where the recirculation cell
is expected to turn off:

| Route | Basis | Re_crit estimate | Trust |
|---|---|---|---|
| A (data trend) | Lower-upcomer backflow extrapolated to zero | ~240-260 | Low: extrapolated from 3 points |
| B (Ri criterion) | `Ri = Gr/Re^2 ~ O(1)` using section-median Ri and D_h | ~100-235 | Low: hand estimate, laminar screen |

Both routes agree to ~factor 2 ("a few hundred Re, ~1.5-2.5x above current max
CFD Re ~135"). Current Salt 3 (Re~97) sits at the lower bound of Route B —
consistent with its observed 22% backflow (the cell is weakening but not off).

**Key caveat:** The fitted linear model `bf = a + b/Re` predicts an asymptote
`bf -> a ~ 0.054` as Re -> infinity, NOT a zero-crossing. The onset Re is
therefore an extrapolation from Route A/B, not a zero-crossing of this
particular functional form.

---

## Dataset (3-point)

Representative station: **TW7** (first cross-section in `left_lower_leg`).  
Re_upcomer from momentum budget (`left_lower_leg` bulk Re).  
Ri, Ra, Pr from section-MEDIAN of solver-written fields (NOT mean — median is
~100x smaller and physically the correct characteristic group).

| Case | Re_upcomer | backflow_frac | Ri_median | Ra_median | Nu_upcomer |
|---|---|---|---|---|---|
| salt_2_jin | 71.1 | 0.278 | 2.634 | 213212 | 3.107 |
| salt_3_jin | 96.8 | 0.219 | 2.396 | 365131 | 4.060 |
| salt_4_jin | 134.9 | 0.172 | 1.498 | 450901 | 4.986 |

Confirmed properties:
- backflow_fraction decreases monotonically with Re (physics check PASS)
- Nu_upcomer increases monotonically with Re (physics check PASS)
- backflow_fraction range 17-28% matches AGENT-162 finding of "15-33%"

---

## Correlation Fit

**Model:** `bf = a + b / Re`  
(Linear in 1/Re; chosen per task specification and consistency with F4 form)

**Parameters:**

| Param | Value | OLS SE (1 DOF) | Jackknife std | Interpretation |
|---|---|---|---|---|
| a | 0.05389 | ±0.00065 | ±0.00090 | Asymptotic backflow at high Re |
| b | 15.931 | ±0.060 | ±0.086 | Buoyancy-driven backflow strength |

**Fit quality:** sigma_hat = 0.000281 (1 DOF). The fit is nearly exact
because 3 points constrain 2 parameters completely (1 DOF = minimal residual).

**WARNING on uncertainty:** With only 3 calibration points and 2 free
parameters, the reported standard errors appear very small because sigma_hat
is tiny (3 collinear points fit the model almost exactly). This does NOT
imply high confidence in the parameters for out-of-sample prediction.
The true parameter uncertainty at the onset Re (~240-260, extrapolation ~2x
beyond calibration range) is O(1) in the correlation prediction interval.

---

## Data Needs Statement

Corrected Q perturbation jobs (SLURM 3275448-3275451, Salt 2/3/4 hi/lo heater
power) are required to expand the Re range beyond the nominal S2/S3/S4
operating points (Re ~68-135). Until those runs qualify under the T2 gate,
the correlation is extrapolated beyond its calibration range for all onset-Re
predictions.

Specifically:
- **Re range needed to constrain onset:** Re ~ 150-300 (crossing the Route
  A/B onset bracket requires at least one run showing backflow_fraction < 5%)
- **Status:** Corrected jobs running (as of 2026-07-04); preliminary gate
  pending (AGENT-185 shows 14/14 direction check PASS, but formal Re-range
  qualification not yet complete)
- **Until T2 gate qualifies corrected Q runs:** do NOT add perturbation
  Re-points to this correlation (AGENT-166 confirmed all June 19/25 runs
  are false-steady with mdot pinned at nominal)

---

## Outputs

| File | Description |
|---|---|
| `upcomer_dataset.csv` | 3-row dataset: Re, Ri, Ra, Pr, bf, Nu per case |
| `upcomer_correlation_fit.csv` | Fit parameters, uncertainty, onset Re |
| `summary.json` | Machine-readable package metadata |

---

## Reproduce

```bash
python tools/analyze/build_upcomer_correlation.py
# or to a custom output dir:
python tools/analyze/build_upcomer_correlation.py --out-dir path/to/out/
```

Tests:
```bash
python -m pytest tools/analyze/test_build_upcomer_correlation.py -v
```

---

## Limitations

1. **3 data points only** — parameter uncertainty is O(1) for out-of-sample
   prediction, even though in-sample fit is nearly exact (1 DOF).
2. **Single representative station (TW7/left_lower_leg)** — the upper
   upcomer (TP5/TW8/TP6) shows a nearly constant ~30% backflow not captured
   by this fit; a 2-region model may be needed.
3. **Coarse mesh, laminar, single time per case** — no mesh-independence
   (GCI) bounds, no oscillation-aware uncertainty (AGENT-192 quasi-steady UQ
   tool not yet applied to upcomer metrics).
4. **Solver-written Ri/Ra fields** — Lc and reference Delta_T definition not
   audited against the case setup (flagged NEEDS-AUDIT in prior notes).
5. **Onset Re extrapolation is low-trust** — Routes A and B bracket a factor
   of 2 from each other; both are well outside the calibration range.
