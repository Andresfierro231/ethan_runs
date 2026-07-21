# Thermal Closure Extraction Spec — HTC / UA' / Nu / R' per Segment

Date: `2026-06-30`
Lane: **L3** (thermal extraction prep) of `.agent/journal/2026-06-30/1d-model-status-and-plan.md`.
Author: claude (Opus 4.8)
Status: SPECIFICATION ONLY — implementable now, **executable only after blocker B1
clears** (OF13 runtime + `libRCWallBC.so`). Companion tool:
`tools/extract/sample_segment_htc_uaprime.py` (written + dry-run-runnable now).

Guiding principles (user-stated): disclose confidence boundaries on every artifact;
record the "why" for every decision; keep the work resumable after a break.

This note answers thermal critique items **S9** (enthalpy-flux bulk T), **S10**
(`qr` exclusion), **S2/S5** (convergence + mesh adequacy) and **S16** (segment
map) from `.agent/journal/2026-06-30/claude-inspection-cfd-1d-closure-postprocessing.md`,
and fulfils the closure contract in
`../cfd-modeling-tools/tamu_first_order_model/Fluid/validation_data/ethan_cfd_informed_salt_v2/one_d_closure_map.csv`
(UA' primary `W/m/K`; HTC secondary `W/m2/K`; Nu direct only on `left_lower_leg`;
`R'_thermal = 1/UA'`).

---

## 0. The blocker (read first)

**B1 — `T` cannot be reconstructed with the LS6 v12 toolchain.** The cases are
OpenFOAM Foundation **v13** collated runs whose `T` field carries a private custom
boundary condition (`rcExternalTemperature` / `libRCWallBC.so`) that is **not
installed on LS6**. Foundation `openfoam/12` reads v13 fields only for *standard*
BCs (`p p_rgh U phi rho`), so `reconstructPar -fields '(T)'` either fails to load
the BC or silently produces an invalid `T`. Every quantity in this spec depends on
`T` (bulk temperature, wall temperature, and the T-dependent properties `k`, `cp`),
so **none of it can be run until B1 is resolved** (recover the OF13 runtime + the
custom BC library — lane L4). Tracked in
`imports/2026-06-02_openfoam13_runtime_source.json`.

Until B1 clears the companion tool runs only `--dry-run`: it validates inputs,
prints the per-segment plan, and reports the missing-`T` blocker explicitly rather
than producing numbers from a bad reconstruction.

---

## 1. Definitions (exact, with units)

Per loop segment `j`, at a converged time `t`:

| Quantity | Symbol | Definition | Units |
| --- | --- | --- | --- |
| Wall heat flux | `q_w` | area-weighted mean `q` over the segment's wall patches, `Σ Q_p / Σ A_p` | W/m² |
| Wall heat duty per length | `q'_wall` | `Σ Q_p / L_seg` (segment wall duty per unit streamwise length) | W/m |
| Wall temperature | `T_wall` | area-weighted mean wall-face `T` over the segment's wall patches | K |
| Bulk temperature | `T_bulk` | **enthalpy-flux-weighted mixed mean** (see §2) | K |
| Heat-transfer coefficient | `h` (= HTC) | `h = q_w / (T_wall − T_bulk)` | W/m²/K |
| Thermal conductance / length | `UA'` | `UA' = q'_wall / (T_wall − T_bulk)` | W/m/K |
| Effective heat resistance / length | `R'_thermal` | `R'_thermal = 1 / UA'` | m·K/W |
| Hydraulic diameter | `D_h` | measured `4A/P` from the masked single-leg cut (§4) | m |
| Nusselt number | `Nu` | `Nu = h · D_h / k(T_bulk)` | 1 |

Consistency identity (must hold to within wall-perimeter discretization):
`UA' = h · P_wetted` where `P_wetted = (Σ A_p)/L_seg` is the wall perimeter, since
`q'_wall = q_w · P_wetted`. The tool reports both `h·P_wetted` and the directly
computed `UA'` so the two routes cross-check.

WHY UA' is primary, HTC secondary: the 1D energy march needs conductance per unit
length directly (`one_d_state_vector.csv`: `UAprime_seg[j]` = `energy_closure`,
admit; `HTC_seg[j]` = `diagnostic_or_alt_closure`, admit_secondary). UA' does not
require committing to a single reference `D_h`/perimeter geometry, so it is the more
robust surface; HTC and Nu are carried for comparison/diagnostics, and Nu is
admitted for *direct* 1D use only on `left_lower_leg` (closure map row
`left_lower_leg_nu_branch_aware_re_power_law`).

The sign convention: the solver writes `q` negative on heated/heating walls (heat
INTO the fluid is a negative wall flux in the FO, see the `wallHeatFlux.dat`
columns). The tool uses **signed** `q_w` and signed `(T_wall − T_bulk)` so that `h`,
`UA'` come out positive for a wall hotter than the bulk and negative for a cooler
wall (the cooler leg), without taking absolute values that would hide a reversed
sign. The legacy extractor used `|q_w| / |ΔT|`; we keep the sign to surface
physical inconsistencies (S8/S9 spirit).

---

## 2. Bulk temperature MUST be the enthalpy-flux-weighted mixed mean

Definition used (over the masked single-leg cut plane at the segment's measurement
station):

```
T_bulk = ∫ ρ u_n cp(T) T dA  /  ∫ ρ u_n cp(T) dA
```

discretized over cut-plane faces `f` as

```
T_bulk = Σ_f ρ_f u_{n,f} cp(T_f) T_f  /  Σ_f ρ_f u_{n,f} cp(T_f)
```

where `u_{n,f} = U_f · n` is the face-normal (throughflow) velocity and `n` is the
local centerline tangent (plane normal).

WHY enthalpy-flux weighting (not mass-flux-only, not area-average):
- The textbook mixed-mean ("bulk") temperature is defined so that
  `ṁ cp T_bulk = ∫ ρ u_n cp T dA` — i.e. it is the temperature that carries the
  correct **enthalpy flux**. Only with the `cp` weight does `T_bulk` reproduce the
  advected enthalpy, which is exactly what the 1D energy balance marches.
- For molten salt `cp` is (in general) **strongly temperature dependent**, so a
  mass-flux-only weight `∫ρ u_n T dA / ∫ρ u_n dA` mis-weights hot vs cold faces and
  biases `T_bulk` — and therefore `ΔT = T_wall − T_bulk`, `h`, `UA'`, and `Nu`. The
  current Salt cases happen to use a constant `Cp_coeffs = [1423.47]` (see any
  `case_config.yaml`), so for *those* cases the cp weight is a no-op; we still
  implement the cp weight because (a) the contract requires the correct definition,
  (b) future salts / refits may carry a real `cp(T)` polynomial, and (c) it makes
  the deviation from the textbook definition impossible to forget.
- An **area-average** `∫ T dA / ∫ dA` is wrong for advected energy whenever the
  velocity and temperature profiles are correlated (they always are in a heated
  duct: the near-wall fluid is both slow and hot/cold) and is rejected.

Reverse-flow handling: the integral includes `u_n` with its sign, so back-flow
faces contribute with negative weight — this is the correct enthalpy balance and
avoids the legacy bias (S9) of dropping reverse-flow faces. A station whose net
`Σ ρ u_n cp dA` is near zero (flow alignment below gate, e.g. a bend) is flagged
`low_flow_alignment` and its `T_bulk` is not trusted; pick a clean mid-leg station
for the bulk reference.

---

## 3. OpenFOAM fields / function objects required

| Need | Field / FO | Notes |
| --- | --- | --- |
| `q_w`, `q'_wall` | `wallHeatFlux` FO (`.dat`: Time, patch, min, max, **Q [W]**, **q [W/m²]**) | solver-written; `kappaEff·snGrad(T)`. **No `qr` column** → convective/conductive only (§6). |
| `T_wall` | reconstructed `T` on wall patches | **needs `libRCWallBC.so` → B1** |
| `T_bulk` | reconstructed `T` + `U` + `rho` on a cut plane | `T` needs B1; `U`,`rho` are standard-BC OK |
| `cp(T)`, `k(T)` | salt property polynomial from `case_config.yaml` `fluid_properties` | evaluated in-tool (see §5) — no field needed |
| `D_h` | measured `4A/P` from masked cut | reuse `sample_section_mean_pressure.py` geometry |

The wall duty `Q [W]` per patch comes straight from the FO and needs **no
reconstruction** (it is a scalar time series already on disk), so `q_w`, `q'_wall`,
and the wall perimeter can be assembled even while B1 blocks the `T` fields. This is
why the tool can validate most of the plan in `--dry-run`: only `T_wall`/`T_bulk`
(hence `ΔT`, `h`, `UA'`, `Nu`) are gated on B1.

---

## 4. Per-segment geometry & station (single-leg radius masking)

Use the SAME single-leg radius masking on raw cut-plane `.xy` dumps as
`tools/extract/sample_section_mean_pressure.py` (cut a plane perpendicular to the
local centerline tangent, dump raw faces, keep faces within `--leg-radius-m` of the
station point). This is required because OpenFOAM **Foundation** silently ignores
the `cuttingPlane` `bounds` keyword, so an unmasked plane spans two
counter-flowing legs and the enthalpy flux cancels (the same root cause as the
velocity anomaly). `D_h = 4A/P` is measured from the masked convex hull (a tight
lower bound on the true bore; documented in that tool).

Wall patches per segment come from the LOCKED profile via read-only import:
`get_case_analysis_profile(source_id).major_spans[span]["wall_patches"]`. The
segment wall duty and perimeter sum over exactly those patches.

---

## 5. Reference temperature & properties

Evaluate `k` and `cp` at the **segment bulk temperature `T_bulk`** (the mixed-mean
from §2), using the case's own salt polynomial (`fluid_properties` in
`case_config.yaml`: `kappa_spec.coeffs` for `k`, `Cp_coeffs` for `cp`, evaluated as
`Σ c_i T^i`). Decision + WHY: the bulk T is the single defensible reference for a
duct closure — `Nu = h D_h / k` and the cp weight in `T_bulk` must be
self-consistent, and the 1D model evaluates `k_seg`, `cp_seg` at the segment mean
bulk T as well (`one_d_state_vector.csv`). Using a fixed case-probe T instead would
desynchronize the CFD-side and 1D-side property evaluation. The film temperature
`(T_wall+T_bulk)/2` is NOT used for `k` in `Nu` because the closure consumer
(`build_dimensionless_bundle` in `tools/analyze/ethan_salt_hardening_common.py`)
evaluates at bulk T; we match it to keep the surfaces drop-in compatible.

Property model is read from the case config, not hard-coded, so a Jin/Kirst
viscosity swap or a refit cannot silently desync the properties.

---

## 6. `qr` radiative-flux exclusion (rad_on cases)

The `wallHeatFlux` FO header has columns `min/max/Q/q` only — there is **no `qr`
(radiative) column**. The extracted flux is therefore **conductive/convective at
the wall only** (`kappaEff·snGrad(T)`). For any `rad_on` case the salt-side HTC/UA'
produced here is a **convective-only** coefficient and EXCLUDES radiative wall
transport. The tool stamps every output row with a `qr_excluded_convective_only`
caveat and a `radiation_mode` column so the consumer never mistakes a rad-on
convective HTC for the total wall conductance. If a future run adds `qr` to the FO,
the total wall flux is `q + qr` and `h`, `UA'` must be recomputed.

---

## 7. Convergence prerequisite (gate before trusting any number)

UA'/HTC/Nu are meaningful only at a stationary operating point. **Gross wall duty
must be stationary** before extraction. Use
`tools/analyze/assess_time_convergence.py --paper-grade-salt-jin`, which normalizes
net heat by gross duty and reports flow + gross-heat-duty steadiness:
- **Salt 2 / 3 / 4 Jin: verified stationary** (flow + gross duty `<0.2%`, heat
  closes `<0.1%`) on both warmup and the mainline continuation → extraction
  defensible.
- **Salt 1 Jin: weaker** (`−2.08%`) → mark extracted UA'/HTC `provisional`;
  report the imbalance alongside the value.

The tool refuses (or flags `convergence_unverified`) if the case's convergence
status has not been asserted; pass the verified time and source-id from the
continuation reconstruction (`jadyn_runs/.../2026-06-18_convergence_and_jin_envelope_wave/runs/`).

---

## 8. Per-segment mapping (LOCKED segment map)

From `operational_notes/06-26/30/2026-06-30_cfd_to_1d_segment_map.md` (owner-confirmed) and
`tools/analyze/validate_segment_map.py`. The thermal closure operates on CFD spans,
which compose into 1D segments:

| 1D segment | CFD span(s) | role | thermal status |
| --- | --- | --- | --- |
| `lower_leg` (= `heated_incline`) | `lower_leg` | **heated** bottom leg | direct |
| `upcomer` | `left_lower_leg` + `test_section_span` + `left_upper_leg` | riser | UA' from component spans; `derived` |
| `downcomer` | `right_leg` | return | **thermally blocked** (`THERMAL_BLOCKED_BRANCHES`) |
| (cooler) | `upper_leg` | cooled leg | duty from imposed cooler BC |

WARNING (S16): `lower_leg` (heated bottom main-loop leg) is NOT `left_lower_leg`
(part of the upcomer). The tool keys strictly on the profile span names to avoid
the heated/unheated collision. Direct **Nu** is admitted for 1D use ONLY on
`left_lower_leg` (closure map). UA' is the primary surface on
`left_lower_leg | test_section_span | left_upper_leg | upcomer`.

---

## 9. Confidence boundaries (must be stamped on every output)

1. **Coarse mesh only (B2 / S5).** No mesh-independence bound exists on any
   UA'/HTC/Nu. Project rule: medium/fine required for publishable thermal closure.
   Every row is stamped `mesh=coarse, mesh_independence=UNESTABLISHED`. A 3-level
   GCI study (lane L5, `tools/analyze/compute_gci.py`) must bracket the
   discretization error before these enter a publishable 1D result.
2. **Single-branch direct Nu.** `Nu(Re,Pr)` is NOT identifiable: direct Nu is
   defended on `left_lower_leg` only, over a narrow laminar `Re ≈ 76–165` window,
   and much of that spread is the Jin/Kirst viscosity-model swap, not independent
   operating points. Treat as a single-regime calibration; clamp 1D queries to the
   fit Re window; never query for water.
3. **Pr not identifiable.** `Pr` is collinear with `Re` over the available cases
   (constant `cp`, weak `k(T)`), so no `Nu(Re,Pr)` separation is possible. Carry
   `Pr` as a reported property only.
4. **Convective-only (qr excluded)** for rad-on cases (§6).
5. **Salt 1 provisional** (convergence `−2.08%`, §7).
6. **B1 blocker**: the numbers cannot be produced until the OF13 runtime + custom
   BC are recovered; the dry-run plan is the deliverable until then.

---

## 10. Outputs

The companion tool writes, per segment:
- `segment_htc_uaprime_<source_id>.csv` and `.json` with columns:
  `segment, span(s), q_w_wm2, qprime_wall_wm, T_wall_k, T_bulk_k, delta_T_k,
  htc_wm2k, uaprime_wmk, R_prime_thermal_mkw, D_h_m, k_bulk_wmk, cp_bulk_jkgk,
  Nu, htc_times_perimeter_check, n_wall_patches, station_label, flow_alignment,
  convergence_status, radiation_mode` plus confidence columns
  `mesh, mesh_independence, qr_caveat, nu_direct_admitted, blocker_B1`.
- A top-level `method`, `definitions`, and `caveats` block in the JSON mirroring
  §1, §2, §6, §9 so the artifact is self-describing.

Run (after B1, on a reconstructed continuation case with `T U rho wallHeatFlux`):

```bash
python tools/extract/sample_segment_htc_uaprime.py \
    --case-dir tmp/<recon_salt2_jin_continuation> --time 7915 \
    --source-id viscosity_screening_salt_test_2_jin_coarse_mesh
```

Before B1, validate the plan with `--dry-run` (system python; do NOT source the OF
env):

```bash
python tools/extract/sample_segment_htc_uaprime.py \
    --case-dir <any_case_dir> --time <t> \
    --source-id viscosity_screening_salt_test_2_jin_coarse_mesh --dry-run
```
