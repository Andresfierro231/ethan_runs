# Claude Inspection — CFD Post-Processing → 1D Closure Pipeline

Date: `2026-06-30`
Role: `Reviewer`
Author: Claude (Opus 4.8)
Requested by: anf2282@eid.utexas.edu

## Purpose

Honest scientific review of the existing ("Codex first pass") post-processing
that extracts centerline / pressure / wall quantities from the OpenFOAM TAMU
molten-salt natural-circulation loop CFD and turns them into **apparent friction
factor** and **heat-transfer-coefficient (HTC / Nu)** closure terms for the 1D
reduced-order loop model in `../cfd-modeling-tools/tamu_first_order_model/Fluid/`.

This entry separates **observed output** (what the code/data actually do),
**interpretation** (what it means scientifically), **contradictions**, and
**next suggested actions**, per the repo writing rules. All claims cite files.
The review was assembled from direct reading plus four scoped sub-audits
(hydraulic, thermal, data-provenance, 1D-contract).

---

## TL;DR for Ethan

The pipeline gets several hard things **right** and is unusually honest about
its own limits, but the headline deliverables ("apparent friction factor",
"Nu(Re,Pr)") are **over-claimed relative to the data that supports them**. The
two most important truths to internalize:

1. **There is no real correlation here.** Every "fit" is calibrated from ~3
   physically-distinct **laminar** salt cases (Salt 2/3/4; Salt 1 absent) over a
   narrow Re ≈ 76–174 window, and much of even that Re spread is an *artifact of
   swapping the viscosity model* (Jin vs Kirst), not independent operating
   points. Treat all closures as **single-regime, operating-point calibrations**,
   not transferable correlations — and never let the 1D solver query them for
   water or at Re outside ~76–174.
2. **"Steady/averaged" is asserted, not demonstrated.** The cases have **no
   in-solver `fieldAverage`**; "time-averaged" QoI = an arithmetic mean of the
   last ~5 *instantaneous* snapshots, with **no convergence test**. Some
   downstream freeze-window files even reference times that are **not on disk**.

Everything below expands these with evidence and concrete fixes.

---

## Observed: what the data and solver actually are

(Verified directly against the staged cases and `registry/case_registry.csv`.)

- **13 native OpenFOAM cases on disk**: 8 salt
  (`viscosity_screening_salt_test_{1..4}_{jin,kirst}_coarse_mesh`), 4 water
  (`val_water_test_{1..4}_coarse_mesh_laminar`), 1 standalone
  `val_salt_test_2_coarse_mesh_laminar`. Source: collaborator scratch
  `/scratch/09807/ethanrozak/foam_vv/runs/viscosity_screening_20260511_221340/`.
- **Solver**: OpenFOAM Foundation **v13 `foamRun`** (modular `fluid` /
  buoyant solver), **transient** (`deltaT 0.01`, `endTime 10000`,
  `writeControl adjustableRunTime`). Not a steady SIMPLE solver — cases march
  toward a pseudo-steady natural-circulation state and are frozen mid-run.
- **All 13 cases are `simulationType laminar`** (`constant/momentumTransport`).
  Stray `k/epsilon/omega/nut` in `0/` are unused initializations. y+ is recorded
  but on a laminar run it is only a mesh-resolution diagnostic, not a wall
  treatment.
- **Fields written**: `U, T, p, p_rgh, phi, rho, nuEff` plus coded
  non-dimensional volume fields (`Gr, Pr, Ra, Re, Ri, Nu`) and
  `wallHeatFlux, wallShearStress, yPlus`. `p`/`p_rgh` are **absolute Pa**
  (compressible/buoyant solver), with `p_rgh = p − ρgh`; density via EoS
  ρ = 2293.6 − 0.7497·T.
- **Function objects already in the cases**: 4× `surfaceFieldValue` mdot
  monitors, `wallHeatFlux`, `wallShearStress`, `yPlus`, `total_Q`, PIV slab,
  temperature/wall-temperature probes, velocity profiles. **There is no
  `fieldAverage` and no `*Mean`/`*Prime2Mean` field anywhere.**
- **Decomposition**: 64 subdomains in the **collated `processors64/`** format;
  no top-level reconstructed time dirs. Mesh is full 3D (10 `nonConformalCyclic`
  couplings; no `empty`/`wedge`) — the "2D"/PIV-slab labels are post-processing
  slice constructs, not the simulation dimensionality.
- **Convergence reality**: mdot is well-converged on at least
  `salt_test_1_jin` (≈ −0.01126 kg/s, flat to ~5 sig figs at t≈3230 s), but
  on-disk latest times are uneven and far below `endTime`
  (salt2_jin=2431, salt4_jin=2082, **salt2_kirst=586**); paper inventory marks
  several `qoi_run_status: terminated` and `retained_window_status:
  convergence_audit_required`.

### Core post-processing math (verified)

- Apparent Darcy friction, two independent routes, both dimensionally correct
  in true Pa:
  - shear route `f = 8·|τ_w| / (ρ u²)`
    (`tools/extract/sample_leg_centerline_major_loss.py:1702-1704`)
  - pressure route `f = 2·D_h·∇p_rgh / (ρ u²)` (`:1417-1425`); Fanning =
    `0.25·f` (`:1708`).
- HTC `h = |q_w| / |T_bulk − T_wall|` with `T_bulk` = **mass-flux-weighted
  mixed-mean** (`:1655,1678`; weighting at `:659-665`); quality-gated by
  `THERMAL_MIN_ABS_DELTA_T_K`, area-ratio, and aligned-flux thresholds
  (`:1664-1688`).
- `Nu = h·D_h / k(T_eval)` with **temperature-dependent salt properties**
  evaluated at local branch bulk T (`ethan_salt_hardening_common.py:183`,
  `build_ethan_salt_model_dependency_package.py:780,803`).
- Closure fits delivered to the 1D model
  (`Fluid/validation_data/ethan_cfd_informed_salt_v2/`):
  friction `log f_D = 5.2316 − 0.9478·log Re + 2.9211·I[test_section]`
  (`straight_friction_fit.json`, valid Re 80–174);
  direct `log Nu = −3.0043 + 0.9608·log Re` (`direct_nu_fit.json`, valid
  Re 76–165, **`left_lower_vertical` branch only**); UA'/HTC as per-case scalar
  surfaces.

---

## What is done correctly (credit where due)

These are the items that most often *sink* a buoyancy-loop reduction, and they
are handled well:

1. **Pressure units & hydrostatic separation.** Using `p_rgh` (= p − ρgh) as
   the primary field for all Δp/friction work is the right choice for a
   buoyancy-driven loop; the EoS slope/intercept in the analysis profile match
   the case EoS exactly. No kinematic-pressure (p/ρ) confusion — the solver is
   compressible so p is already in Pa.
2. **Two independent friction estimates** (wall-shear vs pressure-gradient) give
   a built-in cross-check.
3. **Mixed-mean (mass-flux-weighted) bulk temperature** as the HTC reference —
   the physically correct reference, not area-average or centerline.
4. **Wall flux from the solver's own `wallHeatFlux` FO** (`kappaEff·snGrad T`),
   not a fragile hand-rolled gradient.
5. **Temperature-dependent salt properties** (ρ, μ, cp, k) for Re/Pr/Nu — the
   single most important correctness item for molten salt, done right.
6. **Laminar `Fourier` transport** is consistent with Re≈O(100); no spurious
   turbulent conductivity is injected.
7. **Ambient/parasitic heat loss is separated** from internal transfer
   (`build_ethan_salt_family_heat_loss_breakout.py`), so the salt-side HTC
   surfaces are not contaminated by insulation loss.
8. **Honest scoping & quality gates**: small-ΔT gating, validity windows
   recorded, K_eff explicitly blocked, direct-Nu confined to one branch,
   residual buckets flagged `calibration_only`. The bundle does not pretend to
   cover what it cannot.

---

## Shortcomings — prioritized, with evidence

### Tier 1 — affects scientific validity of the deliverable

**S1. The closures are calibrated from ~3 laminar cases over a manufactured Re
range; they are not correlations.**
Friction = 3 coefficients from 12 rows that collapse to **3 physical cases**
(Salt 2/3/4 × Jin/Kirst viscosity swaps; Salt 1 absent). Nu = 2 coefficients
from 7 rows, all one branch. Re ≈ 76–174 is < a decade and **fully laminar**, so
the fit barely improves on the analytic laminar `f ∝ Re⁻¹` (note the fitted
slope b ≈ −0.95). Worse, the Re spread is dominated by **viscosity-model
disagreement (Jin vs Kirst)**, so the regression bakes property-model
uncertainty into the friction/Nu slope.
→ Frame every fit as a *single-regime calibration*, report it per physical case,
and stop calling it Nu(Re,Pr)/f(Re) correlation.
Evidence: `straight_friction_fit.json`, `direct_nu_fit.json`,
`.../2026-06-19_ethan_salt_model_dependency_package_v3/{hydraulic,thermal}_fit_ready_rows.csv`.

**S2. "Time-averaged / steady" is not demonstrated — no `fieldAverage`, no
convergence test.**
`select_stable_processor_times` (`tools/hydraulic_budget_defs.py:168-197`) only
takes the *last N contiguous* written steps (default N=5, 5 s gap tolerance);
"stable" is a misnomer. QoI are unweighted arithmetic means over those steps
(`safe_nanmean`) with **no residual / plateau / stationarity gate**. For a
natural-circulation loop that can drift or oscillate, 5 instantaneous snapshots
are not a Reynolds/ensemble average. Only an indirect symptom (`*_rel_cv`
spread) is surfaced.
→ Either add `fieldAverage` and re-run, or compute and gate on a real
stationarity metric over a much longer window with reported uncertainty.

**S3. Pressure is sampled on the WALL, not as a cross-sectional mean.**
All pressures are wall-patch boundary-face values, area-averaged over wall faces
per bin (`sample_leg_centerline_major_loss.py:1174-1175, 1581`; corner endpoints
`sample_feature_minor_loss_budget.py:218-220`). The 1D model wants the
**section-mean static pressure**; wall static ≠ section-mean wherever streamlines
curve (bends, reducers, test-section). The irony: the code already builds true
`cutPlane` cross-sections — but only for T and U, never for pressure.
→ Add pressure cut-plane (section-mean) extraction; reserve wall pressure as
supporting context. NB: this is the literal "centerline / average pressure" the
request asked for and is the gap most worth closing first.

**S4. Δp omits the kinetic-energy term → reversible area-change effects are
mislabeled as loss, polluting the major/minor split.**
Span "terminal dp" and corner `delta_p_rgh` are pure static `p_rgh` differences
(`build_ethan_case_analysis_package.py:1072-1073`,
`sample_feature_minor_loss_budget.py:469`). True mechanical loss is
Δ(p_rgh + ½ρu²). At every reducer/expansion (`test_section_complex`,
`pipeleg_upper_*_reducer`) a large reversible ½ρu² exchange is being counted as
"loss," so minor (form) losses at fittings are **not cleanly separated** from
reversible acceleration — directly undermining the stated major/minor goal.
→ Add the dynamic-pressure term from section-mean velocity; report total-pressure
loss.

**S5. Mesh adequacy is unestablished and self-contradicted.**
Every training case is `coarse_mesh`, yet both 1D READMEs state coarse mesh is
diagnostic/regression-only and **medium/fine is required for any thermal-closure
/ wall-temperature interpretation** (`Fluid/README.md:160-165`,
`tamu_loop_model_v2/README.md:154-158`). So the UA'/HTC/Nu surfaces are built on
the mesh the project itself deems inadequate for thermal closure. No
mesh-independence study is attached to any f or Nu value.

### Tier 2 — biases magnitudes; fixable without new runs in some cases

**S6. Geometry feeding f is an idealized circle, not the measured section.**
`D_h = P/π`, `A = P²/(4π)`, perimeter `= wall_area/ds`
(`hydraulic_budget_defs.py:149-158`); bulk velocity `= ṁ/(ρ·A_geom)`
(`sample_leg_centerline_major_loss.py:1700-1701`). The code *already* computes a
real cut-plane `cross_section_area_m2` and even a ratio-to-geom diagnostic
(`:1650-1651`) but does not use it for f. Any non-circularity feeds f
**quadratically** through u².
→ Use the measured cut-plane area/`4A/P` for D_h, A, and u in both f and Nu.

**S7. Borrowed/aggregate mass flow for some spans.**
`left_lower_leg` / `left_upper_leg` have `mdot_face_zone: None` and fall back to
the main-loop mean (`:1308-1311`), so the velocity in their f is not measured in
that span. Combined with S6, ½ρu² is doubly approximate there.

**S8. `f` (shear route) uses |τ_w|, discarding sign/recirculation.**
`tau_mean_abs` is used in `f = 8τ/(ρu²)` (`:1568,1702-1704`); the signed mean is
computed but unused. In separated regions (bend insides, behind reducers) τ_w
reverses, so averaging |τ_w| **over-estimates** net drag and f. The signed
integral is the physically correct one for force balance.

**S9. Mixed-mean bulk T omits cp and drops reverse-flow faces.**
Weight is `ρu` not `ρu·cp` (`:665`) — thermodynamically the bulk (mixed-mean) T
is enthalpy-flux-weighted, and salt cp is strongly T-dependent. Reverse-flow
faces are dropped (`positive_aligned_mass_flux`, `:659,665`), biasing T_bulk in
recirculating sections. Both are undocumented deviations from the textbook
definition.

**S10. Radiative wall flux excluded for `rad_on` cases.**
The `wallHeatFlux` FO header has no `qr` column, so extracted q is
conductive/convective only. Defensible if salt-side HTC is meant to be purely
convective, but currently undocumented for the radiation-on cases the bundle
distinguishes.

### Tier 3 — robustness / reproducibility / wiring hazards

**S11. NaN-token scrubbing in reconstructed T can mask divergence.**
`sanitize_ascii_scalar_nan_tokens` replaces NaN tokens in T by *positional*
(not spatial) neighbor averages (`:190-225`); T drives the EoS density →
velocity → f and the bulk T → HTC. This hides bad cells/reconstruction failures
rather than excluding affected times.

**S12. Reconstruction is fragile and the window can silently shrink.**
On any `reconstructPar` failure the loop `continue`s and drops the time
(`:159-166`); friction comes from reconstructed wall fields while ṁ comes from
the decomposed-run face-zone history, merged by time key with no guarantee the
keys coincide (missing keys → silent NaN f).

**S13. Flow direction is a hard-coded, unvalidated profile assumption.**
Every span hard-codes `flow_direction_sign_hint: 1.0`
(`case_analysis_profiles.py:449...`; profile text admits
"manual_profile_assumption_not_auto_validated"). For a buoyancy loop the
circulation direction is a *result*; a reversed case would silently invert
aligned-flux selection. `flow_alignment_sign` is inferred separately and can
disagree with no reconciliation check.

**S14. Provenance gap — freeze windows reference times not on disk.**
`freeze_case_windows.csv` claims retained times up to 5397 s (salt2) / 8123 s
(salt4), but on-disk `processors64` only reaches 2431 / 2082. "Continuation"
and `hiq` lanes imply later runs whose data is **not in this workspace** → those
analyses cannot be verified or re-sampled here.

**S15. No OpenFOAM runtime here → not currently reproducible.**
No OF env in this container (`reconstructPar`/`foamRun` absent); the OF13 tree
plus a custom BC (`libRCWallBC.so`) are unrecovered
(`imports/2026-06-02_openfoam13_runtime_source.json`). Downstream products
depend entirely on pre-extracted `.dat` outputs; volumes can't be regenerated.

**S16. Segment-name mapping CFD↔1D is implicit and collision-prone.**
Friction `admitted_parent_segments=["heated_incline","test_section"]` but CFD
rows/closure map call them `lower_leg|test_section_span`; Nu uses
`left_lower_vertical` vs CFD `left_lower_leg`. Worse, **"lower_leg" denotes the
heated branch in the thermal policy but the unheated main-loop straight in the
friction rows** — a real mis-wiring trap.

**S17. No validity-window guard against extrapolation.**
Validity Re windows are text only; the 1D solver computes ṁ (hence Re)
self-consistently and nothing clamps queries to Re≈76–174. Insulation sweeps
(0–3 in) and **water** cases will drive Re out of domain where the laminar law +
fixed offset has no support.

**S18. Linearized resistance R=Δp/ṁ used for off-design prediction.**
`build_ethan_salt_pressure_drop_predictivity.py:155-158,330-331` predicts ṁ from
a fixed `R [Pa·s/kg]`, but the loss is quadratic (`f ρu²/2`); a fixed R is valid
only at the operating point it was measured. Undocumented.

**S19. UA'/HTC surfaces in v2 are stale v1 copies.**
The v2 "producer" `shutil.copy2`s the v1 surface CSVs unchanged
(`build_ethan_cfd_informed_salt_v2_bundle.py`); only the friction/Nu JSONs and
provenance were refreshed. "v2" overstates what changed.

**S20. Water family has no CFD-informed closures at all** — the 1D registry
includes Water 1–4 but the bundle is salt-only; water closures are inherited
legacy and unaudited.

---

## Contradictions surfaced

- **"Coarse mesh is regression-only"** (project's own rule) vs **thermal
  closures built on coarse mesh** (S5).
- **"Time-averaged" QoI** vs **no `fieldAverage`, 5 instantaneous snapshots, no
  convergence gate** (S2).
- **Freeze-window times (≤8123 s)** vs **on-disk times (≤2431 s)** (S14).
- **`flow_direction_sign_hint=1.0` hard-coded** vs **`flow_alignment_sign`
  inferred from pressure** — no reconciliation (S13).
- **"v2 refresh"** vs **stale v1 UA'/HTC copied verbatim** (S19).
- **Pressure cut-planes available** (used for T/U) vs **wall pressure used for
  Δp/f** (S3).

---

## Next suggested actions (ranked by scientific payoff)

1. **Close the literal request first — section-mean pressure.** Add pressure
   cut-plane extraction (reuse the existing T/U cut-plane machinery) to produce
   true centerline/section-mean p_rgh, and add the ½ρ⟨u⟩² term so Δp becomes a
   total-pressure loss. Fixes S3+S4 and is the highest-value, lowest-cost change;
   no re-run needed.
2. **Establish convergence honestly.** Add `fieldAverage` to `system/functions`
   and re-run to a defined averaging window, OR (no re-run) compute a
   stationarity metric (running-mean drift / oscillation amplitude) over the
   *full* retained window and gate + report uncertainty bands on every f/HTC/Nu.
   Fixes S2.
3. **Stop selling calibrations as correlations.** Report f and Nu **per physical
   case** with the operating Re labeled; separate the Jin/Kirst viscosity-model
   axis from the physical-case axis explicitly; hard-clamp the 1D solver to the
   fit Re window and emit a flag when it extrapolates (and especially for water).
   Fixes S1+S17.
4. **Use measured geometry in f and Nu.** Switch D_h/A/u to the cut-plane
   `4A/P` and measured area the code already computes. Fixes S6 (and partly S7).
5. **Mesh-independence study on ≥1 case** at medium/fine to bound the coarse-mesh
   error on f and Nu before any of these enter a publishable 1D result. Fixes S5.
6. **Reproducibility**: recover the OF13 runtime + `libRCWallBC.so`; reconcile
   freeze-window CSVs with on-disk times (or relocate the missing continuation
   data into the workspace and register it). Fixes S14+S15.
7. **Lock the CFD↔1D segment map** in one documented table; rename or namespace
   "lower_leg" to remove the heated/unheated collision. Fixes S16.
8. **Smaller corrections**: use signed τ_w for the shear-route f (S8);
   enthalpy-flux (ρu·cp) weighting and document the reverse-flow truncation for
   bulk T (S9); document the `qr` exclusion (S10); replace NaN-scrubbing with
   time-exclusion + a logged count (S11); refresh or explicitly version the
   stale v1 UA'/HTC surfaces (S19).

---

## Assumptions / caveats of THIS review

- No OpenFOAM runtime was available, so I could not re-run extraction or
  reconstruct volumes; findings are from source reading + the on-disk
  function-object outputs and staged case configs.
- I sampled solver/convergence facts primarily on `salt_test_1_jin` and the
  `val_salt_test_2` case; a couple of provenance claims (freeze-window times,
  continuation lanes) come from CSVs that themselves may be stale.
- Line numbers are against the files as of 2026-06-30 and may drift.

## Key files referenced

- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/hydraulic_budget_defs.py`
- `tools/extract/sample_feature_minor_loss_budget.py`
- `tools/analyze/build_ethan_case_analysis_package.py`
- `tools/analyze/build_ethan_salt_model_dependency_package.py`
- `tools/analyze/ethan_salt_hardening_common.py`
- `tools/analyze/summarize_corner_pressure_drops.py`
- `tools/analyze/build_ethan_salt_pressure_drop_predictivity.py`
- `tools/case_analysis_profiles.py`
- `registry/case_registry.csv`,
  `imports/2026-06-02_openfoam13_runtime_source.json`
- `staging/modern_runs/2026-06-01_full_extractable_batch/{salt,water}/*/`
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/ethan_cfd_informed_salt_v2/`
  (`straight_friction_fit.json`, `direct_nu_fit.json`, `htc_surface.csv`,
  `ua_prime_surface.csv`, `one_d_closure_map.csv`, `closure_snapshot.json`)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tools/build_ethan_cfd_informed_salt_v2_bundle.py`
