# Salt 2 Case Analysis: Mathematical Method Companion

Generated alongside the June 10 Salt 2 case-analysis package.

This note is the explicit mathematical companion to the package in this directory. It is written to make the reduction rules, assumptions, and known limitations inspectable without reading the implementation code first. The goal is credibility, not rhetorical smoothness.

## Purpose

The package combines three analysis layers:

1. Legwise major-loss reduction on a repaired streamwise coordinate.
2. Feature-based minor-loss pressure budgeting between named NCC interfaces.
3. Case-scoped heat accounting and streamwise thermal indicators.

The CFD solver does not solve directly for "friction factor", "major loss", "minor loss coefficient", "HTC", or "UA'". Those are all postprocessed derived quantities computed from reconstructed OpenFOAM fields and metadata.

## Scope And Data Basis

- Case: `val_salt_test_2_coarse_mesh_laminar`
- Profile: `salt2_val_case_v1`
- Frozen hydraulic retained times in the current package: `7483, 7484, 7485, 7486, 7487 s`
- Heat accounting tail in the current package extends to `7506 s`

Hydraulic and streamwise thermal quantities are frozen to the retained hydraulic window above. Heat accounting is a late-tail summary over the current live `wallHeatFlux` history and is therefore not tied to the same frozen window.

## Notation

Let:

- `s` = local streamwise arclength coordinate within a span
- `A_w,bin` = total wall-face area in one streamwise bin
- `Delta s_bin` = width of one streamwise bin
- `P_w,bin` = estimated wetted perimeter in one bin
- `D_h,bin` = estimated hydraulic diameter in one bin
- `A_f,bin` = estimated flow area in one bin
- `rho` = local bulk density used by the package
- `dot m` = magnitude of mass-flow rate assigned to the span
- `U_b` = inferred bulk speed in the bin
- `tau_w` = wall shear stress vector
- `tau_{w,s}` = streamwise projection of wall shear stress
- `p` = OpenFOAM pressure field
- `p_rgh` = OpenFOAM pressure field with hydrostatic head removed
- `T_w` = wall-area-averaged wall temperature
- `q''_w` = wall-area-averaged wall heat flux
- `T_b` = chosen bulk-fluid temperature from the matched cut-plane method
- `Delta T` = `T_b - T_w`

All area averages below are wall-face-area-weighted unless otherwise stated.

## Streamwise Coordinate Construction

The package does not use one universal geometry proxy for every span.

### TP/TW polyline spans

For spans where the TP/TW sequence remains geometrically acceptable, the local streamwise coordinate is built from the ordered probe locations:

`x_0, x_1, ..., x_n`

with piecewise-linear interpolation between successive points.

### Anchored patch-centroid polyline spans

For repaired spans such as `lower_leg` and `right_leg`, the streamwise path is built from:

1. NCC start-patch centroid
2. ordered wall-patch centroids
3. NCC end-patch centroid

again as a piecewise-linear polyline.

This matters because station generation and wall-face projection must use the same path. A numerically stable reduction is not trustworthy if the bins are constructed on one path and wall faces are projected onto another.

## Face Projection And Binning

For each selected wall face with centroid `x_f`, the package computes its nearest projection onto the local span polyline. This gives:

- projected arclength `s_f`
- distance from face centroid to the polyline
- local tangent direction `hat t_f`

Bins are defined from streamwise station centers. If station centers are `s_0, ..., s_N`, the bin edges are midpoint-based:

- first bin start = `0`
- interior edge between stations `i` and `i+1` = `0.5 (s_i + s_{i+1})`
- last bin end = span terminal arclength

Every wall face is assigned to one bin by projected `s_f`.

## Wall-Shear Reduction

For each wall face, project the wall shear vector onto the local tangent:

`tau_{w,s,f} = tau_w(x_f) dot hat t_f`

The package carries both the signed projection and its magnitude. The major-loss reduction uses the magnitude:

`|tau_{w,s,f}|`

The wall-area-weighted bin mean is:

`bar tau_{w,s} = (sum_f A_f |tau_{w,s,f}|) / (sum_f A_f)`

where the sum is over wall faces in the bin.

The package also computes a weighted standard deviation and a max relative deviation diagnostic to detect bins with large within-bin wall-shear variation.

## Geometry Surrogate For `P_w`, `D_h`, And `A_f`

This is one of the most important model-form assumptions in the package.

Given bin wall area `A_w,bin` and bin width `Delta s_bin`, estimate wetted perimeter by:

`P_w,bin = A_w,bin / Delta s_bin`

Then assume a circular-perimeter surrogate:

`D_h,bin = 4 A_f,bin / P_w,bin`

and for a circular cross-section:

`P = pi D`

`A = pi D^2 / 4`

which implies:

`D_h,bin = P_w,bin / pi`

`A_f,bin = P_w,bin^2 / (4 pi)`

This is not a geometric identity of the actual CFD loop. It is a surrogate used so that wall-based reductions can be expressed in familiar hydraulic form. The report should treat any quantity depending on `D_h` or `A_f` as model-dependent.

## Bulk Density And Bulk Speed

### Density

The package uses a linear temperature-density law:

`rho(T) = a - b T`

with case-profile parameters:

- `a = 2293.6`
- `b = 0.7497`

For major-loss bins, the span-level bulk density is taken from TP-based temperatures when available and otherwise falls back to a global TP-bulk density map.

### Bulk speed

Given span mass flow `dot m` and inferred flow area `A_f,bin`:

`U_b = |dot m| / (rho A_f,bin)`

This is a reduction quantity, not a directly sampled cross-sectional mean of the CFD velocity field.

## Shear-Based Darcy Friction Factor

The primary wall-shear-based Darcy factor is:

`f_D,shear = 8 bar tau_{w,s} / (rho U_b^2)`

This is the standard Darcy relation recovered from wall shear under a bulk-speed interpretation.

It is only as credible as:

1. the streamwise wall-shear projection
2. the inferred `rho`
3. the inferred `U_b`
4. the surrogate `A_f,bin`

## Shear-Based Major Pressure Gradient

From Darcy-Weisbach:

`(dp/ds)_shear = f_D,shear rho U_b^2 / (2 D_h,bin)`

This is reported as a positive pressure-drop magnitude along the local streamwise coordinate.

The bin pressure drop is:

`Delta p_bin = (dp/ds)_shear Delta s_bin`

and the cumulative major loss along a span is the running sum over bins.

## Direct Wall-Pressure-Gradient Reduction

The package also computes a direct wall-registered pressure-drop diagnostic from area-averaged `p_rgh`.

### Why `p_rgh` and not `p`

The direct comparison is made against `p_rgh`, not `p`, because `p` contains hydrostatic variation that dominates the friction-scale signal in this buoyant loop. Therefore `p_rgh` is the correct field for comparing to wall-loss-like pressure gradients.

### Binwise wall-pressure averages

For each bin:

`bar p_rgh,bin = (sum_f A_f p_rgh,f) / (sum_f A_f)`

and similarly for `bar p_bin`.

### Finite difference

Let the ordered bin centers be `s_i` with values `bar p_rgh,i`.

The package uses one-sided differences at the endpoints and centered differences in the interior:

- first bin:
  `g_0 = - (bar p_rgh,1 - bar p_rgh,0) / (s_1 - s_0)`
- last bin:
  `g_N = - (bar p_rgh,N - bar p_rgh,N-1) / (s_N - s_N-1)`
- interior:
  `g_i = - (bar p_rgh,i+1 - bar p_rgh,i-1) / (s_i+1 - s_i-1)`

The sign convention is then aligned so that positive means pressure drop along the actual flow direction.

### Flow-alignment sign

For each retained time and span, compare the first and last valid `bar p_rgh` values. If the local span coordinate is opposite to the physical pressure drop, multiply the direct gradient by `-1`.

This produces the package field:

`(dp/ds)_direct,prgh`

### Pressure-drop-based Darcy factor

Using the same surrogate `D_h` and inferred `rho, U_b`:

`f_D,prgh = 2 D_h,bin (dp/ds)_direct,prgh / (rho U_b^2)`

This quantity is useful as a consistency diagnostic, not as a gold-standard truth. It still depends on the same surrogate `D_h` and inferred `U_b`.

## Feature Minor-Loss Budget

Each feature object is defined by named NCC start and end patches. For each retained time, the raw feature extractor computes:

- area-averaged start and end `p`
- area-averaged start and end `p_rgh`
- total feature pressure difference

with sign convention:

`Delta p_rgh,feature = p_rgh,end - p_rgh,start`

The integrated package then uses:

`|Delta p_rgh,feature|`

as the total feature-associated pressure scale.

### Reference major-loss subtraction

For a feature adjoining one or more major spans, define a reference length `L_ref` from nearby probe geometry and define a reference major wall-loss contribution from adjacent span mean gradients:

`Delta p_ref,major = mean((dp/ds)_major,adjacent) L_ref`

Then define:

`Delta p_minor,residual = |Delta p_rgh,feature| - Delta p_ref,major`

and a reference minor coefficient:

`K_minor,ref = 2 Delta p_minor,residual / (rho_ref U_ref^2)`

where `rho_ref` and `U_ref` are adjacent-span reference values.

This is a first-budget split, not a rigorous local decomposition of the feature flow physics. Negative residuals are treated as caveats, not as established "negative losses".

## Heat Accounting

Heat accounting is based on `wallHeatFlux.dat` section sums, not on the streamwise thermal reduction.

Let `Q_section` be the signed integrated wall heat flow over the section patch set.

The package reports:

- heater input section
- cooling branch removal
- downcomer, upcomer, lower transport, upper transport, test-section, and junction section totals
- net total closure

The important conservation check is:

`Q_net,total = sum_sections Q_section`

Near-zero `Q_net,total` means the section partition closes numerically at the analyzed tail.

The ambient proxy reported in the package is a diagnostic partition, not an extra independent term to add on top of the total removal.

## Streamwise Thermal Bulk-Temperature Method

This is the most delicate part of the current methodology.

For each streamwise bin and retained time, a cut plane is defined by:

- plane point = bin-center point on the repaired streamwise path
- plane normal = local tangent direction

OpenFOAM sampled surfaces are then used to sample both `T` and `U` on that plane.

### Connected-region parsing

The raw sampled cut plane may intersect more than one connected region. Therefore the package:

1. reads sampled points and faces
2. builds face-edge adjacency
3. partitions the plane into connected face regions

### Regionwise mass flux

For each sampled face `j` in a region:

- sampled temperature `T_j`
- sampled velocity `U_j`
- plane normal `hat n`
- face area vector `A_j hat n_j`

Density is inferred locally:

`rho_j = a - b T_j`

Face signed mass flux is:

`dot m_j = rho_j (U_j dot hat n) A_j`

The profile provides a `flow_direction_sign_hint`, currently `+1` for all Salt 2 major spans. Define aligned flux:

`dot m_j^+ = max(0, sign_hint dot m_j)`

### Region selection

For each connected region `R`, compute:

- total area `A_R`
- positive aligned mass flux `dot m_R^+ = sum_{j in R} dot m_j^+`
- signed aligned flux
- area-weighted temperature
- mass-flux-weighted temperature

The region-selection rule is:

1. keep regions with aligned signed mass flux
2. keep only regions with `dot m_R^+` at least `25%` of the largest aligned region positive mass flux
3. among those, choose the region with the smallest absolute log-area error versus the reference area
4. if none survive, choose the best area-matching region anyway and flag the support

Reference area here is the span mdot-monitor area, not the wall-area-derived flow surrogate.

### Bulk temperature

The primary matched bulk temperature is:

`T_b = (sum_{j in R*} dot m_j^+ T_j) / (sum_{j in R*} dot m_j^+)`

where `R*` is the chosen region.

The package also retains:

- chosen-region area-weighted temperature
- union area-weighted temperature over all cut-plane faces
- TP-endpoint bulk-temperature proxy

for comparison and debugging.

## Effective HTC And Effective `UA'`

Let:

`Delta T = T_b - T_w`

`q'_w = q''_w P_w,bin`

Then the package defines:

`h_eff = |q''_w| / |Delta T|`

`UA'_eff = |q'_w| / |Delta T|`

These are explicitly effective CFD-side transfer indicators. They are not intrinsic local convective coefficients unless the support assumptions are accepted and the thermal resistance structure is interpreted very carefully.

## Thermal Support Gates

The primary effective HTC and `UA'` are only reported when all of the following are true:

1. chosen-region area ratio to reference area is in `[0.5, 2.0]`
2. aligned positive mass flux is above tolerance
3. region selection did not fall back to a wrong-sign or unsupported region
4. `|Delta T| >= 0.25 K`

If any gate fails:

- raw temperature and heat-flux diagnostics are retained
- `h_eff` and `UA'_eff` are written as `NaN`
- an explicit `thermal_support_status` is written

This masking is deliberate. It prevents known bad-support bins from contaminating the plotted local transfer curves.

## Reconstructed-Field Sanitization

Some reconstructed retained `T` files contained literal invalid scalar tokens such as `-nan`.

The package does not mutate the source runtime tree. Instead it sanitizes only the temp extraction case. The rule is:

- replace standalone invalid scalar token with the mean of nearest previous and next finite scalar tokens when both exist
- otherwise use the nearest finite neighbor
- use `0.0` only if no finite neighbors exist

The replacement counts are written to:

- `raw_extraction/thermal_sanitization_summary.json`
- `raw_extraction/leg_major_loss_extraction_summary.json`
- `summary.json`

and should agree exactly.

## Numerical And Methodological Limitations

The most important limitations are:

1. `D_h` and `A_f` are surrogate quantities inferred from wall area per unit length using a circular-perimeter assumption.
2. The direct pressure-drop comparison is wall-registered and finite-differenced on bin averages, not a centerline or volume-integrated momentum balance.
3. The streamwise thermal bulk-temperature reduction still depends on a profile-authored flow-direction hint.
4. The region-selection procedure is algorithmic and defensible, but not unique. Another reasonable support-selection rule could produce slightly different local `T_b` and therefore different local `h_eff`.
5. Effective HTC and `UA'` are masked support-filtered indicators, not clean intrinsic material or convective coefficients.
6. The heat-accounting tail and the frozen hydraulic window are not identical time bases.
7. Feature minor-loss residuals are budget residuals after subtracting an inferred major-loss reference, not direct measurements of pure form drag.

## What Is Credible To Claim

Credible:

- the repaired streamwise coordinate materially improved geometric registration
- the package now supports a coherent loopwise comparison of shear-based and direct-pressure-based hydraulic indicators
- the streamwise thermal method is more credible than the old TP-endpoint proxy because it uses matched cut-plane field samples
- the support-gated thermal curves are better behaved and more honest than the earlier unfiltered curves

Not yet fully credible without stronger qualification:

- interpreting `h_eff(s)` as an intrinsic local HTC
- treating pressure-drop-based and shear-based `f_D` agreement as a proof that the hydraulic model form is exact
- treating negative feature residuals as settled physical evidence of local pressure recovery mechanisms

## Files To Use With This Note

Use this companion together with:

- `README.md`
- `summary.json`
- `major_loss_summary.csv`
- `major_loss_cumulative_timeseries.csv`
- `raw_extraction/bulk_cross_section_temperature_samples.csv`
- `raw_extraction/thermal_sanitization_summary.json`
- `figures/png/case_loopwise_thermal_profiles.png`
- `figures/png/case_loopwise_thermal_support_qc.png`

## Implementation References

The current implementation lives primarily in:

- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/analyze/build_ethan_case_analysis_package.py`
- `tools/case_analysis_profiles.py`
- `tools/extract/sample_streamwise_friction_patch_averages.py`

If the package and this note ever disagree, treat the package outputs and current code as authoritative and then update this note immediately.
