# Ethan Runs Update

Date: 2026-06-10

## Observed Outputs

- Completed the full Salt 2 major-loss registration repair in `tools/case_analysis_profiles.py` and `tools/extract/sample_leg_centerline_major_loss.py`.
- Rebuilt `reports/2026-06-10_ethan_salt2_case_analysis_package/` on a frozen hydraulic window of `7353, 7354, 7355, 7356, 7357` s. The current package heat tail extends to `7365` s; see `summary.json`.
- The final package has no quarantined major-loss spans. This is a material change from the earlier June 10 state where `lower_leg` and then later only `right_leg` were still quarantined by projection-distance diagnostics.
- The repaired major-loss summary now reports:
  - `lower_leg`: `mean_darcy_f = 0.8925998301184789`, `valid_bin_count = 460`, `total_bin_row_count = 460`, `empty_bin_fraction = 0.0`, `median_face_distance_to_centerline_m = 0.01102534324076041`, `p95_face_distance_to_centerline_m = 0.011844021316045825`
  - `right_leg`: `mean_darcy_f = 1.122555440907394`, `valid_bin_count = 465`, `total_bin_row_count = 465`, `empty_bin_fraction = 0.0`, `median_face_distance_to_centerline_m = 0.011025343240929148`, `p95_face_distance_to_centerline_m = 0.011025343265719694`
- In `raw_extraction/leg_major_loss_extraction_summary.json`, both repaired spans now record `streamwise_coordinate_method = patch_centroid_polyline`.
- In `raw_extraction/leg_centerline_station_definitions.csv`, the repaired `right_leg` bins begin on anchored segments such as `ncc_pipeleg_right_01_lower_start -> pipeleg_right_01_lower`, confirming that the streamwise path now includes the true span endpoints rather than starting at the first wall-patch centroid.
- Also fixed two package-refresh provenance bugs in `tools/analyze/build_ethan_case_analysis_package.py`:
  - `--raw-extraction-dir` no longer fails when the source raw-extraction tree is the package's own `raw_extraction/` directory.
  - When raw extraction is reused, `summary.json` and `analysis_manifest.json` now preserve the raw extractor's retained times and frozen runtime root instead of stamping a newer live selected-time window onto older hydraulic artifacts.

## How The Full Hydraulic Repair Was Done

- The earlier June 10 diagnosis was correct about the core failure mode: the TP/TW-derived polyline was a bad centerline surrogate for both `lower_leg` and `right_leg`. It produced huge projected wall-face distances and sparse or empty major-loss bins.
- The first repair pass replaced `lower_leg` with a wall-patch-centroid polyline. That fixed most of the lower-leg collapse but intentionally left `right_leg` untouched until its geometry was checked separately.
- The follow-on `right_leg` prototype showed that a simple three-wall-patch centroid path was still incomplete. It brought the median projected distance down to about `0.011 m`, but the p95 stayed around `0.130 m` because the path terminated at the wall-patch centroids instead of the actual span boundaries.
- The final repair generalized the method: every span using `patch_centroid_polyline` now uses an anchored explicit polyline built from:
  - the NCC start-patch centroid
  - the ordered wall-patch centroids
  - the NCC end-patch centroid
- This anchored polyline is then used consistently for both:
  - station/bin generation
  - wall-face projection and tangent evaluation
- That consistency is the main method requirement. If bins are generated on one path and wall faces are projected onto another, the major-loss statistics can look numerically stable while still being geometrically inconsistent.
- In practice, the right-leg anchored path now runs from `ncc_pipeleg_right_01_lower_start` through `pipeleg_right_01_lower`, `pipeleg_right_02_middle`, `pipeleg_right_03_upper`, and out to `ncc_pipeleg_right_03_upper_end`.
- The same anchored-path generalization also improved the already repaired `lower_leg`, because its explicit path now covers the real start and end interfaces instead of only the interior wall-patch centroids.

## Assumptions

- Assumption 1: the `wall_patches` order in `tools/case_analysis_profiles.py` is already the correct streamwise sequence for both repaired spans.
  If the patch order is wrong, the polyline will still be wrong even if the distances to that polyline look small.
- Assumption 2: the area-weighted centroids of the major wall patches are acceptable local surrogates for the pipe centerline.
  This assumes each patch represents a sufficiently complete circumferential wall slice rather than a strongly partial wall region.
- Assumption 3: the NCC `start_patch` and `end_patch` centroids lie on or very near the true span centerline and are therefore valid endpoint anchors.
  This is the critical extra assumption that made the full right-leg repair possible.
- Assumption 4: straight line segments between successive anchors and wall-patch centroids are an acceptable discrete approximation to the true span centerline.
  I did not fit higher-order curves or attempt curvature smoothing.
- Assumption 5: the correct repair target was streamwise registration, not the local hydraulic-diameter estimator.
  The circular-perimeter estimate for local wetted perimeter, hydraulic diameter, and area was left unchanged.
- Assumption 6: the raw extractor's own retained-time metadata is authoritative when a package is rebuilt from an existing `raw_extraction/` tree.
  This is why the refresh-path bug fix now rewrites `summary.json` and `analysis_manifest.json` to match the raw extractor metadata instead of the newer live selected times.
- Assumption 7: even after the geometric repair, the existing warning heuristic based on `tauw_streamwise_max_rel_dev > 0.20` remains conservative enough that warning-heavy spans can still be geometrically usable.

## Validation And Before/After Evidence

- Before any patch-centroid repair, the earlier June 10 fix-pass documented:
  - `lower_leg` median projected face distance about `0.444 m`
  - `right_leg` median projected face distance about `0.468 m`
  - `right_leg` p95 projected face distance about `0.872 m`
  - `right_leg` valid bins `105 / 470`
  - `right_leg` empty-bin fraction `0.776595744680851`
  - package-level quarantine for the misregistered spans
- After the first lower-leg-only repair, `lower_leg` was usable but `right_leg` remained quarantined.
- The right-leg prototype showed the key distinction:
  - wall-patch centroids alone fixed the middle of the leg but not the ends
  - adding NCC start/end anchors reduced the full-span right-leg distance distribution to the same centimeter scale as the trusted spans
- In the final rebuilt package:
  - `right_leg` median distance is `0.011025343240929148 m`
  - `right_leg` p95 distance is `0.011025343265719694 m`
  - `right_leg` has zero empty-bin fraction and full retained-window coverage
  - no major-loss spans remain quarantined
- The anchored generalization also materially improved `lower_leg`:
  - the earlier lower-leg-only package had `mean_darcy_f` about `6.54`
  - the final anchored package reduced that to `0.8925998301184789`
  - lower-leg distance metrics stayed in the same trusted centimeter-scale band
- The refresh-path provenance fixes were also validated directly:
  - the first reused-raw refresh exposed a mismatch where the package stamped newer requested times than the hydraulic raw data actually represented
  - after the builder fix, `README.md`, `summary.json`, and `analysis_manifest.json` all consistently report the actual raw-extraction hydraulic window `7353-7357 s`

## Interpretation

- The hydraulic registration problem is now fixed at the package level. The final Salt 2 case package has a single frozen hydraulic window, no quarantined major-loss spans, and geometry diagnostics for `lower_leg` and `right_leg` that are on the same scale as the previously trustworthy spans.
- The most important change is not just that `right_leg` left quarantine. It is that the repair method is now case-profile-driven and span-scoped:
  - TP/TW surrogate where it still works
  - anchored explicit polyline where the TP/TW surrogate fails
- This is the right modular pattern for later CFD cases, because it avoids forcing every span through one geometry proxy.
- The repaired major-loss outputs are now suitable for careful span-level interpretation, but they are not automatically interpretation-clean. Every span is still `warning_heavy`, which means the geometry problem is solved while the shear-variation and local-statistics caution remains.
- The feature minor-loss package also shifted slightly after the full hydraulic repair. The current negative residual feature set is `corner_lower_left`, `corner_lower_right`, and `corner_upper_left`. Those are still better treated as reference-budget caveats than as settled negative-loss physics.

## Contradictions / Caveats

- No major-loss spans are quarantined anymore, but the package is still not a fully review-clean scientific endpoint.
- `profile_dp_pa` remains unsampled directly, and feature `wall_dp_pa` is still inferred from adjacent major-span gradients.
- The local hydraulic geometry estimate still depends on a circular-perimeter assumption derived from wall area per unit length.
- All major-loss spans remain `warning_heavy`, so robust interpretation should lean more on medians, quantiles, and consistency across times than on a mean alone.
- The heat-accounting package is newer than the direct-validation thermal reference. The heat tail in the current package is `7365 s`, while the carried validation reference still ends at `3871.0 s`.
- The repair method depends on stable patch naming and ordering. It should not be copied blindly to another case without verifying that the relevant wall and interface patches have the same geometric meaning.

## Suggested Next Actions

- Run a focused reviewer pass on the full hydraulic repair:
  - confirm the wall-patch ordering is truly streamwise for both repaired spans
  - confirm the NCC start/end centroids are valid endpoint anchors
  - confirm the now-unquarantined `right_leg` friction and gradient trends are physically plausible
- Add a short robust-statistics view for major-loss reporting so `darcy_f` medians and upper quantiles are readily available alongside means.
- Revisit the feature-budget reference model, especially for `corner_lower_right`, since the full hydraulic repair moved that feature into the negative-residual set.
- Keep future package refreshes on the script path. The raw-reuse provenance fixes are now in the builder, so the June 10 package can be regenerated without hand-editing its manifest or README.

## Report-Prep Hydraulic And Thermal Method Extension

### Observed Outputs

- Rebuilt `reports/2026-06-10_ethan_salt2_case_analysis_package/` again on a frozen hydraulic window of `7391, 7392, 7393, 7394, 7395` s with the current heat tail extending to `7401` s; see `summary.json` and `analysis_manifest.json`.
- Added direct wall-pressure comparison products to the major-loss package:
  - `major_loss_cumulative_timeseries.csv` now carries wall-area-averaged `p` and `p_rgh`, direct `p_rgh` pressure-drop gradients, direct-pressure-based `Darcy f`, and a per-span `flow_alignment_sign`.
  - New figure products are written under `figures/`:
    - `case_major_friction_profiles_comparison`
    - `case_major_pressure_gradient_profiles_comparison`
    - `case_loopwise_friction_comparison`
    - `case_loopwise_pressure_gradient_comparison`
- The new loopwise plots are intentionally built on the physical loop order
  `lower_leg -> right_leg -> upper_leg -> left_upper_leg -> test_section_span -> left_lower_leg`,
  rather than the earlier convenience ordering used for some package tables.

### Why Pressure Gradient Can Be Gotten More Directly

- The solver itself is not solving a scalar called “friction factor.” It solves the fluid fields and we postprocess derived quantities from those fields.
- A direct distributed pressure-gradient view is possible because OpenFOAM already has the primitive fields:
  - `p`
  - `p_rgh`
  - `wallShearStress`
  - `yPlus`
- The original major-loss package only used `wallShearStress` and `yPlus`, so its major pressure gradient was a Darcy-Weisbach estimate reconstructed from wall shear:
  - `f_D,shear = 8 tau_w / (rho U^2)`
  - `(dp/ds)_est = f_D,shear rho U^2 / (2 D_h)`
- The new report-prep extension reconstructs `p` and `p_rgh` on the same retained times, samples those fields on the same repaired wall faces already used for the shear reduction, and then reduces them into the same centerline bins. That common binning is the key methodological requirement. Without it, the “estimated” and “direct” curves would not be geometrically comparable.

### Exact Direct-Comparison Method

- Step 1: keep the repaired span geometry exactly as-is.
  - `lower_leg` and `right_leg` stay on the anchored `patch_centroid_polyline`.
  - the other spans stay on their existing TP/TW-based or explicit span definitions.
- Step 2: reconstruct `wallShearStress`, `yPlus`, `p`, and `p_rgh` on the same retained times in the temporary extraction case.
- Step 3: for each retained time and each selected wall face:
  - project the face center onto the repaired streamwise coordinate
  - attach the local tangent
  - record wall-face `tau_w`, `yPlus`, `p`, and `p_rgh`
- Step 4: for each span bin:
  - area-average `tau_w`
  - area-average `p`
  - area-average `p_rgh`
  - keep the same geometry-based `D_h` and area surrogate from wall area per unit length
- Step 5: compute two hydraulic reductions on those same bins:
  - shear-based:
    - `f_D,shear = 8 tau_w / (rho U^2)`
    - `(dp/ds)_est = f_D,shear rho U^2 / (2 D_h)`
  - direct wall-pressure-drop-based:
    - first compute a finite-difference gradient of area-averaged `p_rgh` along local bin arclength
    - then convert to pressure-drop sign convention with `-(d<p_rgh>/ds)`
    - then infer whether the local span coordinate is aligned or anti-aligned with the actual flow by checking the retained `p_rgh` drop from the first valid bin to the last valid bin
    - if the span coordinate is anti-aligned, multiply the direct gradient by `-1` so the plotted direct pressure-drop gradient is positive when pressure drops along flow
    - finally compute `f_D,dp = 2 D_h (dp/ds)_direct / (rho U^2)`

### Why `p_rgh` Is The Correct Direct Comparison Field

- `p` is not the right friction-comparison field for this loop because it includes hydrostatic variation. In the rebuilt package, the direct wall-averaged `p` gradients are on the order of:
  - about `-5.18e3 Pa/m` on `lower_leg`
  - about `1.90e4 Pa/m` on `right_leg`
  - about `1.89e4 Pa/m` on `left_lower_leg`
  - about `1.85e4 Pa/m` on `test_section_span`
  - about `1.90e4 Pa/m` on `left_upper_leg`
  - about `5.40e3 Pa/m` on `upper_leg`
- Those magnitudes are dominated by elevation effects, not by the wall-loss scale we are trying to compare against the shear estimate.
- `p_rgh` removes the hydrostatic head contribution, so its streamwise gradient is the appropriate direct wall-pressure field for comparison to a friction-style major-loss estimate.

### Current Direct-Versus-Estimated Hydraulic Results

- In the rebuilt `major_loss_summary.csv`, the span-mean comparison is:
  - `lower_leg`: estimated `(dp/ds)` `13.24 Pa/m` vs direct `p_rgh` `(dp/ds)` `8.19 Pa/m`; shear `f` `0.893` vs direct `f` `0.466`
  - `right_leg`: estimated `(dp/ds)` `16.50 Pa/m` vs direct `17.31 Pa/m`; shear `f` `1.123` vs direct `f` `1.142`
  - `left_lower_leg`: estimated `(dp/ds)` `18.68 Pa/m` vs direct `17.79 Pa/m`; shear `f` `1.275` vs direct `f` `1.328`
  - `test_section_span`: estimated `(dp/ds)` `19.51 Pa/m` vs direct `18.53 Pa/m`; shear `f` `0.945` vs direct `f` `0.788`
  - `left_upper_leg`: estimated `(dp/ds)` `14.04 Pa/m` vs direct `25.28 Pa/m`; shear `f` `0.962` vs direct `f` `1.938`
  - `upper_leg`: estimated `(dp/ds)` `13.60 Pa/m` vs direct `59.27 Pa/m`; shear `f` `0.944` vs direct `f` `4.037`
- The strongest same-direction agreement is now on:
  - `right_leg`
  - `left_lower_leg`
  - `test_section_span`
- `lower_leg` is still qualitatively consistent but quantitatively lower on the direct `p_rgh` side.
- `left_upper_leg` and especially `upper_leg` still diverge materially. Those spans are not yet comparison-clean enough for a strong report claim.

### Interpretation

- The new plots answer the immediate report question directly:
  - yes, we can now plot an “actual” direct wall-pressure-drop gradient against the prior shear-based estimate on the same span coordinate
  - yes, we can now plot `f_D,shear` against `f_D,dp` as a function of traveled distance through the physical loop, with span landmarks
- The most important methodological improvement is not the existence of more plots. It is that the comparison is now made on one repaired coordinate, one frozen time window, and one bin definition.
- The `p_rgh` comparison is already useful even where it is not yet perfectly reassuring:
  - it shows that some spans agree closely enough to support the shear-based reduction
  - it also exposes where the direct wall-pressure signal is still noisier or stronger than the shear estimate, which is exactly the kind of discrepancy worth discussing in a report rather than hiding

### Heat Accounting: Where The Heat Is Going

- The current package heat tail ends at `7401` s and the latest `wallHeatFlux`-based section balance is:
  - heater input: `+244.64 W`
  - cooling branch removal: `-136.35 W`
  - junction losses: `-40.93 W`
  - downcomer losses: `-22.20 W`
  - upcomer losses: `-19.24 W`
  - upper transport losses: `-11.86 W`
  - test-section losses: `-7.44 W`
  - lower transport losses: `-6.38 W`
  - net total: `+0.241 W`
- The near-zero net total is the important closure check. At this late tail, the heater input is almost exactly balanced by the summed removal and loss terms.
- The ambient-style loss proxy is `188.06 W`, which is about `76.9%` of heater input. The cooling branch total removal is `136.35 W`, about `55.7%` of heater input.
- The ambient proxy should not be added on top of the total cooling removal as if it were an independent sink. In the current Salt 2 heat semantics it already includes:
  - passive ambient losses
  - powered-section ambient losses
  - cooling-branch excess above the operating cooling reference
- For report writing, the cleanest “where the heat is going” story is:
  - start from heater input
  - show the signed sectionwise balance from `wallHeatFlux`
  - separately explain the ambient proxy as a diagnostic partition, not as another term in the conservation sum

### Can We Report HTC Versus Distance?

- Not from the current package alone, not yet in a defensible local sense.
- The present package has:
  - direct wall heat-rate accounting by section
  - TP/TW-based temperature histories
  - repaired hydraulic streamwise coordinates
- It does not yet have a matched local streamwise thermal reduction of:
  - wall heat flux `q''(s)`
  - wall temperature `T_wall(s)`
  - bulk fluid temperature `T_bulk(s)`
- To report local HTC, the next extension should sample `T` on the same wall faces and on a matched fluid-side bulk surface for each span bin or each set of cross-sections, then compute:
  - `h(s) = q''(s) / (T_wall(s) - T_bulk(s))`
- The bulk temperature should not come from the sparse TP probes alone if the goal is a report-grade local HTC curve. It should come from a matched cross-sectional or cross-bin fluid average so the numerator and denominator live on the same streamwise resolution.

### What We Can Say About Thermal Resistance

- A thermal-circuit framing is possible, but the defensible level right now is sectionwise effective resistance, not a finely resolved distributed resistance network.
- If this case is treated as a fluid-region CFD model with effective thermal boundary conditions rather than a fully resolved conjugate solid wall, then any resistance we infer from the CFD side is an effective resistance of the applied boundary model. It is not automatically separable into:
  - internal convection
  - metal conduction
  - external convection/radiation
- The next useful resistance quantities would be:
  - sectionwise effective `R = ΔT / Q`
  - sectionwise effective `UA = Q / ΔT`
  - distributed `UA'` or `R'` per unit length once `q''(s)`, `T_wall(s)`, and `T_bulk(s)` are sampled on one common streamwise coordinate

### Best Report Plots To Add Next

- Hydraulic:
  - keep the new loopwise `f_D,shear` vs `f_D,dp` figure
  - keep the new loopwise estimated-vs-direct `p_rgh` pressure-gradient figure
  - optionally add a companion plot of wall-area-averaged `p_rgh(s)` itself so the direct gradient has an immediately visible source curve
- Heat:
  - a signed waterfall or horizontal bar chart from heater input to the section sinks is the clearest “where the heat is going” figure
  - keep the existing wallHeatFlux tail time-series figure as the stability/closure panel
- Future HTC:
  - one aligned four-panel streamwise figure is likely best:
    - `q''(s)`
    - `T_wall(s)` and `T_bulk(s)`
    - `ΔT(s) = T_wall - T_bulk`
    - `h(s)`
- Future thermal circuit:
  - a sectionwise `UA` or effective `R` bar chart is the cleanest first view
  - only after that should we try a more interpretive ladder or Sankey-style thermal-circuit diagram

### Contradictions / Caveats

- The direct hydraulic comparison is wall-registered, not centerline-volume-registered.
- The direct `p_rgh` gradients are finite-difference derivatives of binwise averages, so they are more noise-sensitive than the shear reduction.
- `left_upper_leg` and `upper_leg` still diverge materially between the shear-based and direct-pressure-based views and should be treated as open analysis items, not settled results.
- All major spans remain `warning_heavy`, so the new direct-vs-estimated comparison should be used to sharpen interpretation, not to overstate certainty.

### Suggested Next Actions

- Add a direct `p_rgh(s)` profile plot to the package so the pressure-gradient comparison can be read against its source curve.
- Extend the same streamwise extraction pattern to `T` and wall heat flux so local HTC can be built on the repaired loop coordinate instead of on sparse probes.
- Keep sectionwise heat-loss accounting and future HTC / resistance products explicitly separated in the report:
  - sectionwise heat balance for conservation and narrative
  - local HTC / `UA` / `R` only after a matched streamwise thermal reduction exists

## Streamwise Thermal Extension

### Observed Outputs

- Extended the Salt 2 case package so the same repaired major-span bins now carry:
  - wall-area-averaged wall temperature `T_wall`
  - wall-area-averaged wall heat flux `q''`
  - a TP-endpoint bulk-temperature proxy `T_bulk,proxy`
  - `T_bulk,proxy - T_wall`
  - effective `h`
  - effective `UA'` per unit length
- The new figure outputs are now in the package:
  - `case_loopwise_thermal_profiles`
  - `case_loopwise_effective_ua_per_m`
- The current rebuilt package is at a frozen hydraulic/thermal retained time of `7416 s` only. The explicit request for `7412-7416 s` produced missing snapshot times for `7412-7415`, so this first thermal-extension package is a latest-tail snapshot rather than a five-time late-window average.

### What `Upper Transport` And `Lower Transport` Mean

- These are section-heat bookkeeping labels from the existing `wallHeatFlux` aggregation, not new physics categories.
- In `tools/analyze/build_salt2_behavior_package.py`, the section buckets are assigned by patch naming:
  - `upper_transport`: any wall patch whose name starts with `pipeleg_upper_`
  - `lower_transport`: any wall patch whose name starts with `pipeleg_lower_`
  - `downcomer`: `pipeleg_right_*`
  - `upcomer`: `pipeleg_left_*`
  - `junctions`: `junction_*`
- For Salt 2 specifically:
  - `upper_transport` is the upper horizontal transport branch between the upper-right and upper-left junction regions, including the upper straight, bend, reducer, and cooler-wall patches.
  - `lower_transport` is the lower horizontal transport branch between the lower-left and lower-right junction regions, including the lower straight, fitting, and bend wall patches.
- So when the package says `section_upper_transport_net_q_w` or `section_lower_transport_net_q_w`, it is reporting the net wall heat transfer summed over those patch families.

### Exact Thermal-Extension Method

- The streamwise thermal extension reuses the repaired major-span extraction rather than creating a separate thermal coordinate.
- On the same retained times as the major-loss pass, the extractor now reconstructs:
  - `T`
  - `wallHeatFlux`
  - alongside the existing `wallShearStress`, `yPlus`, `p`, and `p_rgh`
- For each selected wall face, the extractor now records:
  - projected streamwise position on the repaired span coordinate
  - wall temperature from the reconstructed wall-boundary `T` field
  - wall heat flux from the reconstructed `wallHeatFlux` field
- For each major-span bin, it then computes:
  - `T_wall,areaAvg`
  - `q''_wall,areaAvg`
  - `q'_wall = q'' * wetted_perimeter`
- Because a matched cross-sectional bulk-fluid reduction does not yet exist in this package, the current bulk temperature is a proxy:
  - find the TP label at the start of the span
  - find the TP label at the end of the span
  - linearly interpolate between those two TP temperatures by local streamwise fraction within the span
- Then compute:
  - `Delta T_proxy = T_bulk,proxy - T_wall`
  - `h_effective = |q''| / |Delta T_proxy|`
  - `UA'_effective = |q'| / |Delta T_proxy|`

### Important Assumptions

- Assumption 1: the repaired streamwise coordinate used for hydraulic reduction is also a defensible coordinate for local thermal reduction.
- Assumption 2: wall-area-averaged reconstructed `T` on the selected wall patches is a useful local wall-temperature representative for report plots.
- Assumption 3: the linear TP-endpoint interpolation is acceptable as a first bulk-temperature proxy within each span.
  This is the dominant thermal-modeling assumption in this first HTC pass.
- Assumption 4: using magnitudes in `h_effective` and `UA'_effective` is preferable to carrying a sign, because the report goal is local resistance strength rather than signed heating/cooling direction alone.
- Assumption 5: the local wetted-perimeter estimate reused from the hydraulic package is sufficient for the first `UA'` calculation.

### Current Thermal Results

- The new `major_loss_summary.csv` now reports span-mean thermal quantities. At `7416 s`:
  - `lower_leg`: mean `q''` about `+3768.6 W/m^2`, mean `Delta T_proxy` about `-10.86 K`, mean effective `h` about `303.4 W/m^2/K`, mean effective `UA'` about `21.04 W/m/K`
  - `right_leg`: mean `q''` about `-350.0 W/m^2`, mean `Delta T_proxy` about `+0.81 K`, mean effective `h` about `537.1 W/m^2/K`, mean effective `UA'` about `37.02 W/m/K`
  - `left_lower_leg`: mean `q''` about `-373.3 W/m^2`, mean `Delta T_proxy` about `-5.43 K`, mean effective `h` about `75.3 W/m^2/K`, mean effective `UA'` about `5.24 W/m/K`
  - `test_section_span`: mean `q''` about `-572.7 W/m^2`, mean `Delta T_proxy` about `-1.08 K`, mean effective `h` about `772.3 W/m^2/K`, mean effective `UA'` about `48.92 W/m/K`
- The sign patterns already show why this needs careful interpretation:
  - the heater-region lower leg shows positive imposed wall heat flux into the fluid
  - cooling and passive-loss legs mostly show negative wall heat flux out of the fluid
  - some `Delta T_proxy` signs reveal that the TP-endpoint interpolation is only a first proxy, not a true local bulk fluid temperature

### Interpretation Boundary

- This is now a valid report-facing first pass for loopwise thermal patterning.
- It is not yet a definitive internal-convection HTC measurement.
- The current `h_effective` and `UA'_effective` should be described as effective CFD-side streamwise thermal-transfer indicators based on:
  - wall-resolved `T`
  - wall-resolved `wallHeatFlux`
  - TP-based bulk-temperature proxy
- That is good enough for:
  - where the loop is thermally active
  - where losses or cooling are concentrated
  - where apparent local transfer strength is large or small
- It is not yet good enough for a strong claim about true local convective HTC without the caveat that the bulk term is approximate.

### Suggested Next Actions

- Add a matched cross-sectional bulk-fluid temperature reduction so the thermal package can replace the TP-endpoint interpolation with a true local `T_bulk(s)`.
- Once that exists, keep the same plotting structure and simply upgrade:
  - `Delta T_proxy` -> `Delta T_local`
  - `h_effective` -> better-supported local effective HTC
  - `UA'_effective` -> better-supported local effective `UA'`

## Cross-Sectional Bulk-Temperature Upgrade

### Why The Earlier Thermal Method Needed Replacement

- The first HTC-style package used wall-resolved `T` and `wallHeatFlux`, but its fluid-side temperature came from a TP-endpoint interpolation inside each span.
- That made the thermal figures useful for pattern recognition but weak for a report claim about local transfer strength, because `q''(s)` and `T_bulk(s)` were not being reduced from the same geometric support.
- The next correct step was therefore not another plotting pass. It was to sample the fluid field on matched streamwise cross-sections so `T_wall`, `T_bulk`, `q''`, `h`, and `UA'` all live on the same repaired coordinate.

### Implemented Matched-Bulk Method

- The upgraded extractor still uses the repaired major-span bins as the master coordinate.
- For every bin center, it now writes an OpenFOAM `surfaces` function object with a `cutPlane` whose:
  - point is the bin-center coordinate
  - normal is the repaired local tangent
- The current implementation uses:
  - `type surfaces`
  - `surfaceFormat foam`
  - `interpolationScheme cellPoint`
  - `fields (T)`
- The resulting cut-plane surfaces are written under:
  - `tmp_extract/ethan_streamwise_friction/<source_id>/postProcessing/streamwiseBulkTemperature/<time>/<surface>/`
- The Python layer then reads the written `points`, `faces`, and `scalarField/T` files and computes its own area-weighted cross-sectional bulk temperature rather than asking OpenFOAM to emit only a single scalar reduction.
- The per-bin matched bulk term is therefore:
  - `T_bulk,cutPlane(s) = sum(A_face * T_face) / sum(A_face)`
- Once that exists on the same bin, the streamwise package now reports both:
  - matched cut-plane thermal quantities
  - the older TP-endpoint proxy quantities as a diagnostic comparison only

### Exactly How The Thermal Scalars Are Now Built

- For each retained time and each major-loss bin:
  - wall faces are reduced to:
    - `T_wall,areaAvg`
    - `q''_wall,areaAvg`
    - `q'_wall = q'' * wetted_perimeter`
  - the matched cut plane is reduced to:
    - `T_bulk,cutPlane`
    - cut-plane face count
    - cut-plane area
    - cut-plane area divided by the geometry-surrogate flow area
- The package then computes:
  - `Delta T_cutPlane = T_bulk,cutPlane - T_wall`
  - `h_effective,cutPlane = |q''| / |Delta T_cutPlane|`
  - `UA'_effective,cutPlane = |q'| / |Delta T_cutPlane|`
- It also retains the older comparison path:
  - `Delta T_TPproxy = T_bulk,TPproxy - T_wall`
  - `h_effective,TPproxy`
  - `UA'_effective,TPproxy`

### Reconstructed-Field Failure Mode And Local Repair

- The first cut-plane implementation exposed a real defect in the reconstructed retained `T` files used in the temp extraction case.
- OpenFOAM was failing while reading reconstructed `T` because some retained snapshots contained literal `-nan` tokens in the ASCII scalar field.
- Important detail: this failure was not in the primary solved runtime tree. It appeared in the reconstructed temp-case copies used for postprocessing.
- The failure mode mattered because:
  - the wall-face parser used by the package could still produce some thermal outputs
  - but OpenFOAM function objects reading the full `volScalarField T` would abort on the malformed token
- The local repair implemented in the extractor is:
  - inspect each reconstructed retained `T` file in the temp case
  - replace any standalone `-nan`, `nan`, or `+nan` scalar token
  - use the average of the nearest previous and next finite scalar token when both exist
  - fall back to the nearest finite neighbor, then to `0.0` only if no finite neighbor exists
- This sanitization is deliberately scoped to the temp extraction case, not the original runtime source tree.
- The package summary now records the replacement count by retained time so the cleanup is explicit provenance, not a silent mutation.

### Assumptions In The Upgraded Matched-Bulk Method

- Assumption 1: a cut plane normal to the repaired local tangent is a defensible local cross-section for these loop spans.
- Assumption 2: area-weighted `T` on that cut plane is an acceptable first matched bulk-fluid temperature.
  This is better than the TP-endpoint proxy, but it is still not a mass-flux-weighted bulk temperature.
- Assumption 3: `cellPoint` interpolation on the cut plane is acceptable for this first report-facing local thermal reduction.
- Assumption 4: the local `-nan` token repair in the temp reconstructed `T` fields is a safer and more transparent choice than silently dropping affected retained times.
- Assumption 5: the same repaired streamwise bins that are good enough for the hydraulic reduction are also the correct backbone for the thermal reduction.
- Assumption 6: cut-plane area compared against the hydraulic geometry-surrogate flow area is a useful diagnostic for whether the matched bulk sample is geometrically reasonable.

### Report Interpretation Boundary After The Upgrade

- This upgrade materially improves the report path.
- It gives a matched local thermal basis for:
  - `T_wall(s)`
  - `T_bulk(s)`
  - `Delta T(s)`
  - `h_effective(s)`
  - `UA'(s)`
- The remaining major limitation is now specific and explicit:
  - the matched bulk temperature is area-weighted, not yet mass-flux-weighted
- That means the new loopwise thermal plots are appropriate for a strong engineering narrative about where transfer is large or weak, where heating changes to cooling, and how the thermal structure compares with the hydraulic structure.
- They are still not the final word on publication-grade local convective HTC until the bulk reduction is upgraded to a flux-weighted form.

### Best Thermal Plot Structure For The Report

- Keep one common loopwise x-axis with the repaired span landmarks.
- The best primary figure remains a four-panel streamwise stack:
  - `T_wall(s)` and `T_bulk(s)` together
  - `q''(s)`
  - `Delta T(s)`
  - `h_effective(s)`
- Keep `UA'(s)` as a companion figure rather than forcing five panels into one stack.
- Overlay the TP-endpoint-proxy version as a dashed diagnostic curve where useful. That makes the upgrade visible to the reader and shows where the old proxy was biasing interpretation.

### Final Rebuild State For This Upgrade

- The upgraded June 10 Salt 2 case package was rebuilt successfully on the shared retained hydraulic window:
  - `7444, 7445, 7446, 7447, 7448` s
- Matched streamwise thermal coverage is now complete on all five retained times:
  - `cross_section_temperature_available_times = [7444, 7445, 7446, 7447, 7448]`
  - `cross_section_temperature_row_count = 1895`
- The local temp-case `T` sanitization actually used during that rebuild was:
  - `7444: 1` invalid scalar-token replacement
  - `7446: 2`
  - `7447: 6`
  - `7448: 3`
- `7445` required no replacement.
- The package heat tail at the time of the final rebuild reached `7462 s`.
- The rebuilt package README and `summary.json` now explicitly carry:
  - the five matched thermal times
  - the `-nan` token sanitization provenance
  - the remaining area-weighted-bulk limitation

## Mass-Flux-Weighted Thermal Support Repair

### Observed Outputs

- Rebuilt `reports/2026-06-10_ethan_salt2_case_analysis_package/` on a later frozen hydraulic window of `7483, 7484, 7485, 7486, 7487` s.
- The new raw thermal artifacts are:
  - `raw_extraction/bulk_cross_section_temperature_samples.csv`
  - `raw_extraction/thermal_sanitization_summary.json`
  - refreshed `raw_extraction/leg_major_loss_timeseries.csv`
  - refreshed `raw_extraction/leg_major_loss_extraction_summary.json`
- The package summary, the raw extractor summary, and the dedicated sanitization artifact now agree exactly on reconstructed-`T` token replacements:
  - `7484: 4`
  - `7485: 5`
  - `7487: 2`
- The rebuilt `major_loss_summary.csv` now reports mean chosen-region area ratio to reference area close to `1.0` on most spans:
  - `lower_leg = 1.4259`
  - `right_leg = 1.4821`
  - `left_lower_leg = 1.0000`
  - `test_section_span = 1.0081`
  - `left_upper_leg = 1.0000`
  - `upper_leg = 1.0104`
- The package-level thermal-support QC count is now explicit:
  - `thermal_support_flagged_bin_count = 285`
- The old report-blocking local HTC spikes are gone from the primary mass-flux-weighted curve. The largest retained non-masked local HTC values are now about:
  - `1402 W/m^2/K` on `lower_leg`, bin `1`
  - `740 W/m^2/K` on `upper_leg`, bin `3`
  That is materially different from the earlier `~1e4 W/m^2/K` singularities.

### How The Repair Was Done

- The old matched-bulk method reduced every cut plane into one area-weighted bulk temperature. That allowed oversized or multi-region cut-plane supports to contaminate the local `T_bulk` signal.
- The repaired method now samples both `T` and `U` on every repaired streamwise cut plane and performs connected-region analysis before choosing the support region used for bulk temperature.
- For each cut plane and retained time:
  - parse points and faces
  - build connected face regions by shared-edge adjacency
  - compute region area
  - compute region signed mass flux from sampled `U`, face area, and the existing linear density law applied to sampled `T`
  - compute area-weighted `T`
  - compute aligned positive-mass-flux-weighted `T`
- Region selection rule:
  - keep regions with aligned signed mass flux
  - keep only regions with positive aligned mass flux at least `25%` of the largest aligned region positive mass flux
  - among those, choose the region with the smallest log-area error against the span reference area
  - if none survive, fall back to the best area-matching region and flag the support
- The span reference area is the mdot-monitor area already used elsewhere in the hydraulic package, not the geometry-surrogate flow area from wall area per unit length.

### Assumptions

- Assumption 1: all Salt 2 major spans currently use `flow_direction_sign_hint = +1.0`.
  This assumes the authored span order already follows the physical loop flow direction.
- Assumption 2: the linear density law already used in the package is acceptable at the sampled cut-plane temperatures.
- Assumption 3: the chosen connected region should represent one local flow passage rather than the full union of all cut-plane intersections.
- Assumption 4: only aligned positive mass flux should contribute to the primary local bulk-temperature reduction.
- Assumption 5: local HTC and `UA'` should be masked, not clipped or smoothed, when support quality fails.

### Thermal Support Gates

- The package now treats local HTC / `UA'` as report-facing only when all of the following are true:
  - chosen-region area ratio to reference area is in `[0.5, 2.0]`
  - aligned positive mass flux exceeds tolerance
  - region selection succeeded without fallback
  - `|T_bulk - T_wall| >= 0.25 K`
- If any gate fails:
  - raw wall temperature, bulk temperature, wall heat flux, and support diagnostics are retained
  - `effective_htc_w_m2_k` and `effective_ua_per_m_w_m_k` are set to `NaN`
  - a `thermal_support_status` is written explicitly
- In the rebuilt package, `240` retained rows still have chosen-region area ratio greater than `2.0`, but they are now marked `area_ratio_out_of_range` and do not contaminate the primary HTC / `UA'` curves.

### Deterministic Provenance Repair

- The earlier matched-bulk pass had an invocation-order bug: once a temp case had been sanitized, later reruns would report zero replacements even though the first run had repaired invalid retained `T` tokens.
- The new method fixes that by:
  - keying the temp extraction case by `source_id + profile_name + retained-time-window + required_fields`
  - persisting `thermal_sanitization_summary.json`
  - making the package summary read sanitization provenance from that dedicated raw artifact
- This was validated directly by rerunning the package from its own `raw_extraction/` tree. The raw artifact, the raw extractor summary, and `summary.json` all preserved the same sanitization counts after the raw-reuse rebuild.

### Interpretation

- The primary result is not that every local thermal-support problem is solved. The important change is that the known bad-support bins are now gated out instead of being plotted as if they were valid local transport measurements.
- The new loopwise thermal figure is now suitable for a careful report discussion of:
  - wall heat-flux distribution
  - wall-versus-bulk temperature structure
  - where the matched bulk support is good enough to discuss effective local transfer
- The new QC figure is part of the report method story. It shows exactly where local bulk support is weak or oversized and therefore where effective HTC / `UA'` interpretation is intentionally withheld.

### Remaining Caveats

- The repaired method still leaves `285` retained rows flagged by thermal-support diagnostics. The method now handles those rows honestly, but it does not make them physically trustworthy.
- Some selected regions still match the area criterion poorly before masking, especially on parts of `lower_leg` and `right_leg`. The support-selection method is therefore improved and bounded, not universally perfect.
- The local effective HTC / `UA'` curves remain effective CFD-side indicators. They should not yet be written up as clean intrinsic local coefficients without explicitly stating the support-gating method and the remaining flagged-bin count.
- The raw-reuse package path is now thermally reproducible with respect to sanitization provenance, but the broader builder still creates a fresh live snapshot even on raw reuse. That is a separate package-builder robustness issue, not a thermal-method issue.

### Suggested Next Actions

- Reviewer pass focused specifically on the new thermal QC figure and on whether the remaining `285` flagged rows are acceptable for the report boundary now that they are masked in the primary derived curves.
- If stronger local-coefficient claims are needed, tighten the support selection further rather than relaxing the current gates.
- In report text, describe the current primary curves as:
  - mass-flux-weighted
  - connected-region selected
  - support-filtered
  - effective, not intrinsic

## Checkpoint — 2026-06-10 End Of Day

### Current Durable State

- The working report package is `reports/2026-06-10_ethan_salt2_case_analysis_package/`.
- The package now includes a standalone mathematical companion:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/METHODOLOGY_MATH_COMPANION.md`
- The latest integrated rebuild is on frozen hydraulic times `7483, 7484, 7485, 7486, 7487` s.
- The matched streamwise thermal method is no longer the earlier area-weighted cut-plane reduction. The primary thermal path is now:
  - repaired loopwise bins
  - sampled `T` and `U`
  - connected-region parsing on each cut plane
  - one chosen region per bin
  - aligned positive-mass-flux-weighted `T_bulk`
  - support-gated local HTC / `UA'`
- The primary package provenance is internally consistent:
  - `summary.json`
  - `raw_extraction/leg_major_loss_extraction_summary.json`
  - `raw_extraction/thermal_sanitization_summary.json`
  all agree on the same retained window and reconstructed-`T` sanitization counts.

### Most Important Files To Reopen First Tomorrow

- Curated context:
  - `journals/2026-06/2026-06-10_ethan_runs.md`
  - `operational_notes/2026-06-10_todo.md`
- Package-level interpretation:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/README.md`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/METHODOLOGY_MATH_COMPANION.md`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/summary.json`
- Thermal QC and raw support evidence:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/figures/png/case_loopwise_thermal_profiles.png`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/figures/png/case_loopwise_thermal_support_qc.png`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction/bulk_cross_section_temperature_samples.csv`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction/thermal_sanitization_summary.json`
- Core implementation paths:
  - `tools/extract/sample_leg_centerline_major_loss.py`
  - `tools/analyze/build_ethan_case_analysis_package.py`
  - `tools/case_analysis_profiles.py`

### Open Technical Questions

- Are the remaining `285` thermal-support-flagged retained rows acceptable for the report boundary if they remain masked in the primary HTC / `UA'` curves?
- Should the current `flow_direction_sign_hint = +1.0` profile assumption be treated as sufficient for Salt 2, or should it be replaced with a stronger direction-inference rule before freezing report language?
- Are the remaining high-area-ratio zones on parts of `lower_leg` and `right_leg` acceptable as explicitly masked support failures, or do they justify another support-selection refinement pass?
- How strongly should the report interpret the local effective HTC / `UA'` curves versus treating them only as effective CFD-side transfer indicators?

### Tomorrow Restart Guidance

- Do not restart from memory. Restart from the package and QC artifacts above.
- If the goal is review and report writing, start from the figures and `summary.json`, not from the extractor code.
- If the goal is another thermal-method refinement, start from:
  - `sample_leg_centerline_major_loss.py`
  - `bulk_cross_section_temperature_samples.csv`
  - the flagged-bin pattern in `case_loopwise_thermal_support_qc.png`
- If a clean package refresh is needed without new extraction logic, prefer:
  - `python tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar --raw-extraction-dir reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction`
- If the extractor logic changes, rerun the full build:
  - `python tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar`

### Tomorrow TODOs

- Run a reviewer pass focused on the new thermal QC figure and the remaining flagged bins before tightening report claims.
- Decide whether the current report language should stop at “effective, support-filtered thermal indicators” or whether another refinement pass is needed before using stronger local-HTC wording.
- If refinement is needed, prioritize support selection on the remaining flagged `lower_leg` and `right_leg` zones rather than changing the masking thresholds first.
- If report-writing proceeds, build the thermal narrative around:
  - heat-balance closure
  - loopwise wall heat flux
  - wall-versus-bulk temperature structure
  - explicit QC-backed masking of weak local support
