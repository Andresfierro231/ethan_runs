# Ethan Streamwise Transport Math Reference

Generated: `2026-06-17`

This package is the current source-of-truth note for the June 15-era
streamwise transport variables. It supersedes the older June 10 Salt 2 math
companion as the place to look first when interpreting:

- shear-based Darcy / Fanning friction behavior
- direct wall-registered `p_rgh` and `p` pressure-gradient behavior
- effective `HTC(x)`, `UA'(x)`, and `R'_th(x)`
- estimated and direct momentum-resistance proxies
- new branch-separated thermal reductions built from the same validated
  major-span bins

The goal here is not to make the package read cleaner. The goal is to state
exactly what the implemented reductions do, which quantities are direct field
reductions versus geometry/model surrogates, and which interpretation limits
still remain.

## Primary implementation references

- `tools/extract/sample_leg_centerline_major_loss.py`
- `tools/analyze/build_ethan_case_analysis_package.py`
- `tools/case_analysis_profiles.py`

## Historical and report context

- `reports/2026-06-10_ethan_salt2_case_analysis_package/METHODOLOGY_MATH_COMPANION.md`
- `reports/2026-06-10_ethan_salt2_case_analysis_package/README.md`
- `journals/2026-06/2026-06-10_ethan_runs.md`
- `reports/2026-06-15_ethan_representative_transport_comparison/README.md`
- `reports/2026-06-15_ethan_field_transport_campaign/README.md`

## What changed relative to June 10

- The hydraulic package already carried the shear-based and direct
  wall-registered pressure reductions on one repaired coordinate.
- The thermal package already carried matched cut-plane bulk support plus
  support-gated effective `HTC` / `UA'`.
- The new June 17 addition is a branch-thermal reduction layer that keeps the
  six repaired major spans as first-class outputs and adds one derived branch:
  `upcomer = left_lower_leg + test_section_span + left_upper_leg`.
- The derived `upcomer` branch concatenates only validated major-span bins and
  intentionally skips corners and junctions.

## Deliverables in this package

- `MATH_COMPANION.md`
  The rigorous formula and interpretation note.

## How to use this package

- Use `MATH_COMPANION.md` when you need exact definitions, units, sign
  conventions, QC gates, and failure modes.
- Use the current per-case package `summary.json`, `major_loss_summary.csv`,
  `major_loss_cumulative_timeseries.csv`, `branch_thermal_profiles.csv`, and
  `branch_thermal_summary.csv` together with this note when checking a specific
  case.
- Treat this package as the authoritative interpretation reference for the
  current code path until a later dated report explicitly replaces it.
