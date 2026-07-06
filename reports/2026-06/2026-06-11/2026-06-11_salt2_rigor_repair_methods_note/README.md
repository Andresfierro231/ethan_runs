# Salt 2 Rigor Repair Methods Note

Generated: `2026-06-11`

This note follows `reports/2026-06-11_salt2_internal_technical_report_brief/`
but changes the goal. The brief says what is currently usable. This note says
what still has to be fixed before stronger report or manuscript claims are
scientifically justified.

The working rule here is simple: do not hide contradictions, do not manually
massage package outputs, and do not promote effective diagnostics into settled
physics.

## Purpose

- Record the highest-value unresolved Salt 2 package issues in one place.
- Rank repair approaches by scientific rigor and reproducibility, not by how
  quickly they make the package look cleaner.
- Preserve an explicit interpretation boundary for later PhD writing.

## Canonical inputs

- Existing June 11 report-facing brief:
  - `reports/2026-06-11_salt2_internal_technical_report_brief/README.md`
  - `reports/2026-06-11_salt2_internal_technical_report_brief/figure_manifest.md`
- Current June 10 Salt 2 package:
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/README.md`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/summary.json`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/analysis_manifest.json`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/major_loss_summary.csv`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/major_loss_cumulative_timeseries.csv`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/feature_minor_loss_summary.csv`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction/leg_major_loss_extraction_summary.json`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction/feature_minor_loss_extraction_summary.json`
  - `reports/2026-06-10_ethan_salt2_case_analysis_package/raw_extraction/thermal_sanitization_summary.json`
- Context and recent interpretation:
  - `journals/2026-06/2026-06-09_ethan_runs.md`
  - `journals/2026-06/2026-06-10_ethan_runs.md`
  - `reports/2026-06-09_ethan_steady_state_heat_flow_audit/README.md`
  - `reports/2026-06-05_ethan_continuation_diagnosis/README.md`

## Observed issues that still block stronger claims

### 1. Direct `p_rgh` summary completeness is still imperfect

- The package README correctly says the hydraulic comparison now puts the
  shear-based and direct wall-`p_rgh` views on one repaired coordinate.
- But `major_loss_summary.csv` still reports
  `mean_terminal_dp_major_direct_prgh_pa = nan` for `left_upper_leg` and
  `upper_leg`.
- The corresponding `major_loss_cumulative_timeseries.csv` rows show valid
  direct `p_rgh` values immediately before terminal rows with
  `missing_wall_faces`.

Interpretation:

- This looks like a summary-construction problem at the span endpoint, not a
  clean physical statement that the direct pressure-drop view is unavailable on
  the whole span.
- Until that is fixed, the current package should not be presented as if every
  span has a fully resolved direct terminal pressure-drop comparison.

### 2. The package is still warning-heavy after the geometry repair

- All six spans remain `warning_heavy` in `major_loss_summary.csv`.
- The raw extractor summary records `warning_row_count = 1791` out of
  `major_loss_row_count = 1895`.
- The current no-quarantine state therefore means only that the
  projection-distance rule no longer rejects a span. It does not mean the full
  hydraulic reduction is review-clean.

Interpretation:

- The centerline-registration repair appears materially useful.
- The stronger claim "the hydraulic story is now clean" is not yet justified.

### 3. Streamwise thermal outputs remain intentionally masked

- `summary.json` records `thermal_support_flagged_bin_count = 285`.
- That is about `15%` of the `1895` streamwise rows in the matched thermal
  reduction.
- The package README already states the current rule: effective HTC and `UA'`
  are only reported when support passes the current quality gates.

Interpretation:

- The thermal package is still best treated as an effective,
  support-filtered indicator of where transfer is strong or weak.
- It is not yet a clean intrinsic local-coefficient result.

### 4. The heat-validation anchor still lags the live Salt 2 state

- The current June 10 package heat tail reaches `7506 s`.
- The reused direct-validation reference still ends at `3871 s`.
- The carried validation row in `summary.json` still says
  `run_status = "running"` and `convergence_reached = "False"`.

Interpretation:

- The wall-heat accounting itself is still useful.
- But the package should not describe the current thermal validation numbers as
  if they are synchronized to the present late-tail Salt 2 state.

### 5. Feature-budget residual caveats remain unresolved

- `feature_minor_loss_summary.csv` still carries negative residuals for
  `corner_lower_left`, `corner_lower_right`, and `corner_upper_left`.
- The raw feature extractor summary also states that direct `profile_dp_pa`
  sampling is deferred and that the early extractor semantics were incomplete
  until the integrator layer supplied the reference terms.

Interpretation:

- The feature package is still acceptable as a caveat surface and a direction
  finder.
- It is not yet a settled minor-loss truth table.

## Interpretation boundary for current PhD writing

- Safe to say:
  - the repaired loopwise coordinate materially improved cross-span comparison
  - the late-tail heat partition is internally tight enough to support a first
    "where is the heat going?" statement
  - the thermal streamwise package is useful only in effective,
    support-gated language
- Not safe to say:
  - the direct-vs-shear hydraulic comparison is complete and settled on every
    span
  - the current local HTC or `UA'` curves are intrinsic transport coefficients
  - the current validation anchor is fully current to the live Salt 2 tail
  - the negative feature residuals are established physical negative losses

## Repair approaches

### Approach A: Provenance-first package hardening

Recommended order: first.

This approach fixes package semantics before any new physics claim is tightened.

Steps:

1. Make the direct-pressure summary use the last valid direct `p_rgh` bin, not
   a terminal placeholder row with `missing_wall_faces`.
2. Export explicit per-span validity metadata for the direct comparison:
   terminal-valid flag, last-valid-bin index, and count of dropped tail rows.
3. Fail or loudly warn when a report-facing summary claims a spanwise direct
   comparison but the span terminates on invalid wall-face rows.
4. Keep the current warning counts visible in the package summary instead of
   allowing the no-quarantine state to read as a general clean bill of health.
5. Refresh the June 11 brief only after the hardened package is rebuilt from
   script, not by hand-editing tables.

Why this is rigorous:

- It improves reproducibility without changing the scientific story by fiat.
- It prevents a packaging bug from being mistaken for a physical signal.
- It preserves the current contradictions instead of smoothing them away.

What it will not solve by itself:

- It will not explain why `upper_leg` and `left_upper_leg` still diverge
  materially between the shear and direct views.

### Approach B: Span-focused hydraulic diagnosis before stronger reporting

Recommended order: second, after Approach A.

This approach assumes the remaining upper-span disagreement may be partly
physical, partly reduction-related, and should be diagnosed directly instead of
written around.

Steps:

1. Isolate `left_upper_leg` and `upper_leg` from
   `major_loss_cumulative_timeseries.csv` and inspect where direct gradients
   become invalid or unstable near the span ends.
2. Check whether the remaining endpoint bins have a wall-face coverage problem,
   a patch-order problem, or a legitimate wall-averaged `p_rgh` discontinuity.
3. Recompute comparison summaries with robust statistics alongside the current
   means:
   medians, interquartile ranges, and last-valid-bin terminal drops.
4. If needed, add one alternate direct observable for those spans only:
   cross-section-averaged `p_rgh` or a matched probe-based check, but keep it
   explicitly parallel to the wall-registered method rather than replacing it
   silently.
5. Treat any improvement as conditional until it survives the same retained
   window and the same repaired coordinate.

Why this is rigorous:

- It targets the real scientific disagreement instead of just improving
  packaging.
- It is narrow enough to preserve the rest of the package as a stable baseline.
- It distinguishes "the reduction is incomplete" from "the span physics are
  genuinely different."

What it will cost:

- More analysis time.
- A real possibility that the honest result is weaker report language, not
  stronger report language.

### Approach C: Thermal and validation closure only after the hydraulic path is stable

Recommended order: third.

This approach treats the thermal story as important but downstream of the
hydraulic trust problem.

Steps:

1. Refresh the direct-validation anchor so the Salt 2 `TW` metrics reflect the
   same runtime era as the current heat tail.
2. Keep the current support-masked streamwise thermal reductions, but add
   explicit spanwise flagged fractions to the report-facing summary.
3. If local HTC language remains necessary, promote only span-aggregated or
   support-qualified values first, not a fully pointwise intrinsic story.
4. Preserve the thermal sanitization provenance exactly as it is now; do not
   hide the `-nan` replacement history.

Why this is rigorous:

- It avoids mixing a current heat-balance narrative with stale validation
  provenance.
- It keeps the thermal evidence usable without overselling what the cut-plane
  method currently proves.

Why it is not the first step:

- The hydraulic comparison is presently the more immediate report-path risk,
  because it mixes real scientific disagreement with a likely summary-endpoint
  defect.

## Recommended staged plan

1. Do Approach A first and rebuild the package from script.
2. Immediately rerun a reviewer pass on the rebuilt package before updating any
   report-facing prose.
3. If the upper-span disagreement remains after the packaging hardening, do
   Approach B next and let the outcome determine whether the report claim
   weakens or strengthens.
4. Do Approach C only after the hydraulic interpretation boundary is stable
   enough that the thermal discussion is not being built on moving ground.

## Explicit do-not-do list

- Do not hand-edit summary numbers to remove `nan` endpoint artifacts.
- Do not suppress `warning_heavy` spans just because the projection-distance
  quarantine is gone.
- Do not relabel effective support-gated HTC as intrinsic local HTC.
- Do not call the current validation anchor "current" while it still ends at
  `3871 s` against a `7506 s` heat tail.
- Do not reinterpret negative feature residuals as resolved physics before the
  deferred reference-pressure terms are independently checked.

## Recommendation

For important PhD work, the most defensible path is:

- package hardening first
- reviewer confirmation second
- targeted upper-span diagnosis third
- refreshed validation and thermal tightening last

That ordering is slower than simply polishing the existing brief, but it is the
better scientific choice because it keeps provenance, contradictions, and
interpretation limits visible at each step.
