# Ethan Transport Interpretation Closure

Generated: `2026-06-18T14:22:21-05:00`

## Purpose

This package closes the remaining scientific interpretation pass on the June
15/17/18 Ethan transport audit stack. It does not regenerate extraction,
rebuild campaigns, or widen the branch promotion boundary. It performs one
bounded forensic audit on Water 2 `left_lower_leg`, then locks the final
transport interpretation state for downstream model-dependency and paper work.

## Input Packages Used

- package index: `reports/2026-06-15_ethan_all_runs_field_transport_campaign/field_transport_package_index.csv`
- analysis package: `reports/2026-06-18_ethan_transport_analysis_package`
- scrutiny package: `reports/2026-06-17_ethan_transport_scrutiny_package`
- math reference: `reports/2026-06-17_ethan_streamwise_transport_math_reference/MATH_COMPANION.md`
- previous scientific interpretation package: `reports/2026-06-18_ethan_transport_scientific_interpretation_package`

## What Was Analyzed

- one retained-time forensic audit of `val_water_test_2_coarse_mesh_laminar / left_lower_leg`
- revised contradiction status for both Water left_lower_leg rows
- existing branch-by-branch effective thermal interpretation without changing the Salt thermal trust boundary
- revised cross-family claim gates and model-dependency readiness wording

## What Was Not Regenerated

- no OpenFOAM extraction
- no per-case package rebuild
- no campaign rebuild
- no new dashboard stack

## Water 2 Hydraulic Audit Summary

- recommended status: `resolved_exclude`
- confidence: `high`
- interpretation: Resolved exclusion. Water 2 left_lower_leg does not show evidence of a stable branchwise pressure-drop reversal. All retained times keep a positive branch-end cumulative direct p_rgh drop, one retained time carries a unique alignment-sign flip relative to the modal branch orientation, and the remaining sign changes in the branch-mean direct gradient are weak-signal finite-difference cancellations rather than robust reversals.

## Contradiction Resolution Summary

- Water 1 / left_lower_leg: resolved_exclude (high) -> Weak wall-registered p_rgh signal plus oscillatory local finite-difference averaging. The branch-mean direct gradient changes sign because local positive and negative direct bins nearly cancel, even though the branch-end cumulative p_rgh drop remains positive at every retained time.
- Water 2 / left_lower_leg: resolved_exclude (high) -> One retained time carries a unique branch alignment-sign flip relative to the modal left_lower_leg orientation, while the branch-end cumulative direct p_rgh drop stays positive for every retained time. The remaining branch-mean sign changes are weak-signal local cancellations rather than stable pressure-drop reversal.

## Branch-By-Branch Thermal Summary

- headline-eligible Salt branches remain: `left_lower_leg, left_upper_leg, test_section_span, upcomer`
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

## Blocked / Excluded Conclusions

- Water 1 left_lower_leg hydraulic disagreement is best interpreted as a weak-signal wall-registered p_rgh issue: the branch-end cumulative direct p_rgh drop stays positive, but the branch-mean direct gradient oscillates around zero because mixed-sign local derivatives nearly cancel.
- Water 2 left_lower_leg hydraulic disagreement is now best treated as a resolved exclusion: branch-end cumulative direct p_rgh drop remains positive for every retained time, one retained window carries the only branch alignment-sign flip, and the remaining branch-mean direct sign changes are weak-signal cancellation artifacts rather than stable reversal.
- Cross-family hydraulic dependency construction on left_lower_leg remains blocked because both Water rows are exclusions from the evidence subset, even though Water 2 no longer requires an unresolved-sign label.

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

- unresolved hydraulic contradiction rows: `0`
- excluded contradiction rows: `2`
- blocked cross-family claims: `5`
- blocked thermal branches remain concentrated in Water left-side branches and both-family right_leg thermal behavior

## Reproduction Commands

- `python -m py_compile tools/analyze/build_ethan_transport_interpretation_closure.py`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir tmp/2026-06-18_ethan_transport_interpretation_closure_smoke`
- `python tools/analyze/build_ethan_transport_interpretation_closure.py --output-dir reports/2026-06-18_ethan_transport_interpretation_closure`

## Limitations

- cross-family hydraulic dependency work remains blocked because Water left_lower_leg is excluded from the usable branch evidence subset
- effective thermal metrics remain effective, support-gated diagnostics rather than intrinsic coefficients
- boundary-layer landmarks remain contextual-only
- momentum resistance remains a proxy rather than a directly measured closure quantity
