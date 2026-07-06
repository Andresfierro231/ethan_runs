# Ethan Transport Scientific Interpretation Package

Generated: `2026-06-18T13:58:43-05:00`

## Purpose

This package is the focused scientific interpretation handoff for the current
June 15/17/18 transport audit stack. It does not regenerate extraction,
rebuild campaign dashboards, or alter the finished per-case packages. Its job
is to decide what the existing transport outputs actually support, what remains
family-specific, what is contradictory, and what should stay internal-only.

## Input Packages Used

- package index: `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`
- analysis package: `reports/2026-06-18_ethan_transport_analysis_package`
- scrutiny package: `reports/2026-06-17_ethan_transport_scrutiny_package`
- math reference: `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- per-case packages from `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`

## What Was Analyzed

- the two priority-one Water hydraulic contradiction rows:
  - `val_water_test_1_coarse_mesh_laminar / left_lower_leg`
  - `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- branch-by-branch effective thermal outputs:
  - `HTC(x)`
  - `UA'(x)`
  - `R'_th(x)`
- branch support fractions, minimum resolved `|T_bulk - T_wall|`, and sign consistency
- existing scrutiny and analysis package promotion boundaries

## What Was Not Regenerated

- no OpenFOAM extraction
- no per-case package rebuild
- no campaign rebuild
- no new figure dashboard stack

## Contradiction Resolution Summary

- Water 1 / left_lower_leg: resolved_exclude (high) -> Weak wall-registered p_rgh signal plus oscillatory local finite-difference averaging. The branch-mean direct gradient changes sign because local positive and negative direct bins nearly cancel, even though the branch-end cumulative p_rgh drop remains positive at every retained time.
- Water 2 / left_lower_leg: unresolved_exclude (medium) -> Mixed flow-alignment registration inside one retained time, combined with a weak wall-registered p_rgh signal. The direct cumulative p_rgh drop remains positive for every retained time, but one time window carries flow_alignment_sign = -1 over multiple valid bins, which contaminates the branch-mean direct reduction.

## Branch-By-Branch Thermal Summary

- headline-eligible Salt branches: `left_lower_leg, left_upper_leg, test_section_span, upcomer`
- right_leg remains withheld from headline thermal use
- Water left_lower_leg remains blocked for effective thermal dependency use
- Water test_section_span remains supporting-only rather than headline-safe

## Salt-Only Conclusions

- Across all nine Salt cases, left_lower_leg effective thermal metrics remain scrutiny-cleared and can support Salt-only branch dependency work on the left-side return path.
- Across all nine Salt cases, test_section_span is the cleanest thermal anchor: all branch rows remain usable and stay comfortably above the current small-delta-T floor.
- Across all nine Salt cases, left_upper_leg remains Salt-only headline-eligible because usable fractions stay high and the minimum driving temperature stays well above the masking floor.
- The derived upcomer remains a defensible Salt-only branch surface because all three component spans stay scrutiny-cleared in the Salt family and the derived branch inherits high usable fractions.
- Salt right_leg thermal rows remain blocked from headline use even though the mean driving temperature is not small, because usable fraction stays near 0.73 and the failure mode is persistent area-ratio masking.

## Water-Only Conclusions

- Across all four Water cases, left_lower_leg effective thermal metrics are blocked by small |T_bulk - T_wall| and low usable fraction; this branch should not be used for Water-family HTC, UA', or R'_th fitting.
- Water test_section_span is the cleanest Water thermal branch, but it remains supporting-only rather than headline-safe because the minimum resolved driving temperature stays below the current 0.50 K scrutiny threshold.

## Cross-Family Conclusions

- Across both Salt and Water, effective thermal metrics are not uniformly interpretable branch-by-branch; branch promotion gates are required because support quality and resolved driving temperature vary systematically by branch and family.
- Boundary-layer landmarks remain contextual evidence only; they can help explain branch behavior but should not be used as headline model evidence or closure targets.
- Momentum resistance should remain a proxy diagnostic rather than a direct model target because it inherits the same branchwise disagreement and support limits as the underlying direct-versus-shear pressure reductions.

## Family-Specific Conclusions

- The main Salt-vs-Water difference is interpretability, not just magnitude: Salt left-side return-path branches are scrutiny-cleared, whereas Water left-side return-path branches remain support-limited by low |T_bulk - T_wall| and inherited masking.

## Internal-Only Decisions

- salt_all / lower_leg / effective_htc: internal_only (thermal_qc_marginal)
- salt_all / lower_leg / effective_ua: internal_only (thermal_qc_marginal)
- salt_all / lower_leg / thermal_resistance: internal_only (thermal_qc_marginal)
- salt_all / right_leg / effective_htc: internal_only (thermal_low_usable_fraction)
- salt_all / right_leg / effective_ua: internal_only (thermal_low_usable_fraction)
- salt_all / right_leg / thermal_resistance: internal_only (thermal_low_usable_fraction)
- salt_all / left_lower_leg / effective_htc: headline_evidence (safe_salt_subset)
- salt_all / left_lower_leg / effective_ua: headline_evidence (safe_salt_subset)

## Remaining Blockers

- unresolved hydraulic contradiction rows: `1`
- excluded contradiction rows: `2`
- blocked cross-family claims: `5`
- blocked thermal branches remain concentrated in Water left-side branches and both-family right_leg thermal behavior

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_transport_scientific_interpretation_package.py`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir tmp/2026-06-18_ethan_transport_scientific_interpretation_package_smoke`
- `python tools/analyze/build_ethan_transport_scientific_interpretation_package.py --output-dir reports/2026-06-18_ethan_transport_scientific_interpretation_package`

## Limitations

- cross-family hydraulic dependency work remains blocked by the unresolved Water left_lower_leg sign problem
- effective thermal metrics remain effective, support-gated diagnostics rather than intrinsic coefficients
- boundary-layer landmarks remain contextual-only
- momentum resistance remains a proxy rather than a directly measured closure quantity
