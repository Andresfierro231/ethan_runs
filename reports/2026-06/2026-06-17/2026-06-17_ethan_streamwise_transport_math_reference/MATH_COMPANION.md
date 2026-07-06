# Ethan Streamwise Transport Math Companion

Generated: `2026-06-17`

This note documents the implemented math for the current streamwise transport
 package. It is written so later report or paper work does not have to infer
 the equations from code comments or CSV column names.

## Purpose

The package carries five coupled reduction families:

1. streamwise wall-shear hydraulic reduction
2. direct wall-registered pressure-gradient reduction
3. support-gated effective thermal reduction
4. momentum-resistance proxy reduction
5. branch-separated thermal reduction built from the validated major-span bins

The CFD solver does not directly solve for Darcy friction factor, Fanning
friction coefficient, effective HTC, `UA'`, thermal resistance, or momentum
resistance. Every one of those quantities is postprocessed from reconstructed
OpenFOAM fields plus geometry/profile metadata.

## Canonical output fields

The main package fields referred to in this note are:

- hydraulic:
  - `darcy_f`
  - `fanning_cf_shear`
  - `dp_major_gradient_pa_per_m`
  - `darcy_f_pressure_drop_prgh`
  - `fanning_cf_pressure_drop_prgh`
  - `dp_major_gradient_direct_prgh_pa_per_m`
  - `dp_major_gradient_direct_p_pa_per_m`
- thermal:
  - `t_wall_area_avg_k`
  - `bulk_temp_fluid_area_avg_k`
  - `bulk_temp_area_weighted_k`
  - `bulk_temp_tp_endpoint_proxy_k`
  - `bulk_minus_wall_temp_k`
  - `wall_heatflux_area_avg_w_m2`
  - `wall_heat_per_length_w_m`
  - `effective_htc_w_m2_k`
  - `effective_ua_per_m_w_m_k`
  - `effective_thermal_resistance_k_m_w`
- resistance:
  - `momentum_resistance_estimated_pa_s_kg_m`
  - `momentum_resistance_direct_prgh_pa_s_kg_m`
- branch thermal:
  - `branch_thermal_profiles.csv`
  - `branch_thermal_summary.csv`

## Notation

Let:

- `s` = local streamwise arclength within one repaired major span
- `Delta s_bin` = streamwise bin width
- `A_w,bin` = wall area assigned to one streamwise bin
- `P_w,bin` = inferred wetted perimeter
- `A_f,bin` = inferred flow area
- `D_h,bin` = inferred hydraulic diameter
- `rho_b` = bulk density used by the reduction
- `dot m` = span mass-flow magnitude used by the reduction
- `U_b` = inferred bulk speed
- `tau_w` = wall shear vector
- `tau_{w,s}` = projection of wall shear onto the repaired streamwise tangent
- `p` = OpenFOAM pressure field
- `p_rgh` = OpenFOAM pressure field with hydrostatic head removed
- `T_w` = wall-area-averaged wall temperature
- `T_b` = chosen cut-plane bulk-fluid temperature
- `Delta T = T_b - T_w`
- `q''_w` = wall-area-averaged wall heat flux
- `q'_w` = wall heat per unit length

Unless stated otherwise, wall means are wall-area-weighted means over the
faces assigned to one streamwise bin.

## Streamwise coordinate and bin basis

The current package reduces everything on the repaired major-span coordinate.
Each major span is defined by the case-analysis profile and represented by an
ordered polyline. Every selected wall face is projected onto that polyline to
obtain:

- projected streamwise coordinate `s_f`
- nearest streamwise tangent `hat t_f`
- distance from the face centroid to the polyline

The package then groups projected faces into bins constructed from the repaired
station definitions. Corners and junctions are not included in these major-span
bins.

This matters because all downstream branch reductions reuse these exact bins.
The new branch layer does not create a second geometry model.

## Geometry surrogates

The current package still uses a circular-perimeter surrogate to express
wall-based reductions in familiar hydraulic form.

For each bin:

`P_w,bin = A_w,bin / Delta s_bin`

Assuming a circular-perimeter surrogate:

`D_h,bin = P_w,bin / pi`

`A_f,bin = P_w,bin^2 / (4 pi)`

These are not exact geometric properties of the real loop. They are model-form
surrogates used to turn wall-based reductions into Darcy/Fanning-style
quantities.

Anything depending on `D_h` or `A_f` must therefore be read as
surrogate-dependent.

## Bulk density and bulk speed

The current density law is profile-authored:

`rho(T) = a - b T`

with current Salt/Water family defaults carried by the case profile.

The current major-loss reduction then infers bulk speed by:

`U_b = |dot m| / (rho_b A_f,bin)`

This `U_b` is not a directly sampled cross-sectional CFD mean. It is a reduced
bulk speed built from the chosen mass-flow input and the surrogate flow area.

## Shear-based hydraulic reduction

For each wall face in one bin, project wall shear onto the local streamwise
tangent:

`tau_{w,s,f} = tau_w(x_f) dot hat t_f`

The current major-loss reduction uses the magnitude of that projected streamwise
shear:

`|tau_{w,s,f}|`

The wall-area-weighted mean streamwise wall shear is:

`bar tau_{w,s} = (sum_f A_f |tau_{w,s,f}|) / (sum_f A_f)`

The current shear-based Darcy friction factor is:

`f_D,shear = 8 bar tau_{w,s} / (rho_b U_b^2)`

The current Fanning friction coefficient is:

`C_f,shear = f_D,shear / 4`

The current shear-implied major pressure gradient is:

`(dp/ds)_shear = f_D,shear rho_b U_b^2 / (2 D_h,bin)`

This is what the package writes to:

- `darcy_f`
- `fanning_cf_shear`
- `dp_major_gradient_pa_per_m`

## Direct wall-registered pressure-gradient reduction

The package also computes a direct pressure-drop diagnostic from wall-area-
averaged pressure fields. This is a wall-registered reduction, not a centerline
probe history and not a control-volume momentum balance.

For each bin:

`bar p_rgh,bin = (sum_f A_f p_rgh,f) / (sum_f A_f)`

`bar p_bin = (sum_f A_f p_f) / (sum_f A_f)`

The package then finite-differences the ordered bin means along local span
arclength.

Endpoint bins use one-sided differences:

`g_0 = - (bar p_1 - bar p_0) / (s_1 - s_0)`

`g_N = - (bar p_N - bar p_{N-1}) / (s_N - s_{N-1})`

Interior bins use centered differences:

`g_i = - (bar p_{i+1} - bar p_{i-1}) / (s_{i+1} - s_{i-1})`

The sign is then aligned so positive means pressure drop along the physical
flow direction:

`(dp/ds)_direct,prgh = sign_align * g_i`

`(dp/ds)_direct,p = sign_align * g_i^p`

The current pressure-drop-based Darcy and Fanning reductions are:

`f_D,prgh = 2 D_h,bin (dp/ds)_direct,prgh / (rho_b U_b^2)`

`C_f,prgh = f_D,prgh / 4`

These are what the package writes to:

- `dp_major_gradient_direct_prgh_pa_per_m`
- `dp_major_gradient_direct_p_pa_per_m`
- `darcy_f_pressure_drop_prgh`
- `fanning_cf_pressure_drop_prgh`

## Why `p_rgh` is the primary direct hydraulic field

The direct hydraulic comparison is anchored on `p_rgh`, not `p`, because `p`
contains the hydrostatic variation of the buoyant loop. For friction-scale
interpretation, the current package treats wall-area-averaged `p_rgh` as the
more relevant field.

That does not make the direct result a gold standard. It is still a
wall-registered diagnostic reduced on repaired bins and finite-differenced in
postprocessing.

## Streamwise thermal reduction

For each streamwise bin and retained time, the package samples OpenFOAM `T` and
`U` on a cut plane whose:

- plane point = repaired bin-center point
- plane normal = repaired streamwise tangent

The sampled plane may intersect multiple connected face regions. The current
package:

1. reconstructs connected face regions on that plane
2. computes a local signed and positive aligned mass-flux support for each
   region
3. chooses one region by aligned-flow support plus area agreement to the
   reference monitor area

The chosen-region positive aligned mass flux is:

`dot m_R^+ = sum_{j in R} max(0, sign_hint dot m_j)`

with local face mass flux:

`dot m_j = rho_j (U_j dot hat n) A_j`

The primary bulk temperature is the chosen-region mass-flux-weighted mean:

`T_b = (sum_{j in R*} dot m_j^+ T_j) / (sum_{j in R*} dot m_j^+)`

The package also carries comparison quantities:

- `bulk_temp_area_weighted_k`
- `bulk_temp_union_area_avg_k`
- `bulk_temp_tp_endpoint_proxy_k`

## Effective thermal variables

For one streamwise bin:

`Delta T = T_b - T_w`

`q'_w = q''_w P_w,bin`

The primary effective thermal quantities are then:

`h_eff = |q''_w| / |Delta T|`

`UA'_eff = |q'_w| / |Delta T|`

`R'_th,eff = 1 / UA'_eff`

These are what the package writes to:

- `effective_htc_w_m2_k`
- `effective_ua_per_m_w_m_k`
- `effective_thermal_resistance_k_m_w`

The TP-endpoint proxy versions use the same numerator but substitute:

`Delta T_proxy = T_b,TPproxy - T_w`

and are written to the `*_tp_endpoint_proxy_*` fields.

## Why effective HTC and `UA'` can blow up

These ratios become unstable when the denominator collapses:

- `|T_b - T_w|` becomes very small
- the chosen cut-plane support is disconnected or area-mismatched
- the positive aligned mass flux becomes too small to define a stable bulk
  state

The package therefore does not treat these quantities as unconditional local
coefficients. They are support-gated effective indicators.

## Thermal QC and masking gates

The primary effective thermal quantities are only reported when all of the
following are true:

1. the chosen region status is `aligned_area_match`
2. chosen-region positive aligned mass flux exceeds the current minimum
   tolerance
3. chosen-region area ratio to the reference area stays inside `[0.5, 2.0]`
4. `|T_b - T_w| >= 0.25 K`

If any gate fails:

- wall temperature and wall heat flux are still retained
- bulk-temperature diagnostics are still retained where sampled
- effective `HTC`, `UA'`, and `R'_th` are written as `NaN`
- `thermal_support_status` records why the row was masked

That masking behavior is intentional. It is the reason the current package
still has trustworthy gaps instead of smooth but misleading spikes.

## Momentum-resistance proxies

The package currently carries two local momentum-resistance proxies. These are
not yet canonical publication-ready nondimensional groups.

Estimated from shear-implied major pressure gradient:

`R_m,est = (dp/ds)_shear / dot m`

Direct from wall-registered `p_rgh` gradient:

`R_m,direct = (dp/ds)_direct,prgh / dot m`

These are written to:

- `momentum_resistance_estimated_pa_s_kg_m`
- `momentum_resistance_direct_prgh_pa_s_kg_m`

They are useful for comparing where the loop imposes stronger or weaker
resistance on the same repaired coordinate. They should not be promoted to a
stronger theoretical status than that.

## Branch-separated thermal reduction

The new branch layer does not rerun extraction. It reuses the validated
major-span cumulative rows already assembled by the package builder.

### Branch set

The current branch outputs include the six first-class span sections:

- `lower_leg`
- `right_leg`
- `left_lower_leg`
- `test_section_span`
- `left_upper_leg`
- `upper_leg`

and one derived branch:

`upcomer = left_lower_leg + test_section_span + left_upper_leg`

### Branch coordinate

For a derived branch, the current builder concatenates the local span
coordinates in the declared order:

`s_branch = offset(span_k) + s_local`

The offsets are built from the repaired span lengths only. Corners and
junctions are intentionally skipped. The resulting branch coordinate is
therefore:

- continuous across the reused major spans
- not a full geometric arclength including omitted corner/junction material

### Branch profile rows

`branch_thermal_profiles.csv` is a row-level derived view of the major-span
thermal rows. It preserves:

- original `span_name`
- original bin-level thermal fields
- branch-local `branch_s_*` coordinates
- one `branch_profile_index` used for time averaging on a branch-local axis

### Branch summary weighting

The branch summaries are flow-weighted using the same support-qualified thermal
state the primary effective variables use.

For one row:

`w_branch,row = dot m_positive,row * Delta s_row`

where `dot m_positive,row` is the chosen-region positive aligned mass flux.

The branch summary uses these weights only on rows whose
`thermal_support_status == usable`.

That means:

- branch mean `HTC`, `UA'`, `R'_th`, bulk temperature, and wall temperature are
  all built from the same support-qualified thermal rows
- masked rows remain visible in counts and warning fractions, but they do not
  contaminate the branch thermal means

Branch wall-heat-per-length means use length-weighting rather than the stricter
thermal support weight, because `q'_w` itself is still a meaningful wall-side
diagnostic even when `Delta T` support is not good enough for ratio metrics.

## Safe interpretation boundaries

Safe:

- compare shear-based and direct wall-registered hydraulic indicators on the
  same repaired coordinate
- discuss where effective thermal driving force collapses and where transfer is
  support-qualified versus masked
- discuss branch-local redistribution of bulk temperature and support-qualified
  effective transfer indicators

Not safe without stronger qualification:

- describe `effective_htc_w_m2_k` as an intrinsic local HTC
- describe `effective_ua_per_m_w_m_k` as a geometry-independent transport law
- treat `R_m,est` or `R_m,direct` as canonical momentum-resistance coefficients
- treat branch `upcomer` distance as a full geometric arclength that includes
  corners and junctions

## Cross-check files

Use this note with:

- the current per-case `summary.json`
- `major_loss_summary.csv`
- `major_loss_cumulative_timeseries.csv`
- `branch_thermal_profiles.csv`
- `branch_thermal_summary.csv`
- `streamwise_heat_loss_summary.csv`
- `parasitic_heat_loss_summary.csv`

## Implementation references

- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/analyze/build_ethan_case_analysis_package.py`
- `tools/case_analysis_profiles.py`
